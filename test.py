import uvicorn
from fastapi import FastAPI
from loguru import logger

server_log = logger.bind(logger_name="Server")
server_log.info("Server started")
uvicorn.run(
    FastAPI(),
    log_level="error",
    server_header=False,
)
server_log.info("Server stopped")
