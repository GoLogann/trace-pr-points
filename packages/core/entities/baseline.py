from dataclasses import dataclass

@dataclass
class Baseline:
    app_id: str
    method: str  # "SFP" | "APF"
    value: float
    release: str | None
