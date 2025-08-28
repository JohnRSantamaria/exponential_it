import uvicorn
from app.core.settings import settings


if __name__ == "__main__":
    host = settings.HOST
    port = settings.PORT
    debug = settings.DEBUG

    uvicorn.run("app.main:app", host=host, port=port, reload=debug)
