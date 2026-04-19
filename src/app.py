"""FastAPI webhook server for Google Actions → Sky Q voice control."""
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from .device_registry import DeviceRegistry
from .intents import handle_help, handle_list_devices, handle_sky_control

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

registry = DeviceRegistry()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Sky Q Voice Control starting. Registered devices: %s", registry.devices)
    yield


app = FastAPI(
    title="Sky Q Voice Control",
    description="Google Actions webhook that routes voice commands to Sky Q boxes via pyskyq.",
    version="1.0.0",
    lifespan=lifespan,
)

INTENT_HANDLERS = {
    "SkyControl": lambda p: handle_sky_control(p, registry),
    "SkyPower": lambda p: handle_sky_control(p, registry),
    "ListDevices": lambda _: handle_list_devices(registry),
    "Help": lambda _: handle_help(),
}


@app.post("/webhook")
async def webhook(request: Request) -> JSONResponse:
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    handler_name = payload.get("handler", {}).get("name", "")
    intent_name = payload.get("intent", {}).get("name", "")
    logger.debug("handler=%r intent=%r", handler_name, intent_name)

    # Match by handler name first, fall back to intent name
    key = handler_name or intent_name
    handler = INTENT_HANDLERS.get(key)
    if handler is None:
        # Default: try to treat it as a SkyControl intent
        handler = INTENT_HANDLERS.get("SkyControl")

    response = handler(payload)
    return JSONResponse(content=response)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "devices": registry.devices}


@app.get("/devices")
async def devices() -> dict:
    return {"devices": registry.devices}


@app.get("/commands")
async def commands() -> dict:
    from .sky_controller import SkyController
    return {"commands": SkyController.known_commands()}
