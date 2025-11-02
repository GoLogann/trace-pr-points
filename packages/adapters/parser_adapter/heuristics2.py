import re
from typing import List
from packages.core.entities.pull_request import PullRequest
from packages.core.entities.functional_unit import FunctionalUnit, Evidence

RX = lambda p, flags=0: re.compile(p, flags)

H_ENDPOINT = RX(r"(?:@app|router|app)\.(get|post|put|patch|delete)\(|\br\.(GET|POST|PUT|PATCH|DELETE)\(")
H_JOB      = RX(r"\b(cron|Airflow|Celery|APScheduler|schedule)\b", re.I)
H_TRANSF   = RX(r"(clean|normaliz(e|ar)|transform|preprocess|tokeni[sz]e)")
H_MODEL    = RX(r"\.(predict|invoke|generate)\(|openai\.|anthropic\.|bedrock|langchain\..*(invoke|predict|stream)")
H_DISPLAY  = RX(r"\bSELECT\b|\bto_json\b|return\s+JSONResponse|res\.json\(|render_template|fastapi\.responses\.", re.I)
H_DDL      = RX(r"\b(CREATE|ALTER)\s+TABLE\b|Column\(|Table\(|class\s+\w+\(Base\):")

def _cat(status: str) -> str:
    return "INCL" if status=="added" else "EXC" if status=="removed" else "ALT"

def _lines_added(patch: str) -> tuple[int,int]:
    if not patch: return (0,0)
    new_line = start = end = None
    for line in patch.splitlines():
        m = re.match(r"@@ -\d+(?:,\d+)? \+(\d+)", line)
        if m: new_line = int(m.group(1)); continue
        if new_line is None: continue
        if line.startswith('+') and not line.startswith('+++'):
            if start is None: start = new_line
            end = new_line
            new_line += 1
        elif line.startswith(' '):
            new_line += 1
    return (start or 0, end or 0)

class HeuristicDiffParserV2:
    def detect_functional_units(self, pr: PullRequest) -> List[FunctionalUnit]:
        units: List[FunctionalUnit] = []
        for f in pr.files:
            p = f.patch or ""
            cat = _cat(f.status)
            boundary = "API" if H_ENDPOINT.search(p) else ("BATCH" if H_JOB.search(p) else "UNKNOWN")
            a,b = _lines_added(p)
            emitted = set()

            def emit(kind: str, why: str):
                if kind in emitted: return
                emitted.add(kind)
                units.append(FunctionalUnit(
                    boundary=boundary, method="SFP", type="PE" if kind!="AL" else "AL", category=cat,
                    evidence=Evidence(file=f.path, hunk="…", line_from=a, line_to=b, rationale=why)
                ))

            if H_ENDPOINT.search(p): emit("PE","endpoint/rota detectado")
            if H_TRANSF.search(p):  emit("PE","transformação de dados detectada")
            if H_MODEL.search(p):   emit("PE","invocação de modelo detectada")
            if H_DISPLAY.search(p): emit("PE","exibição/consulta de dados detectada")
            if H_DDL.search(p):     emit("AL","DDL/ORM detectado")
        return units
