# app/api/routes/entry.py
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from typing import List, AsyncIterator
import asyncio, asyncpg, json

from app.services.logger.schemas.event import EventSchema
from app.services.logger.schemas.queries import INSERT_SQL, SELECT_TIMELINE_SQL

router = APIRouter()


@router.post("/events")
async def create_event(request: Request, evt: EventSchema):
    """
    Inserta un evento de auditoría (idempotente por event_id).
    """
    pool = request.app.state.pool
    try:
        async with pool.acquire() as conn:
            await conn.execute(
                INSERT_SQL,
                str(evt.event_id),
                evt.ts,
                evt.invoice_id,
                evt.step,
                evt.status,
                evt.service,
                evt.request_id,
                evt.user,
                evt.date,
                evt.file_name,
                evt.partner_cif,
                evt.partner_name,
                evt.amount_total,
                evt.amount_tax,
                evt.time_process,
                evt.error,
                evt.recommendations,
                json.dumps(evt.meta),
            )
        return {"ok": True, "event_id": str(evt.event_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB insert error: {e}")


@router.get("/timeline/{invoice_id}")
async def timeline(request: Request, invoice_id: str) -> List[dict]:
    """
    Devuelve la línea de tiempo (eventos ordenados) para una factura.
    """
    pool = request.app.state.pool
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(SELECT_TIMELINE_SQL, invoice_id)
        return [dict(r) for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB query error: {e}")


@router.get("/stream")
async def stream(request: Request) -> StreamingResponse:
    """
    SSE: emite cada nuevo INSERT notificado por el trigger 'trg_notif_invoice_event'.
    Requiere que tu init SQL cree la función 'notif_invoice_event' y el trigger.
    """
    PG_DSN = request.app.state.DB_DSN if hasattr(request.app.state, "DB_DSN") else None
    if not PG_DSN:
        # Mantén una copia del DSN en app.state.DB_DSN desde tu lifespan
        raise HTTPException(
            status_code=500, detail="DB_DSN no configurado en app.state"
        )

    async def event_generator() -> AsyncIterator[bytes]:
        conn = await asyncpg.connect(PG_DSN)
        queue: asyncio.Queue[str] = asyncio.Queue()

        def _listener(*args):
            # args: (connection, pid, channel, payload)
            payload = args[3]
            queue.put_nowait(payload)

        await conn.add_listener("invoice_events", _listener)
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    payload = await asyncio.wait_for(queue.get(), timeout=10.0)
                    # Formato SSE
                    yield f"data: {payload}\n\n".encode()
                except asyncio.TimeoutError:
                    # keep-alive para proxies
                    yield b": keep-alive\n\n"
        finally:
            await conn.remove_listener("invoice_events", _listener)
            await conn.close()

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/health")
async def health() -> dict:
    return {"ok": True}
