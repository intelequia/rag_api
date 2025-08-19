# main.py
import os
from dotenv import find_dotenv, load_dotenv
load_dotenv(find_dotenv())

import uvicorn
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor

from starlette.responses import JSONResponse

from app.config import (
    VectorDBType,
    debug_mode,
    RAG_HOST,
    RAG_PORT,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    PDF_EXTRACT_IMAGES,
    VECTOR_DB_TYPE,
    LogMiddleware,
    logger,
)
from app.middleware import security_middleware
from app.routes import document_routes, pgvector_routes
from app.services.database import PSQLDatabase, ensure_vector_indexes


import json  
#### Azure Application Insights telemetry ####
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import trace
from opentelemetry.trace import (
    SpanKind,
    get_tracer_provider,
    set_tracer_provider,
)
from opentelemetry.propagate import extract

# import logging
# from logging import getLogger, INFO

configure_azure_monitor( connection_string=os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING"))


# # Configurar el registrador específico de azure.core.pipeline.policies.http_logging_policy
# http_logging_logger = logging.getLogger('azure.core.pipeline.policies.http_logging_policy')
# http_logging_logger.setLevel(logging.WARNING)  # Para deshabilitar los logs de INFO y mostrar solo WARNING y superiores

# # Configurar logging para azure.monitor también si es necesario
# monitor_exporter_logger = logging.getLogger('azure.monitor.opentelemetry.exporter.export._base')
# monitor_exporter_logger.setLevel(logging.WARNING)

# tracer = trace.get_tracer(__name__, tracer_provider=get_tracer_provider())
# logger = logging.getLogger(__name__)

####


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic goes here
    # Create bounded thread pool executor based on CPU cores
    max_workers = min(
        int(os.getenv("RAG_THREAD_POOL_SIZE", str(os.cpu_count()))), 8
    )  # Cap at 8
    app.state.thread_pool = ThreadPoolExecutor(
        max_workers=max_workers, thread_name_prefix="rag-worker"
    )
    logger.info(
        f"Initialized thread pool with {max_workers} workers (CPU cores: {os.cpu_count()})"
    )

    if VECTOR_DB_TYPE == VectorDBType.PGVECTOR:
        await PSQLDatabase.get_pool()  # Initialize the pool
        await ensure_vector_indexes()

    yield

    # Cleanup logic
    logger.info("Shutting down thread pool")
    app.state.thread_pool.shutdown(wait=True)
    logger.info("Thread pool shutdown complete")


app = FastAPI(lifespan=lifespan, debug=debug_mode)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(LogMiddleware)

app.middleware("http")(security_middleware)

# Set state variables for use in routes
app.state.CHUNK_SIZE = CHUNK_SIZE
app.state.CHUNK_OVERLAP = CHUNK_OVERLAP
app.state.PDF_EXTRACT_IMAGES = PDF_EXTRACT_IMAGES

# Include routers
app.include_router(document_routes.router)
if debug_mode:
    app.include_router(router=pgvector_routes.router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    body = await request.body()
    logger.debug(f"Validation error occurred")
    logger.debug(f"Raw request body: {body.decode()}")
    logger.debug(f"Validation errors: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
            "body": body.decode(),
            "message": "Request validation failed",
        },
    )


if __name__ == "__main__":
    uvicorn.run(app, host=RAG_HOST, port=RAG_PORT, log_config=None)
