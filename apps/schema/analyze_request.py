from pydantic import BaseModel

class AnalyzeRequest(BaseModel):
    pr_url: str
