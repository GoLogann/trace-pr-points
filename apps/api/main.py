from urllib.parse import urlparse
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import hmac, hashlib, json

# LangGraph
from apps.schema.analyze_request import AnalyzeRequest
from infra.config import settings
from infra.db.sql import Base, make_engine, make_session_factory
from infra.di_container import build_graph_compiled

engine = make_engine(settings.database_url)
SessionLocal = make_session_factory(engine)
Base.metadata.create_all(bind=engine)

from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="PR Points SaaS",
    description="API para análise de Pontos de Função em Pull Requests",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def _verify_signature(payload: bytes, signature: str | None):
    if not signature:
        raise HTTPException(400, "Missing signature")
    mac = hmac.new(settings.github_webhook_secret.encode(), msg=payload, digestmod=hashlib.sha256)
    expected = "sha256=" + mac.hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(401, "Invalid signature")

@app.post("/webhooks/github")
async def github_webhook(request: Request, x_hub_signature_256: str | None = Header(None), x_github_event: str = Header(...)):
    body = await request.body()
    _verify_signature(body, x_hub_signature_256)
    event = json.loads(body.decode())

    if x_github_event == "pull_request":
        action = event.get("action")
        if action in {"opened","synchronize","reopened"}:
            repo_full = event["repository"]["full_name"]
            number = event["number"]
            g = build_graph_compiled()
            # inicializa estado mínimo
            state = {"repo": repo_full, "pr_number": number, "pr_head_sha": "", "files_count": 0,
                     "units": [], "result": None, "rag_refs": [], "explanation": None, "ambiguous": False}
            out = g.invoke(state)
            res = out["result"]
            return {"ok": True, "sfp": res.total_sfp if res else 0.0, "ambiguous": out.get("ambiguous", False)}
    return {"ok": True}


@app.post("/analyze_pr")
async def analyze_pr(request: AnalyzeRequest):
    pr_url = request.pr_url
    try:
        u = urlparse(pr_url)
        parts = [p for p in u.path.rstrip("/").split("/") if p]
        # esperado: /{owner}/{repo}/pull/{number}
        owner, repo, _, number = parts[0], parts[1], parts[2], parts[3]
        if _ != "pull":
            raise ValueError("URL não parece ser de um Pull Request")
        repo_full = f"{owner}/{repo}"
        pr_number = int(number)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"PR URL inválido: {pr_url} ({e})")

    g = build_graph_compiled()
    state = {
        "repo": repo_full,
        "pr_number": pr_number,
        "pr_head_sha": "",
        "files_count": 0,
        "units": [],
        "result": None,
        "rag_refs": [],
        "explanation": None,
        "ambiguous": False,
    }

    out = g.invoke(state)
    result = out.get("result")

    if not result:
        return {"ok": False, "error": "sem resultado", "ambiguous": out.get("ambiguous", False)}

    # Coalescer total (APF > SFP) e identificar método
    total_apf = getattr(result, "total_apf", None)
    total_sfp = getattr(result, "total_sfp", None)
    total = result.total()  # usa APF se houver, senão SFP, senão 0.0
    method = "APF" if total_apf is not None else "SFP"

    payload = {
        "ok": True,
        "method": method,
        "total": round(float(total), 2),
        "total_apf": None if total_apf is None else round(float(total_apf), 2),
        "total_sfp": None if total_sfp is None else round(float(total_sfp), 2),
        "formula": result.formula_text,
        "totals": {
            "pe_incl": result.totals.pe_incl, "pe_alt": result.totals.pe_alt, "pe_exc": result.totals.pe_exc,
            "al_incl": result.totals.al_incl, "al_alt": result.totals.al_alt, "al_exc": result.totals.al_exc,
        },
        "units_count": len(result.units),
        "ambiguous": out.get("ambiguous", False),
        "explanation": out.get("explanation"),
    }
    return payload

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)