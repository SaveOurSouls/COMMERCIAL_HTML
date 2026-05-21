from collections import defaultdict

from app.models import Assembly, CalculationProject, ComponentSpec, OperationCatalog, RouteStep
from app.schemas import (
    AssemblySummary,
    GroupedComponent,
    ProjectCalculation,
    TierSummary,
)


def _assembly_quantities(assembly: Assembly) -> list[int]:
    return [
        assembly.qty_tier_1,
        assembly.qty_tier_2,
        assembly.qty_tier_3,
        assembly.qty_tier_4,
    ]


def build_grouped_components(
    assemblies: list[Assembly],
    components: list[ComponentSpec],
) -> list[GroupedComponent]:
    assembly_map = {assembly.id: assembly for assembly in assemblies}
    bucket: dict[tuple[str, str, str], dict[str, object]] = defaultdict(
        lambda: {
            "tier_1": 0.0,
            "tier_2": 0.0,
            "tier_3": 0.0,
            "tier_4": 0.0,
            "price_weight": 0.0,
            "price_qty": 0.0,
            "source_urls": set(),
        }
    )

    for component in components:
        assembly = assembly_map.get(component.assembly_id)
        if not assembly:
            continue

        key = (component.article, component.component_type, component.unit)
        entry = bucket[key]
        quantities = _assembly_quantities(assembly)

        entry["tier_1"] = float(entry["tier_1"]) + component.qty_per_set * quantities[0]
        entry["tier_2"] = float(entry["tier_2"]) + component.qty_per_set * quantities[1]
        entry["tier_3"] = float(entry["tier_3"]) + component.qty_per_set * quantities[2]
        entry["tier_4"] = float(entry["tier_4"]) + component.qty_per_set * quantities[3]
        entry["price_weight"] = float(entry["price_weight"]) + component.unit_price * component.qty_per_set
        entry["price_qty"] = float(entry["price_qty"]) + component.qty_per_set
        if component.source_url:
            source_urls = entry["source_urls"]
            if isinstance(source_urls, set):
                source_urls.add(component.source_url)

    grouped: list[GroupedComponent] = []
    for (article, component_type, unit), values in bucket.items():
        price_qty = float(values["price_qty"]) or 1.0
        weighted_price = float(values["price_weight"]) / price_qty
        source_urls = values["source_urls"]
        grouped.append(
            GroupedComponent(
                article=article,
                component_type=component_type,
                unit=unit,
                total_quantity_tier_1=round(float(values["tier_1"]), 3),
                total_quantity_tier_2=round(float(values["tier_2"]), 3),
                total_quantity_tier_3=round(float(values["tier_3"]), 3),
                total_quantity_tier_4=round(float(values["tier_4"]), 3),
                weighted_avg_unit_price=round(weighted_price, 2),
                source_urls=sorted(source_urls) if isinstance(source_urls, set) else [],
            )
        )
    return sorted(grouped, key=lambda item: (item.component_type, item.article))


def calculate_project(
    project: CalculationProject,
    assemblies: list[Assembly],
    components: list[ComponentSpec],
    route_steps: list[RouteStep],
    operations_by_id: dict[int, OperationCatalog],
) -> ProjectCalculation:
    components_by_assembly: dict[int, list[ComponentSpec]] = defaultdict(list)
    steps_by_assembly: dict[int, list[RouteStep]] = defaultdict(list)

    for component in components:
        components_by_assembly[component.assembly_id].append(component)
    for step in route_steps:
        steps_by_assembly[step.assembly_id].append(step)

    assembly_summaries: list[AssemblySummary] = []
    for assembly in assemblies:
        quantities = _assembly_quantities(assembly)
        tiers: list[TierSummary] = []

        labor_per_set = 0.0
        for step in steps_by_assembly[assembly.id or 0]:
            operation = operations_by_id.get(step.operation_catalog_id)
            if not operation:
                continue
            labor_per_set += (
                step.repeats_per_set
                * step.operators_count
                * operation.minutes_per_cycle
                / 60.0
                * operation.rate_per_hour
            )

        material_per_set = sum(
            component.qty_per_set * component.unit_price
            for component in components_by_assembly[assembly.id or 0]
        )

        for index, quantity in enumerate(quantities, start=1):
            materials_cost = material_per_set * quantity
            labor_cost = labor_per_set * quantity
            production_cost = materials_cost + labor_cost
            overhead_cost = production_cost * project.overhead_percent / 100.0
            subtotal_without_vat = (production_cost + overhead_cost) * (1 + project.margin_percent / 100.0)
            total_with_vat = subtotal_without_vat * (1 + project.vat_percent / 100.0)
            unit_price_with_vat = total_with_vat / quantity if quantity else 0.0

            tiers.append(
                TierSummary(
                    tier_label=f"Кол-во {index}",
                    quantity=quantity,
                    materials_cost=round(materials_cost, 2),
                    labor_cost=round(labor_cost, 2),
                    production_cost=round(production_cost, 2),
                    overhead_cost=round(overhead_cost, 2),
                    subtotal_without_vat=round(subtotal_without_vat, 2),
                    total_with_vat=round(total_with_vat, 2),
                    unit_price_with_vat=round(unit_price_with_vat, 2),
                )
            )

        assembly_summaries.append(
            AssemblySummary(
                assembly_id=assembly.id or 0,
                code=assembly.code,
                product_name=assembly.product_name,
                tiers=tiers,
            )
        )

    grouped_components = build_grouped_components(assemblies, components)
    return ProjectCalculation(
        project_id=project.id or 0,
        project_name=project.name,
        grouped_components=grouped_components,
        assemblies=assembly_summaries,
    )
