"""Rotas simples de saúde da aplicação para o painel acompanhar a API."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["status"])


@router.get("/status")
def status() -> dict[str, str]:
    """Informa ao frontend que a API está ativa e qual versão está em execução."""

    return {"status": "online", "versao": "1.0.0"}
