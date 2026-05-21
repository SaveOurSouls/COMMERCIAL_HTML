from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    full_name: str
    hashed_password: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=utc_now)


class OperationCatalog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    group_code: str = Field(index=True)
    operation_name: str = Field(index=True)
    unit: str = "operation"
    minutes_per_cycle: float = 1.0
    rate_per_hour: float = 700.0
    created_at: datetime = Field(default_factory=utc_now)


class CalculationProject(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    customer_name: str
    customer_details: str = ""
    contractor_name: str
    contractor_details: str = ""
    overhead_percent: float = 12.0
    margin_percent: float = 20.0
    vat_percent: float = 20.0
    created_by_id: int = Field(foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=utc_now)


class Assembly(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="calculationproject.id", index=True)
    code: str = Field(index=True)
    product_name: str
    qty_tier_1: int
    qty_tier_2: int
    qty_tier_3: int
    qty_tier_4: int
    created_at: datetime = Field(default_factory=utc_now)


class ComponentSpec(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    assembly_id: int = Field(foreign_key="assembly.id", index=True)
    article: str
    component_type: str
    description: str = ""
    qty_per_set: float
    linear_value: float = 0.0
    unit: str = "pcs"
    unit_price: float = 0.0
    source_url: str = ""
    created_at: datetime = Field(default_factory=utc_now)


class RouteStep(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    assembly_id: int = Field(foreign_key="assembly.id", index=True)
    operation_catalog_id: int = Field(foreign_key="operationcatalog.id", index=True)
    repeats_per_set: float = 1.0
    operators_count: float = 1.0
    created_at: datetime = Field(default_factory=utc_now)
