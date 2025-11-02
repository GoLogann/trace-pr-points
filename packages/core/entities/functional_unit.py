from dataclasses import dataclass
from typing import Literal

Boundary = Literal["WEB","API","MOBILE","BATCH","BACKEND","UNKNOWN"]
Method   = Literal["APF"]
TypeSFP  = Literal["EE","SE", "CE", "ALI", "AIE"]
Category = Literal["INCL","ALT","EXC"]

@dataclass
class Evidence:
    file: str
    hunk: str
    line_from: int
    line_to: int
    rationale: str
    
@dataclass
class FunctionalUnit:
    boundary: Boundary
    method: Method
    type: TypeSFP
    category: Category
    evidence: Evidence
    
        # --- Campos para APF/complexidade ---
    det: int = 0                  # Data Element Types (transações) ou DET de ALI/AIE
    ftr: int = 0                  # File Types Referenced (transações)
    ret: int = 0                  # Record Element Types (para ALI/AIE)
    # opcional: flags úteis
    is_write: bool = False        # se transação escreve
    external_ref: bool = False    # se referencia dados externos (AIE)
