from app.services.logger.schemas.queries import INIT_SQL


async def ensure_schema(pool):
    async with pool.acquire() as conn:
        await conn.execute("SELECT pg_advisory_lock(42);")
        try:
            await conn.execute(INIT_SQL)
        finally:
            await conn.execute("SELECT pg_advisory_unlock(42);")
