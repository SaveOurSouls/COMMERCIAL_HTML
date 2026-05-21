from app.models import Assembly, CalculationProject, ComponentSpec, OperationCatalog, RouteStep
from app.services.calculations import calculate_project


def test_project_calculation_builds_tier_prices_and_grouped_spec() -> None:
    project = CalculationProject(
        id=1,
        name="Demo",
        customer_name="Customer",
        contractor_name="Contractor",
        overhead_percent=10,
        margin_percent=20,
        vat_percent=20,
        created_by_id=1,
    )
    assembly = Assembly(
        id=11,
        project_id=1,
        code="КБ1",
        product_name="Product A",
        qty_tier_1=10,
        qty_tier_2=20,
        qty_tier_3=30,
        qty_tier_4=40,
    )
    component = ComponentSpec(
        id=101,
        assembly_id=11,
        article="ART-1",
        component_type="Материал",
        qty_per_set=2.0,
        unit_price=50,
    )
    operation = OperationCatalog(
        id=201,
        group_code="1",
        operation_name="Сборка",
        minutes_per_cycle=6,
        rate_per_hour=600,
    )
    step = RouteStep(
        id=301,
        assembly_id=11,
        operation_catalog_id=201,
        repeats_per_set=1,
        operators_count=1,
    )

    result = calculate_project(
        project=project,
        assemblies=[assembly],
        components=[component],
        route_steps=[step],
        operations_by_id={201: operation},
    )

    tier1 = result.assemblies[0].tiers[0]
    # Material per set: 2 * 50 = 100, labor per set: 6/60 * 600 = 60.
    # For 10 sets: production = 1600; overhead 10% => 160; subtotal with margin 20% => 2112; VAT 20% => 2534.4
    assert tier1.production_cost == 1600.0
    assert tier1.total_with_vat == 2534.4
    assert tier1.unit_price_with_vat == 253.44

    grouped = result.grouped_components[0]
    assert grouped.article == "ART-1"
    assert grouped.total_quantity_tier_1 == 20.0
    assert grouped.total_quantity_tier_4 == 80.0
