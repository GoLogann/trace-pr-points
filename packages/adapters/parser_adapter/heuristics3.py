# apps/agent/graph_parser_apf_v3.py
# Parser heurístico com saída em APF (EE/SE/CE/ALI/AIE) + estimativa de DET/FTR/RET

from __future__ import annotations
import re
from typing import List
from packages.core.entities.pull_request import PullRequest
from packages.core.entities.functional_unit import FunctionalUnit, Evidence

# -------------------------------
# Helpers utilitários (mantidos)
# -------------------------------
def RX(p: str, flags=0): 
    return re.compile(p, flags)

def _cat(status: str) -> str:
    return "INCL" if status == "added" else "EXC" if status == "removed" else "ALT"

def _lines_added(patch: str) -> tuple[int, int]:
    if not patch:
        return (0, 0)
    new_line = start = end = None
    for line in patch.splitlines():
        m = re.match(r"@@ -\d+(?:,\d+)? \+(\d+)", line)
        if m:
            new_line = int(m.group(1))
            continue
        if new_line is None:
            continue
        if line.startswith("+") and not line.startswith("+++"):
            if start is None:
                start = new_line
            end = new_line
            new_line += 1
        elif line.startswith(" "):
            new_line += 1
    return (start or 0, end or 0)

def _extract_hunk_snippet(patch: str, max_lines: int = 24, max_chars_per_line: int = 220) -> str:
    """Coleta até max_lines de linhas adicionadas do(s) primeiro(s) hunk(s)."""
    if not patch:
        return ""
    lines = []
    taking = False
    for line in patch.splitlines():
        if line.startswith("@@"):
            taking = True
            continue
        if not taking:
            continue
        if line.startswith("+") and not line.startswith("+++"):
            lines.append(line[:max_chars_per_line])
            if len(lines) >= max_lines:
                break
        elif line.startswith(" ") or line.startswith("-"):
            continue
    return "\n".join(lines)

# -------------------------------
# Padrões universais (com Go/Gin/FastAPI)
# -------------------------------

PAT_ENDPOINTS = [
    # Java/Spring
    r"@(?:Get|Post|Put|Patch|Delete)Mapping\(",
    # .NET
    r"\[(?:HttpGet|HttpPost|HttpPut|HttpPatch|HttpDelete)\]",
    r"\.Map(?:Get|Post|Put|Patch|Delete)\(",
    # PHP Laravel
    r"\bRoute::(get|post|put|patch|delete)\(",
    # Node/JS/TS
    r"\b(app|router|route|server)\.(get|post|put|patch|delete)\(",
    # GraphQL
    r"\b@gql\(|\btype\s+Query\b|\btype\s+Mutation\b",
    r"\bmutation\s*{|\bquery\s*{",
    r"\bGraphQLObjectType\b|\bResolvers?\b",
    # Ktor
    r"\bpath\(\"/[^\"]*\",\s*(GET|POST|PUT|PATCH|DELETE)\b",
    # FastAPI
    r"@app\.(get|post|put|patch|delete|options|head)\(",
    r"@router\.(get|post|put|patch|delete|options|head)\(",
    r"\bAPIRouter\(\)",
    r"\bFastAPI\(\)",
    r"\bapp\.include_router\(",
    r"\bPath\(|Query\(|Body\(|Header\(|Cookie\(",
    r"\bDepends\(",
    r"\bBackgroundTasks\b",
    r"\bWebSocket\b|\bwebsocket\b",
    r"\bHTTPException\(",
    # Go/Gin e outros
    r"\b(router|r|engine|group|v1)\.(GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD)\(",
    r"\bgin\.(?:Default|New)\(\)\.(?:GET|POST|PUT|PATCH|DELETE)",
    r"\b(?:router|r)\.Group\([\"']/[^\"']*[\"']\)",
    r"\bfunc\s+\w+Handler\(",
    r"\bfunc\s+\w+\(c\s*\*gin\.Context\)",
    r"\bc\.(?:JSON|XML|String|HTML|Data|Redirect|Header)\(",
    r"\bgin\.HandlerFunc\b",
    r"\bc\.(?:Param|Query|PostForm|FormValue|ShouldBind)\(",
    r"\bmux\.NewRouter\(\)",
    r"\b(?:router|r)\.HandleFunc\(",
    r"\bchi\.NewRouter\(\)",
    r"\becho\.New\(\)",
    r"\be\.(?:GET|POST|PUT|PATCH|DELETE)\(",
    r"\bfiber\.New\(\)",
    r"\bapp\.(?:Get|Post|Put|Patch|Delete)\(",
    # Go std HTTP
    r"\.HandleFunc\(\s*\"/[^\"]*\",\s*[A-Za-z_]\w*\)",
    r"\bhttp\.HandleFunc\(",
    r"\bhttp\.ListenAndServe\(",
    r"\bservemux\b|\bServeMux\b",
]

PAT_DISPLAY = [
    # .NET / Java / Node / Python geral
    r"\breturn\s+Json(?:Result)?\b",
    r"\bResponseEntity\.<",
    r"\bres\.(json|send|render)\(",
    r"\breturn\s+View\(",
    r"\bSELECT\b|\bto_json\b",
    # FastAPI
    r"\breturn\s+\{.*\}",
    r"\bJSONResponse\(",
    r"\bHTMLResponse\(",
    r"\bPlainTextResponse\(",
    r"\bRedirectResponse\(",
    r"\bFileResponse\(",
    r"\bStreamingResponse\(",
    r"\bResponse\(.*content=",
    r"\bstatus_code=\d+",
    r"\braise\s+HTTPException\(",
    r"\bjinja2\b.*\btemplates\b",
    r"\brender_template\(",
    # Python web
    r"\bjsonify\(",
    r"\brender_(template|json)\(",
    r"\breturn\s+JsonResponse\(",
    r"\breturn\s+HttpResponse\(",
    # Go/Gin
    r"\bc\.JSON\(",
    r"\bc\.(?:XML|YAML|String|HTML|Data|File|Stream)\(",
    r"\bc\.(?:Status|AbortWithStatus|AbortWithStatusJSON)\(",
    r"\bc\.Redirect\(",
    r"\bc\.Header\(",
    r"\bc\.SetCookie\(",
    r"\bc\.Render\(",
    r"\bjson\.Marshal\(",
    r"\bjson\.Unmarshal\(",
    r"\btemplate\.Execute\(",
    r"\bw\.Write\(",
    r"\bfmt\.Fprintf\(w,",
    r"\bhttp\.Error\(",
]

PAT_JOBS = [
    r"\b(cron|CRON)\b",
    r"\bAPScheduler\b|\bCelery\b|\bRQ\b|\bHuey\b",
    r"\bSidekiq\b|\bResque\b|\bActiveJob\b",
    r"\bBullMQ\b|\bAgenda\b",
    r"\bHangfire\b|\bQuartz\b",
    r"\bsetInterval\(",
    r"\bAirflow\b|\bDag\(",
    # Python
    r"\bBackgroundTasks\b",
    r"\badd_task\(",
    r"\bschedule\.(every|job)\b",
    r"\b@periodic_task\b|\b@task\b",
    r"\basyncio\.(create_task|gather|run)\(",
    r"\bawait\s+\w+\.delay\(",
    r"\bfrom\s+celery\b",
    r"\bfrom\s+rq\b",
    # Go
    r"\bgocron\b|\bcron\.New\(",
    r"\brobfig/cron\b",
    r"\btime\.Ticker\b|\btime\.After\(",
    r"\bgo\s+func\(\)",
    r"\bworker\.New\(",
    r"\bqueue\.Add\(",
    r"\bchannel.*<-",
]

PAT_TRANSFORM = [
    r"\b(transform|normalize|preprocess|tokeni[sz]e|cleanse|standardize)\b",
    r"\bfit_transform\(|fitTransform\(",
    r"\bmerge\(|join\(",
    r"\bgroupby\(",
    # Python
    r"\bpydantic\b.*\bBaseModel\b",
    r"\bField\(|validator\(|root_validator\(",
    r"\b\.dict\(\)|\.json\(\)|\.parse_obj\(",
    r"\bfrom\s+pydantic\b",
    r"\bpandas\.(read_csv|read_json|read_excel|DataFrame)",
    r"\bdf\.(apply|map|transform|groupby|merge|join)\(",
    r"\bnumpy\.(array|reshape|transpose)\(",
    r"\bmap\(|reduce\(|filter\(",
    r"\blist\(.*comprehension\)|dict\(.*comprehension\)",
    r"\b(json\.loads|json\.dumps)\(",
    r"\b(yaml\.load|yaml\.dump)\(",
    # Go
    r"\bstrings\.(?:Replace|Split|Join|Trim|ToLower|ToUpper)\(",
    r"\bregexp\.(?:MustCompile|MatchString|ReplaceAll)\(",
    r"\bsort\.(?:Strings|Ints|Sort|Slice)\(",
    r"\bstrconv\.(?:Atoi|Itoa|ParseInt|ParseFloat|FormatInt)\(",
    r"\bencoding/(?:json|xml|csv|base64)\b",
    r"\bfor\s+\w+\s*:=\s*range\b",
]

PAT_MODEL = [
    r"\bopenai\b.*\b(chat|completions?|responses?)\b",
    r"\banthropic\b|\bclaude\b",
    r"\bvertexai\b|\bbedrock\b|\bcohere\b",
    r"\btransformers\b.*\b(pipeline|generate|infer|forward)\b",
    r"\bmodel\.(predict|generate|infer|invoke)\(",
    r"\bsklearn\..*\.predict\(",
    r"\bollama\b.*\bgenerate\b|\b/api/generate\b",
    r"\blangchain\b.*\b(invoke|predict|stream)\b",
    # Go
    r"\bopenai-go\b|\bgo-openai\b",
    r"\bClient\.CreateChatCompletion\(",
    r"\bhttp\.Post\(.*\b(openai|anthropic|cohere|huggingface)\b",
    r"\btensorflow/serving\b",
    r"\bgrpc.*\bPredict\(",
    r"\bmachine.*learning\b|\bml.*model\b",
]

PAT_DDL = [
    # SQL direto
    r"\b(CREATE|ALTER)\s+TABLE\b",
    r"\bPRIMARY\s+KEY\b|\bFOREIGN\s+KEY\b|\bUNIQUE\b",
    # JS/TS
    r"\bknex\.schema\.(createTable|alterTable)\(",
    r"\bsequelize\.define\(|\bqueryInterface\.(createTable|addColumn|changeColumn)\(",
    # TypeORM / Prisma
    r"\bTypeORM\b.*Migration|\bqueryRunner\.(createTable|addColumn|query)\(",
    r"\bprisma\b.*\bschema\b|\bdatasource\b|\bmodel\s+\w+\s*{",
    # Python ORM
    r"\bSQLAlchemy\b.*\b(create_all|drop_all)\(",
    r"\bBase\.metadata\.(create_all|drop_all)\(",
    r"\bColumn\(|Integer\(|String\(|DateTime\(|Boolean\(",
    r"\b__tablename__\s*=",
    r"\brelationship\(|backref\(",
    r"\balembic\b.*\b(upgrade|downgrade|revision)\b",
    r"\bfrom\s+alembic\b",
    r"\btortoise\b.*\bModel\b",
    r"\bpeewee\b.*\bModel\b",
    r"\bmongodb\b|\bMotorClient\b|\bAsyncIOMotorClient\b",
    # Go/GORM e SQL
    r"\bgorm\.io/gorm\b",
    r"\bdb\.(?:Create|AutoMigrate|Migrator)\(",
    r"\btype\s+\w+\s+struct\s*{.*gorm:",
    r"\b`gorm:",
    r"\bsql\.DB\b|\bsql\.Open\(",
    r"\bdb\.Exec\(.*(?:CREATE|ALTER|DROP)\b",
    r"\bmigrate\b.*\b(?:Up|Down|New|Version)\(",
    r"\bdatabase/sql\b",
    r"\bsqlx\b",
    r"\bsquirrel\b.*\b(?:Insert|Update|Delete|Select)\(",
]

PAT_GRPC = [
    r"\bservice\s+\w+\s*{\s*rpc\s+\w+\(",
    r"\bgrpc\.(NewServer|Server)\b|\bRegister\w+Server\(",
    r"\bgrpc\.Dial\(",
    r"\bgrpc\.NewServer\(",
    r"\bgrpc\.ServerStream\b|\bgrpc\.ClientStream\b",
    r"\bcontext\.Context\b.*\bgrpc\b",
    r"\bprotoc-gen-go\b",
    r"\bpb\.\w+Client\b|\bpb\.\w+Server\b",
    r"\bnet\.Listen\(.*grpc",
]

EXCLUDE_NONE_PATHS = [
    r"\bgo\.mod$", r"\bgo\.sum$",
    r"\bpackage\.json$", r"\byarn\.lock$", r"\bpnpm-lock\.yaml$", r"\bpoetry\.lock$", r"\bPipfile(\.lock)?$",
    r"\bDockerfile(\.[\w\-]+)?$", r"\.dockerignore$", r"\.gitignore$",
    r"\.http$", r"\bapi_requests\b", r"\binsomnia\b", r"\bpostman\b",
    r"\.env(\.[\w\-]+)?$",
    r"\.sh$",  # init scripts
    r"\bflyway\.config$", r"\bliquibase\.properties$",
]

RE_EXCLUDE_NONE = re.compile("|".join(EXCLUDE_NONE_PATHS), re.I)

HINT_PATH_MIGRATION = RX(r"(migrate|migrations?|db/migrate|schema\.prisma|\.sql$|liquibase|flyway|alembic)", re.I)
HINT_PATH_PROTO     = RX(r"\.proto$", re.I)
HINT_PATH_GO        = RX(r"\.go$", re.I)
HINT_PATH_PYTHON    = RX(r"\.py$", re.I)

# Pré-compila
R_ENDPOINTS = [RX(p, re.I) for p in PAT_ENDPOINTS]
R_DISPLAY   = [RX(p, re.I) for p in PAT_DISPLAY]
R_JOBS      = [RX(p, re.I) for p in PAT_JOBS]
R_TRANSFORM = [RX(p, re.I) for p in PAT_TRANSFORM]
R_MODEL     = [RX(p, re.I) for p in PAT_MODEL]
R_DDL       = [RX(p, re.I) for p in PAT_DDL]
R_GRPC      = [RX(p, re.I) for p in PAT_GRPC]

def _any(patterns, text: str) -> bool:
    return any(r.search(text) for r in patterns)

def _boundary_for(patch: str, path: str) -> str:
    if _any(R_ENDPOINTS, patch) or _any(R_GRPC, patch):
        return "API"
    if _any(R_JOBS, patch):
        return "BATCH"
    if re.search(r"\.(kt|swift|java)$", path):
        return "MOBILE"
    if re.search(r"\.go$", path):
        return "BACKEND"
    if re.search(r"\.py$", path):
        return "BACKEND"
    return "UNKNOWN"

# -------------------------------
# Estimadores de DET/FTR/RET
# -------------------------------
_KEY_RX      = re.compile(r'["\']([A-Za-z_][\w\-]*)["\']\s*:', re.M)
_PARAM_RX    = re.compile(r'[{(,]\s*([A-Za-z_][\w]*)\s*[:=]', re.M)
_DB_HINT_RX  = re.compile(r'\b(Model|Table|Entity|Repository|DAO|collection|INSERT|UPDATE|DELETE|CREATE\s+TABLE)\b', re.I)
_EXT_CALL_RX = re.compile(r'\b(http|requests|axios|fetch|http\.Client|grpc\.Dial)\b', re.I)
_REPO_CALL_RX= re.compile(r'\b(repo|repository|dao|db)\.', re.I)

def estimate_det(snippet: str) -> int:
    keys = set(_KEY_RX.findall(snippet))
    params = set(_PARAM_RX.findall(snippet))
    return min(60, len(keys | params)) or 1

def estimate_ftr(snippet: str) -> int:
    hits = 0
    hits += 1 if _REPO_CALL_RX.search(snippet) else 0
    hits += 1 if re.search(r'\b(select|from|join)\b', snippet, re.I) else 0
    hits += 1 if re.search(r'\b(collection|table|model)\b', snippet, re.I) else 0
    return max(1, min(6, hits))

def estimate_ret_for_ali(snippet: str) -> int:
    ret = 0
    ret += len(re.findall(r'\b(createTable|ALTER\s+TABLE|PRIMARY\s+KEY|FOREIGN\s+KEY)\b', snippet, re.I))
    ret += len(re.findall(r'\bmodel\s+\w+\s*{', snippet))             # Prisma
    ret += len(re.findall(r'\btype\s+\w+\s+struct\s*{', snippet))     # Go structs
    return max(1, min(6, ret or 1))

def is_write(patch: str) -> bool:
    return bool(re.search(r'\b(POST|PUT|PATCH|DELETE)\b', patch, re.I) or
                re.search(r'\b(insert|update|delete|save|create)\b', patch, re.I))

def is_transform(snippet: str) -> bool:
    return bool(re.search(r'\b(sum|avg|group|aggregate|map|reduce|pivot|join)\b', snippet, re.I))

def is_external(snippet: str) -> bool:
    return bool(_EXT_CALL_RX.search(snippet))

def decide_tx_type(patch: str, snippet: str) -> str:
    if is_write(patch):
        return "EE"
    # GET com transformação/derivação -> SE; caso contrário CE
    return "SE" if is_transform(snippet) else "CE"

# -------------------------------
# Parser principal (APF)
# -------------------------------
class HeuristicDiffParserAPFv3:
    def detect_functional_units(self, pr: PullRequest) -> List[FunctionalUnit]:
        units: List[FunctionalUnit] = []

        for f in pr.files:
            patch = f.patch or ""
            cat = _cat(f.status)
            snippet = _extract_hunk_snippet(patch, 24)
            a, b = _lines_added(patch)
            boundary = _boundary_for(patch, f.path)

            def evidence(why: str) -> Evidence:
                return Evidence(file=f.path, hunk=snippet, line_from=a, line_to=b, rationale=why)

            emitted = False

            # --- DADOS (ALI por DDL/Schema) ---
            if HINT_PATH_MIGRATION.search(f.path) or _any(R_DDL, patch):
                det = estimate_det(snippet)
                ret = estimate_ret_for_ali(snippet)
                units.append(FunctionalUnit(
                    boundary=boundary, method="APF", type="ALI",
                    category=cat, evidence=evidence("alteração de esquema/DDL detectada"),
                    det=det, ret=ret
                ))
                emitted = True  # DDL tende a ser suficiente para uma unidade de dados

            # --- AIE (somente leitura externa, sem manutenção interna) ---
            if is_external(snippet) and not _DB_HINT_RX.search(snippet):
                det = estimate_det(snippet)
                ret = 1
                units.append(FunctionalUnit(
                    boundary=boundary, method="APF", type="AIE",
                    category=cat, evidence=evidence("referência a dados externos (API/serviço)"),
                    det=det, ret=ret, external_ref=True
                ))
                emitted = True

            # --- TRANSAÇÕES: endpoint/serviço/batch ---
            if _any(R_ENDPOINTS, patch) or _any(R_GRPC, patch) or _any(R_JOBS, patch):
                tx = decide_tx_type(patch, snippet)  # EE/SE/CE
                det = estimate_det(snippet)
                ftr = estimate_ftr(snippet)
                units.append(FunctionalUnit(
                    boundary=boundary, method="APF", type=tx,
                    category=cat, evidence=evidence("endpoint/serviço/batch detectado"),
                    det=det, ftr=ftr, is_write=is_write(patch), external_ref=is_external(snippet)
                ))
                emitted = True

            # --- TRANSFORMAÇÃO/RETORNO (quando não pegou via endpoint) ---
            if not emitted and (_any(R_TRANSFORM, patch) or _any(R_DISPLAY, patch) or _any(R_MODEL, patch)):
                tx = decide_tx_type(patch, snippet)
                det = estimate_det(snippet)
                ftr = estimate_ftr(snippet)
                units.append(FunctionalUnit(
                    boundary=boundary, method="APF", type=tx,
                    category=cat, evidence=evidence("transformação/retorno/modelo IA detectado"),
                    det=det, ftr=ftr, is_write=is_write(patch), external_ref=is_external(snippet)
                ))

            # --- .proto → pode registrar como AIE/contrato; opcionalmente mapear como ALI se mantido internamente ---
            if HINT_PATH_PROTO.search(f.path):
                det = estimate_det(snippet)
                units.append(FunctionalUnit(
                    boundary=boundary, method="APF", type="AIE",
                    category=cat, evidence=evidence("contrato gRPC/proto detectado"),
                    det=det, ret=1, external_ref=True
                ))

        return units