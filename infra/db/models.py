from sqlalchemy import String, Float, Text, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column
from infra.db.sql import Base

class BaselineModel(Base):
    __tablename__ = "baseline"
    app_id: Mapped[str]   = mapped_column(String(200), primary_key=True)
    method: Mapped[str]   = mapped_column(String(10), primary_key=True)  # "SFP" | "APF"
    value:  Mapped[float] = mapped_column(Float, default=0.0)
    release: Mapped[str | None] = mapped_column(String(50), nullable=True)

class PRReportModel(Base):
    __tablename__ = "pr_report"
    repo:      Mapped[str] = mapped_column(String(200), primary_key=True)
    pr_number: Mapped[int] = mapped_column(Integer, primary_key=True)
    ts:        Mapped[int] = mapped_column(Integer, primary_key=True)  # epoch

    total_sfp: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_apf: Mapped[float | None] = mapped_column(Float, nullable=True)

    formula:   Mapped[str]   = mapped_column(Text)
    totals:    Mapped[dict]  = mapped_column(JSON)
    units:     Mapped[list]  = mapped_column(JSON)
