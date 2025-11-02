from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
import re

from apps.agent.data import ROTEIRO_METRICAS_SISP, ROTEIRO_SISP_AI

# ======================================================================================
# CONFIG
# ======================================================================================
# Tamanho do hunk (trecho de diff) incluído em cada evidência.
# Use None para NÃO truncar (atenção ao limite de tokens do modelo).
MAX_HUNK_CHARS: int | None = None

# Classificar com LLM no máximo N evidências (None = todas).
MAX_CLASSIFY_UNITS: Optional[int] = None

# Paginação de evidências — mantido como flag, mas DESLIGADO.
PAGINATE = False
PAGE_SIZE_UNITS = 60
MAX_PAGES: Optional[int] = None

# Sempre passar pelo nó de classificação LLM (mesmo se heurística não marcou ambíguo).
FORCE_CLASSIFY = True

# ======================================================================================
# Tipos / Estado
# ======================================================================================
class GraphState(TypedDict):
    repo: str
    pr_number: int
    pr_head_sha: str
    files_count: int
    units: list            # List[FunctionalUnit]
    result: object | None  # CountResult
    rag_refs: list[dict]
    explanation: Optional[str]
    ambiguous: bool

@dataclass
class Env:
    pr_reader: object           # Port: PRReaderPort
    parser: object              # Port: DiffParserPort
    calculator: object          # Port: CalculatorPort (APFCalculator)
    notifier: object            # Port: NotifierPort (GitHub comment)
    baseline_repo: object       # Port: BaselineRepo
    report_repo: object         # Port: ReportRepo
    status_pub: object | None   # Port: StatusPublisher (opcional)
    vector_repo: object | None  # Port: VectorRepo (Qdrant) (opcional)
    llm: object | None          # Port: LLMPort (OpenAI/Ollama) (opcional)

# ======================================================================================
# Helpers
# ======================================================================================
def get_system_message() -> str:
    """Mensagem de sistema com os roteiros SISP."""
    return (f"Roteiro geral SISP:\n{ROTEIRO_METRICAS_SISP}\n\n"
            f"Roteiro SISP-IA:\n{ROTEIRO_SISP_AI}")

def chunk_list(xs: list, size: int) -> list[list]:
    if size <= 0:
        return [xs]
    return [xs[i:i+size] for i in range(0, len(xs), size)]


# ======================================================================================
# Nó 1: Buscar PR + heurísticas
# ======================================================================================
def fetch_pr(state: GraphState, env: Env) -> GraphState:
    repo = state["repo"]
    pr_number = state["pr_number"]

    pr = env.pr_reader.read(repo, pr_number)  # deve preencher: head_sha, files (com .patch)
    files = getattr(pr, "files", []) or []
    head_sha = getattr(pr, "head_sha", "")

    # Heurísticas → units
    units = env.parser.detect_functional_units(pr)

    ambiguous = not bool(units)

    # Status pending no commit
    if env.status_pub and head_sha:
        try:
            import anyio
            async def _pending():
                env.status_pub.set_status(repo, head_sha, "pending", "PRPoints/APF", "Analisando diffs…")
            anyio.run(_pending())
        except Exception:
            pass

    new_state = state.copy()
    new_state.update({
        "pr_head_sha": head_sha,
        "files_count": len(files),
        "units": units,
        "ambiguous": ambiguous,
    })
    return new_state

# ======================================================================================
# Nó 2: Classificar com LLM (múltiplas evidências)
# ======================================================================================
ALLOWED = {"EE", "SE", "CE", "ALI", "AIE", "NONE"}
LABEL_RE = re.compile(r"\b(EE|SE|CE|ALI|AIE|NONE)\b", re.I)

LLM_SYS = """Você é um analista de métricas SISP (APF).
Classifique o trecho de diff em UMA, e somente UMA, das classes:

- EE   → Entrada Externa (transação com escrita: POST/PUT/PATCH/DELETE, inserts/updates).
- SE   → Saída Externa (GET com transformação/cálculo/agregação).
- CE   → Consulta Externa (GET simples/retorno direto, sem transformação relevante).
- ALI  → Arquivo Lógico Interno (manutenção de dados internos: DDL/migração/modelos).
- NONE → Não conta (refator, logs, testes, configs, etc.).

Regras:
- Responda exatamente com UMA etiqueta (somente a palavra).
- Se estiver em dúvida, escolha NONE.
- Segurança/middlewares sozinhos → NONE.
- DDL/Schema claro → ALI.
- GET com transformação → SE; GET simples → CE; escrita → EE.
"""

FEW_SHOT = """
Exemplos:
[ex1]
+ app.get("/users", ...)
+ return res.json(users)
→ CE

[ex2]
+ GET /reports/sales  # agrega e calcula
→ SE

[ex3]
+ POST /users
→ EE

[ex4]
+ ALTER TABLE orders ADD COLUMN status varchar(20);
→ ALI

[ex5]
+ logger.info("refactor")
→ NONE
"""
def _mk_classify_prompt(diff_snippet: str, refs: list[dict]) -> str:
    raw = diff_snippet or ""
    snippet = raw if MAX_HUNK_CHARS is None else raw[:MAX_HUNK_CHARS]
    refs_txt = "\n\n".join(f"[{i+1}] {r['text'][:500]}" for i, r in enumerate(refs or []))
    return f"""{LLM_SYS}

Trecho do diff (parcial):
{snippet}

Referências SISP/Roteiro (RAG):
{refs_txt}

{FEW_SHOT}

Classificação:"""

def _parse_label(text: str) -> str:
    if not text:
        return "NONE"
    m = LABEL_RE.search(text.strip())
    return m.group(1).upper() if m else "NONE"

def classify_with_llm(state: GraphState, env: Env) -> GraphState:
    if not env.llm or not env.vector_repo:
        return state

    # RAG: pequenas referências
    refs = []
    try:
        seeds = ["Processo Elementar", "Transformar Dados", "Invocar Modelo", "Disponibilizar Dados", "Entidade Lógica"]
        acc = []
        for q in seeds:
            acc.extend(env.vector_repo.search(q, k=1))
        # dedup
        seen, uniq = set(), []
        for r in acc:
            key = (r["text"][:160]).strip()
            if key in seen:
                continue
            seen.add(key)
            uniq.append(r)
        refs = uniq[:4]
    except Exception:
        refs = []

    units = list(state.get("units", []))
    total = len(units)
    limit = MAX_CLASSIFY_UNITS if MAX_CLASSIFY_UNITS is not None else total
    count = 0

    for u in units:
        if count >= limit:
            break
        snippet = getattr(u.evidence, "hunk", "") or ""
        if not snippet:
            continue
        prompt = _mk_classify_prompt(snippet, refs)
        system = get_system_message()
        try:
            raw = env.llm.complete(prompt=prompt, system_message=system, temperature=0.0)
            label = _parse_label(raw)
            # Anotar no rationale (sem perder o que já havia)
            base = getattr(u.evidence, "rationale", "")
            mark = f"LLM={label}"
            u.evidence.rationale = (base + (" | " if base else "") + mark).strip()
            count += 1
        except Exception:
            continue

    new_state = state.copy()
    new_state["units"] = units
    new_state["rag_refs"] = refs
    return new_state

# ======================================================================================
# Nó 3: Calcular + Persistir + Explicar (SEM paginação, todas evidências)
# ======================================================================================
def _file_distribution(units) -> dict:
    by_file = {}
    for u in units:
        f = getattr(u.evidence, "file", "unknown")
        if f not in by_file:
            by_file[f] = {"EE": 0, "SE": 0, "CE": 0, "ALI": 0, "AIE": 0,
                          "INCL": 0, "ALT": 0, "EXC": 0}
        # tipos APF
        t = u.type.upper()
        if t in by_file[f]:
            by_file[f][t] += 1
        # categorias
        by_file[f][u.category] = by_file[f].get(u.category, 0) + 1
    return by_file

def _units_to_struct_list(units) -> list[dict]:
    out = []
    for i, u in enumerate(units, start=1):
        raw_hunk = getattr(u.evidence, "hunk", "") or ""
        hunk = raw_hunk if MAX_HUNK_CHARS is None else raw_hunk[:MAX_HUNK_CHARS]
        out.append({
            "index": i,
            "type": u.type,                 # EE/SE/CE/ALI/AIE
            "category": u.category,         # INCL/ALT/EXC
            "det": getattr(u, "det", 0),
            "ftr": getattr(u, "ftr", 0),
            "ret": getattr(u, "ret", 0),
            "file": getattr(u.evidence, "file", "unknown"),
            "line_from": getattr(u.evidence, "line_from", 0),
            "line_to": getattr(u.evidence, "line_to", 0),
            "rationale": getattr(u.evidence, "rationale", ""),
            "hunk": hunk,
        })
    return out


def _mk_explanation_prompt_single(result, params, all_units_struct, by_file_snippet: str) -> str:
    return f"""Gere a explicação **completa** da contagem SISP (APF) em **Markdown**, usando todas as evidências.
Cite **arquivo e linhas** e inclua **trechos reais** do diff (blocos de código). Justifique INCL/ALT/EXC.

## 1. Escopo Funcional da Alteração
1–2 frases resumindo os tipos de mudanças (endpoints, transformações, DDL etc.).

## 2. Identificação das Funções (APF)
### Transacionais (EE/SE/CE)
Para **cada** EE/SE/CE:
- **Arquivo** e **linhas**
- **Tipo**: EE (escrita), SE (GET com transformação), CE (GET simples)
- **Categoria**: INCL/ALT/EXC e **por quê**
- **DET** e **FTR** usados na complexidade
- **Trecho** curto do diff (````diff```)

### Arquivos de Dados (ALI/AIE)
Para **cada** ALI/AIE:
- **Arquivo** e **linhas**
- **Categoria**: INCL/ALT/EXC e **por quê**
- **DET** e **RET** usados na complexidade
- **Trecho** curto do diff

## 3. Resultado da Contagem (Consolidado)
- Total **APF**: {getattr(result, 'total_apf', 0.0):.2f}
- Fórmula: {result.formula_text}

EVIDÊNCIAS (JSON):
{all_units_struct}

Resumo por arquivo:
{by_file_snippet}
"""

def compute_and_persist(state: GraphState, env: Env) -> GraphState:
    result = env.calculator.compute_apf(state["repo"], state["pr_number"], state["units"])
    env.report_repo.persist(result)

    current = env.baseline_repo.get(state["repo"], "APF")
    next_b = env.baseline_repo.apply_from_result(current, result)
    env.baseline_repo.upsert(next_b)

    all_units_struct = _units_to_struct_list(result.units)
    by_file = _file_distribution(result.units)
    by_file_lines = []
    for f, d in sorted(by_file.items(), key=lambda kv: (-(kv[1]["EE"]+kv[1]["SE"]+kv[1]["CE"]+kv[1]["ALI"]+kv[1]["AIE"]), kv[0])):
        by_file_lines.append(
            f"- `{f}` → EE={d['EE']}, SE={d['SE']}, CE={d['CE']}, ALI={d['ALI']}, AIE={d['AIE']} | INCL={d['INCL']}, ALT={d['ALT']}, EXC={d['EXC']}"
        )
    by_file_snippet = "\n".join(by_file_lines) if by_file_lines else "- (sem distribuição por arquivo)"

    if env.llm:
        system = (
            "Você é um especialista em SISP/APF. "
            "Produza explicações **em Markdown**, citando arquivos e linhas, com trechos de diff.\n\n"
            + get_system_message()
        )
        try:
            prompt = _mk_explanation_prompt_single(
                result=result, params={},  # params não são usados no APF
                all_units_struct=all_units_struct,
                by_file_snippet=by_file_snippet,
            )
            explanation = env.llm.complete(prompt=prompt, system_message=system, temperature=0.2).strip()
        except Exception:
            # Fallback simples
            lines = [
                "## 1. Escopo Funcional da Alteração",
                "Alterações envolvendo transações (EE/SE/CE) e arquivos de dados (ALI/AIE).",
                "\n## 2. Identificação — Listagem Completa",
            ]
            for u in all_units_struct:
                lines.append(
                    f"- `{u['file']}` {u['type']}/{u['category']} (linhas {u['line_from']}-{u['line_to']}) — {u['rationale'][:200]}"
                )
            lines.append(f"\n## 3. Resultado da Contagem (APF)\n- Total: {getattr(result, 'total_apf', 0.0):.2f}\n- Fórmula: {result.formula_text}")
            explanation = "\n".join(lines)
    else:
        # Sem IA → Fallback determinístico
        lines = [
            "## 1. Escopo Funcional da Alteração",
            "Alterações envolvendo transações (EE/SE/CE) e arquivos de dados (ALI/AIE).",
            "\n## 2. Identificação — Listagem Completa",
        ]
        for u in all_units_struct:
            lines.append(
                f"- `{u['file']}` {u['type']}/{u['category']} (linhas {u['line_from']}-{u['line_to']}) — {u['rationale'][:200]}"
            )
        lines.append(f"\n## 3. Resultado da Contagem (APF)\n- Total: {getattr(result, 'total_apf', 0.0):.2f}\n- Fórmula: {result.formula_text}")
        explanation = "\n".join(lines)

    import anyio
    async def _pub():
        try:
            await env.notifier.post_result_comment(result, explanation)
        except TypeError:
            await env.notifier.post_result_comment(result)
        except Exception:
            pass

        if env.status_pub and state.get("pr_head_sha"):
            try:
                await env.status_pub.set_status(
                    state["repo"], state["pr_head_sha"], "success", "PRPoints/APF",
                    f"{getattr(result, 'total_apf', 0.0):.2f} APF"
                )
            except Exception:
                pass

    anyio.run(_pub)

    new_state = state.copy()
    new_state["result"] = result
    new_state["explanation"] = explanation
    return new_state

# ======================================================================================
# Construção do grafo
# ======================================================================================
def build_graph(env: Env):
    """Constrói e retorna o grafo compilado do LangGraph."""
    g = StateGraph(GraphState)
    g.add_node("FetchPR", lambda s: fetch_pr(s, env))
    g.add_node("ClassifyLLM", lambda s: classify_with_llm(s, env))
    g.add_node("ComputePersist", lambda s: compute_and_persist(s, env))

    g.set_entry_point("FetchPR")

    def route_after_fetch(state: GraphState):
        if FORCE_CLASSIFY:
            return "ClassifyLLM"
        return "ClassifyLLM" if state.get("ambiguous") else "ComputePersist"

    g.add_conditional_edges(
        "FetchPR",
        route_after_fetch,
        {"ClassifyLLM": "ClassifyLLM", "ComputePersist": "ComputePersist"},
    )
    g.add_edge("ClassifyLLM", "ComputePersist")
    g.add_edge("ComputePersist", END)
    return g.compile()
