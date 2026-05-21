from typing import Optional

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserRead(BaseModel):
    id: int
    email: EmailStr
    full_name: str

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class OperationCreate(BaseModel):
    group_code: str
    operation_name: str
    unit: str = "operation"
    minutes_per_cycle: float = 1.0
    rate_per_hour: float = 700.0


class OperationRead(OperationCreate):
    id: int

    model_config = {"from_attributes": True}


class ProjectCreate(BaseModel):
    name: str
    customer_name: str
    customer_details: str = ""
    contractor_name: str
    contractor_details: str = ""
    overhead_percent: float = 12.0
    margin_percent: float = 20.0
    vat_percent: float = 20.0


class ProjectRead(ProjectCreate):
    id: int
    created_by_id: int

    model_config = {"from_attributes": True}


class AssemblyCreate(BaseModel):
    code: str
    product_name: str
    qty_tier_1: int
    qty_tier_2: int
    qty_tier_3: int
    qty_tier_4: int


class AssemblyRead(AssemblyCreate):
    id: int
    project_id: int

    model_config = {"from_attributes": True}


class ComponentCreate(BaseModel):
    article: str
    component_type: str
    description: str = ""
    qty_per_set: float
    linear_value: float = 0.0
    unit: str = "pcs"
    unit_price: float = 0.0
    source_url: str = ""


class ComponentRead(ComponentCreate):
    id: int
    assembly_id: int

    model_config = {"from_attributes": True}


class RouteStepCreate(BaseModel):
    operation_catalog_id: int
    repeats_per_set: float = 1.0
    operators_count: float = 1.0


class RouteStepRead(RouteStepCreate):
    id: int
    assembly_id: int

    model_config = {"from_attributes": True}


class TierSummary(BaseModel):
    tier_label: str
    quantity: int
    materials_cost: float
    labor_cost: float
    production_cost: float
    overhead_cost: float
    subtotal_without_vat: float
    total_with_vat: float
    unit_price_with_vat: float


class AssemblySummary(BaseModel):
    assembly_id: int
    code: str
    product_name: str
    tiers: list[TierSummary]


class GroupedComponent(BaseModel):
    article: str
    component_type: str
    unit: str
    total_quantity_tier_1: float
    total_quantity_tier_2: float
    total_quantity_tier_3: float
    total_quantity_tier_4: float
    weighted_avg_unit_price: float
    source_urls: list[str]


class ProjectCalculation(BaseModel):
    project_id: int
    project_name: str
    grouped_components: list[GroupedComponent]
    assemblies: list[AssemblySummary]
