"""
Módulo principal da aplicação FastAPI para REST Countries API.

Este módulo contém a configuração da aplicação FastAPI, incluindo
definição de schemas, rotas de saúde, middleware e integração de todas as rotas.
"""

import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field

from app.api.country_routes import router as country_router


class HealthCheckResponse(BaseModel):
    """Schema de resposta para o healthcheck da aplicação.

    Attributes:
        status: Indicador de status operacional da aplicação.
        version: Versão da API.
        timestamp: Timestamp do servidor em formato ISO 8601 UTC.
    """

    status: str = Field(
        ...,
        description="Status operacional da aplicação",
    )
    version: str = Field(
        ...,
        description="Versão da API",
    )
    timestamp: str = Field(
        ...,
        description="Timestamp do servidor em formato ISO 8601 UTC",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "ok",
                "version": "1.0.0",
                "timestamp": "2026-09-14T10:30:00+00:00",
            }
        }
    )


app = FastAPI(
    title="REST Countries API",
    description="API RESTful para ingestão e consulta de dados de países",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS: origens permitidas via variável de ambiente (lista separada por vírgula).
# Default cobre os servidores de desenvolvimento local (FastAPI e futura dashboard Streamlit).
_default_origins = "http://localhost:8000,http://localhost:8501,http://127.0.0.1:8000,http://127.0.0.1:8501"
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", _default_origins).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rotas de país
app.include_router(country_router)


@app.get(
    "/health",
    response_model=HealthCheckResponse,
    tags=["Health"],
    summary="Verificação de saúde da aplicação",
    description="Retorna o status operacional, versão e timestamp do servidor",
    status_code=200,
)
def health_check() -> HealthCheckResponse:
    """Verificação de saúde do serviço.

    Retorna informações de status operacional da aplicação,
    versão e timestamp atual do servidor em formato ISO 8601 UTC.
    Utilizado por orquestradores como Kubernetes e Docker para
    validar a disponibilidade da aplicação.

    Returns:
        HealthCheckResponse: Objeto contendo status, versão e timestamp.

    Example:
        >>> response = GET /health
        >>> response.json()
        {
            "status": "ok",
            "version": "1.0.0",
            "timestamp": "2026-09-14T10:30:00+00:00"
        }
    """
    return HealthCheckResponse(
        status="ok",
        version="1.0.0",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.get("/", tags=["Root"], summary="Endpoint raiz")
def root() -> dict[str, str]:
    """Endpoint raiz da API.

    Returns:
        dict[str, str]: Mensagem de boas-vindas.
    """
    return {"message": "REST Countries API - v1.0.0"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
