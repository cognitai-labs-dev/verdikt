from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncConnection

from src.api.deps import require_admin
from src.api.v1.response import ORJsonResponse
from src.api.v1.schemas import (
    AddAppBindingRequest,
    AppRef,
    CreateMachineClientRequest,
    CreatedMachineClientResponse,
    ErrorResponse,
    MachineClientResponse,
)
from src.constants import SubjectType
from src.dependencies import (
    app_principal_repo,
    app_repo,
    auth_commands,
    get_connection,
    machine_client_repo,
    machine_token_repo,
)
from src.schemas.machine_client import MachineClientSchema

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    default_response_class=ORJsonResponse,
    dependencies=[Depends(require_admin)],
)


async def _apps_for_client(
    conn: AsyncConnection, client_id: str
) -> list[AppRef]:
    """Resolve the CLIENT bindings of a machine client to app references."""
    app_ids = await app_principal_repo.app_ids_for(
        conn, SubjectType.CLIENT, client_id
    )
    if not app_ids:
        return []
    apps = await app_repo.get_by_many_ids(conn, app_ids)
    return [AppRef(id=app.id, slug=app.slug) for app in apps]


async def _to_response(
    conn: AsyncConnection, client: MachineClientSchema
) -> MachineClientResponse:
    return MachineClientResponse(
        id=client.id,
        client_id=client.client_id,
        name=client.name,
        is_admin=client.is_admin,
        revoked=client.revoked,
        created_at=client.created_at,
        apps=await _apps_for_client(conn, client.client_id),
    )


@router.get(
    "/machine-clients",
    operation_id="getMachineClients",
    description="List all machine clients and the apps they are bound to.",
)
async def get_machine_clients(
    conn: AsyncConnection = Depends(get_connection),
) -> list[MachineClientResponse]:
    clients = await machine_client_repo.get_many(conn)
    return [await _to_response(conn, client) for client in clients]


@router.post(
    "/machine-clients",
    operation_id="postMachineClient",
    status_code=201,
    description="Create a machine client. The client_secret is returned ONCE.",
    responses={
        400: {"model": ErrorResponse},
    },
)
async def post_machine_client(
    request: CreateMachineClientRequest,
    conn: AsyncConnection = Depends(get_connection),
) -> CreatedMachineClientResponse:
    try:
        (
            client,
            raw_secret,
        ) = await auth_commands.create_machine_client(
            conn,
            name=request.name,
            is_admin=request.is_admin,
            app_slugs=request.app_slugs,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    base = await _to_response(conn, client)
    return CreatedMachineClientResponse(
        **base.model_dump(), client_secret=raw_secret
    )


@router.post(
    "/machine-clients/{client_id}/revoke",
    operation_id="revokeMachineClient",
    description="Soft-revoke a client and kill its live tokens.",
    responses={
        404: {"model": ErrorResponse},
    },
)
async def revoke_machine_client(
    client_id: str,
    conn: AsyncConnection = Depends(get_connection),
) -> MachineClientResponse:
    client = await machine_client_repo.set_revoked(
        conn, client_id, True
    )
    if client is None:
        raise HTTPException(
            status_code=404, detail="Machine client not found"
        )
    await machine_token_repo.revoke_for_client(conn, client_id)
    return await _to_response(conn, client)


@router.post(
    "/machine-clients/{client_id}/unrevoke",
    operation_id="unrevokeMachineClient",
    description="Reverse a soft-revoke.",
    responses={
        404: {"model": ErrorResponse},
    },
)
async def unrevoke_machine_client(
    client_id: str,
    conn: AsyncConnection = Depends(get_connection),
) -> MachineClientResponse:
    client = await machine_client_repo.set_revoked(
        conn, client_id, False
    )
    if client is None:
        raise HTTPException(
            status_code=404, detail="Machine client not found"
        )
    return await _to_response(conn, client)


@router.post(
    "/machine-clients/{client_id}/apps",
    operation_id="bindMachineClientApp",
    status_code=201,
    description="Bind a machine client to an app.",
    responses={
        404: {"model": ErrorResponse},
    },
)
async def bind_machine_client_app(
    client_id: str,
    request: AddAppBindingRequest,
    conn: AsyncConnection = Depends(get_connection),
) -> MachineClientResponse:
    client = await machine_client_repo.get_by_client_id(
        conn, client_id
    )
    if client is None:
        raise HTTPException(
            status_code=404, detail="Machine client not found"
        )
    app = await app_repo.get(conn, request.app_id)
    if app is None:
        raise HTTPException(status_code=404, detail="App not found")
    await app_principal_repo.add(
        conn, app.id, SubjectType.CLIENT, client_id
    )
    return await _to_response(conn, client)


@router.delete(
    "/machine-clients/{client_id}/apps/{app_id}",
    operation_id="unbindMachineClientApp",
    description="Remove a machine client's binding to an app.",
    responses={
        404: {"model": ErrorResponse},
    },
)
async def unbind_machine_client_app(
    client_id: str,
    app_id: int,
    conn: AsyncConnection = Depends(get_connection),
) -> MachineClientResponse:
    client = await machine_client_repo.get_by_client_id(
        conn, client_id
    )
    if client is None:
        raise HTTPException(
            status_code=404, detail="Machine client not found"
        )
    await app_principal_repo.remove(
        conn, app_id, SubjectType.CLIENT, client_id
    )
    return await _to_response(conn, client)
