import csv
from io import StringIO
from typing import Annotated

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from sqlmodel import Session, select

from app.database import create_db_and_tables, get_session
from app.models import Assembly, CalculationProject, ComponentSpec, OperationCatalog, RouteStep, User
from app.schemas import (
    AssemblyCreate,
    AssemblyRead,
    ComponentCreate,
    ComponentRead,
    OperationCreate,
    OperationRead,
    ProjectCalculation,
    ProjectCreate,
    ProjectRead,
    RouteStepCreate,
    RouteStepRead,
    Token,
    UserCreate,
    UserLogin,
    UserRead,
)
from app.security import create_access_token, get_current_user, hash_password, verify_password
from app.services.calculations import calculate_project
from app.services.pdf_builder import build_commercial_offer_pdf, build_invoice_pdf

app = FastAPI(
    title="Process Costing Web",
    description="Cloud-ready replacement for Google Sheets-based production costing.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    create_db_and_tables()


@app.get("/")
def index() -> FileResponse:
    return FileResponse("app/static/index.html")


@app.post("/api/auth/register", response_model=UserRead)
def register(payload: UserCreate, session: Annotated[Session, Depends(get_session)]) -> User:
    existing = session.exec(select(User).where(User.email == payload.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email is already registered")
    user = User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@app.post("/api/auth/login", response_model=Token)
def login(payload: UserLogin, session: Annotated[Session, Depends(get_session)]) -> Token:
    user = session.exec(select(User).where(User.email == payload.email)).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return Token(access_token=create_access_token(subject=user.email))


@app.get("/api/me", response_model=UserRead)
def me(user: Annotated[User, Depends(get_current_user)]) -> User:
    return user


@app.post("/api/operations", response_model=OperationRead)
def create_operation(
    payload: OperationCreate,
    _: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> OperationCatalog:
    operation = OperationCatalog(**payload.model_dump())
    session.add(operation)
    session.commit()
    session.refresh(operation)
    return operation


@app.post("/api/operations/import-csv", response_model=list[OperationRead])
async def import_operations_csv(
    file: UploadFile = File(...),
    _: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> list[OperationCatalog]:
    content = await file.read()
    decoded = content.decode("utf-8-sig")
    reader = csv.DictReader(StringIO(decoded))
    inserted: list[OperationCatalog] = []
    for row in reader:
        group_code = row.get("group_code") or row.get("Группа") or row.get("Номер")
        operation_name = row.get("operation_name") or row.get("Операция") or row.get("Комплектующая")
        if not group_code or not operation_name:
            continue

        operation = OperationCatalog(
            group_code=str(group_code).strip(),
            operation_name=str(operation_name).strip(),
            unit=str(row.get("unit") or row.get("Ед") or "operation"),
            minutes_per_cycle=float(row.get("minutes_per_cycle") or row.get("Минуты") or 1),
            rate_per_hour=float(row.get("rate_per_hour") or row.get("Ставка_час") or 700),
        )
        session.add(operation)
        inserted.append(operation)

    session.commit()
    for item in inserted:
        session.refresh(item)
    return inserted


@app.get("/api/operations", response_model=list[OperationRead])
def list_operations(
    _: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> list[OperationCatalog]:
    statement = select(OperationCatalog).order_by(OperationCatalog.group_code, OperationCatalog.operation_name)
    return list(session.exec(statement))


@app.post("/api/projects", response_model=ProjectRead)
def create_project(
    payload: ProjectCreate,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> CalculationProject:
    project = CalculationProject(**payload.model_dump(), created_by_id=user.id or 0)
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


@app.get("/api/projects", response_model=list[ProjectRead])
def list_projects(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> list[CalculationProject]:
    statement = select(CalculationProject).where(CalculationProject.created_by_id == user.id)
    return list(session.exec(statement))


def _get_project(project_id: int, user: User, session: Session) -> CalculationProject:
    project = session.get(CalculationProject, project_id)
    if not project or project.created_by_id != user.id:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@app.post("/api/projects/{project_id}/assemblies", response_model=AssemblyRead)
def create_assembly(
    project_id: int,
    payload: AssemblyCreate,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> Assembly:
    _get_project(project_id, user, session)
    assembly = Assembly(project_id=project_id, **payload.model_dump())
    session.add(assembly)
    session.commit()
    session.refresh(assembly)
    return assembly


@app.get("/api/projects/{project_id}/assemblies", response_model=list[AssemblyRead])
def list_assemblies(
    project_id: int,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> list[Assembly]:
    _get_project(project_id, user, session)
    statement = select(Assembly).where(Assembly.project_id == project_id).order_by(Assembly.code)
    return list(session.exec(statement))


@app.post("/api/assemblies/{assembly_id}/components", response_model=ComponentRead)
def add_component(
    assembly_id: int,
    payload: ComponentCreate,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> ComponentSpec:
    assembly = session.get(Assembly, assembly_id)
    if not assembly:
        raise HTTPException(status_code=404, detail="Assembly not found")
    _get_project(assembly.project_id, user, session)
    component = ComponentSpec(assembly_id=assembly_id, **payload.model_dump())
    session.add(component)
    session.commit()
    session.refresh(component)
    return component


@app.get("/api/assemblies/{assembly_id}/components", response_model=list[ComponentRead])
def list_components(
    assembly_id: int,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> list[ComponentSpec]:
    assembly = session.get(Assembly, assembly_id)
    if not assembly:
        raise HTTPException(status_code=404, detail="Assembly not found")
    _get_project(assembly.project_id, user, session)
    statement = select(ComponentSpec).where(ComponentSpec.assembly_id == assembly_id).order_by(ComponentSpec.article)
    return list(session.exec(statement))


@app.post("/api/assemblies/{assembly_id}/route-steps", response_model=RouteStepRead)
def add_route_step(
    assembly_id: int,
    payload: RouteStepCreate,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> RouteStep:
    assembly = session.get(Assembly, assembly_id)
    if not assembly:
        raise HTTPException(status_code=404, detail="Assembly not found")
    _get_project(assembly.project_id, user, session)
    operation = session.get(OperationCatalog, payload.operation_catalog_id)
    if not operation:
        raise HTTPException(status_code=404, detail="Operation not found")
    route_step = RouteStep(assembly_id=assembly_id, **payload.model_dump())
    session.add(route_step)
    session.commit()
    session.refresh(route_step)
    return route_step


@app.get("/api/assemblies/{assembly_id}/route-steps", response_model=list[RouteStepRead])
def list_route_steps(
    assembly_id: int,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> list[RouteStep]:
    assembly = session.get(Assembly, assembly_id)
    if not assembly:
        raise HTTPException(status_code=404, detail="Assembly not found")
    _get_project(assembly.project_id, user, session)
    statement = select(RouteStep).where(RouteStep.assembly_id == assembly_id)
    return list(session.exec(statement))


def _build_calculation(project_id: int, user: User, session: Session) -> tuple[CalculationProject, ProjectCalculation]:
    project = _get_project(project_id, user, session)
    assemblies = list(session.exec(select(Assembly).where(Assembly.project_id == project_id)))
    assembly_ids = [assembly.id for assembly in assemblies if assembly.id is not None]

    components: list[ComponentSpec] = []
    route_steps: list[RouteStep] = []
    if assembly_ids:
        components = list(session.exec(select(ComponentSpec).where(ComponentSpec.assembly_id.in_(assembly_ids))))
        route_steps = list(session.exec(select(RouteStep).where(RouteStep.assembly_id.in_(assembly_ids))))

    operation_ids = [step.operation_catalog_id for step in route_steps]
    operations = []
    if operation_ids:
        operations = list(session.exec(select(OperationCatalog).where(OperationCatalog.id.in_(operation_ids))))
    operations_map = {operation.id: operation for operation in operations if operation.id is not None}

    calculation = calculate_project(
        project=project,
        assemblies=assemblies,
        components=components,
        route_steps=route_steps,
        operations_by_id=operations_map,
    )
    return project, calculation


@app.get("/api/projects/{project_id}/calculation", response_model=ProjectCalculation)
def project_calculation(
    project_id: int,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> ProjectCalculation:
    _, calculation = _build_calculation(project_id, user, session)
    return calculation


@app.get("/api/projects/{project_id}/pdf/offer")
def project_offer_pdf(
    project_id: int,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
    tier: int = Query(default=1, ge=1, le=4),
) -> Response:
    project, calculation = _build_calculation(project_id, user, session)
    pdf = build_commercial_offer_pdf(project, calculation, tier_index=tier - 1)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="offer-project-{project_id}.pdf"'},
    )


@app.get("/api/projects/{project_id}/pdf/invoice")
def project_invoice_pdf(
    project_id: int,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
    tier: int = Query(default=1, ge=1, le=4),
) -> Response:
    project, calculation = _build_calculation(project_id, user, session)
    pdf = build_invoice_pdf(project, calculation, tier_index=tier - 1)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="invoice-project-{project_id}.pdf"'},
    )
