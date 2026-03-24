"""Inicializa a aplicação FastAPI, serve o frontend e abre o navegador automaticamente."""

from __future__ import annotations

import sys
import threading
import webbrowser
import time
import os
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[1]))

import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger

from backend.banco.conexao import ARQUIVO_BANCO, criar_tabelas, engine
from backend.api.rotas_status import router as router_status
from backend.api.rotas_videos import router as router_videos
from backend.config import BASE_DIR, PORTA_API


def _diretorio_recursos() -> Path:
    """Localiza o diretório onde os recursos do frontend ficam disponíveis."""

    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS"))

    return Path(__file__).resolve().parents[1]


if getattr(sys, "frozen", False):
    os.chdir(BASE_DIR)

app = FastAPI(
    title="Upscalling Videos API",
    description="API local do Upscalling Videos para baixar, processar e enviar vídeos ao Telegram.",
    version="1.0.0",
)

# Os roteadores da API são registrados antes do frontend para garantir que os endpoints permaneçam acessíveis.
app.include_router(router_status)
app.include_router(router_videos)

# O frontend é servido em rotas explícitas para evitar conflitos com os endpoints da API.
PASTA_FRONTEND = _diretorio_recursos() / "frontend"
app.mount("/css", StaticFiles(directory=str(PASTA_FRONTEND / "css")), name="frontend-css")
app.mount("/js", StaticFiles(directory=str(PASTA_FRONTEND / "js")), name="frontend-js")


@app.get("/", include_in_schema=False)
def carregar_pagina_inicial() -> FileResponse:
    """Entrega o arquivo HTML principal do painel web."""

    return FileResponse(PASTA_FRONTEND / "index.html")


@app.post("/api/sistema/encerrar")
def encerrar_aplicacao() -> dict[str, str]:
    """Encerra a aplicação local após responder ao navegador."""

    def _encerrar() -> None:
        time.sleep(0.5)
        os._exit(0)

    threading.Thread(target=_encerrar, daemon=True).start()
    return {"mensagem": "Aplicação encerrada com sucesso."}


@app.on_event("startup")
def reiniciar_banco_local() -> None:
    """Inicia sempre com o histórico zerado para manter o painel como um log de sessão."""

    engine.dispose()

    sufixos = ("", "-wal", "-shm")
    for sufixo in sufixos:
        caminho = ARQUIVO_BANCO if not sufixo else ARQUIVO_BANCO.with_name(f"{ARQUIVO_BANCO.name}{sufixo}")
        if caminho.exists():
            try:
                caminho.unlink()
            except OSError as erro:
                logger.warning("Não foi possível remover o arquivo do banco {}: {}", caminho, erro)

    criar_tabelas()


@app.on_event("startup")
def abrir_navegador() -> None:
    """Abre o painel web automaticamente depois que a API subir."""

    def _abrir() -> None:
        try:
            webbrowser.open(f"http://127.0.0.1:{PORTA_API}")
        except Exception as erro:  # noqa: BLE001
            logger.warning("Não foi possível abrir o navegador automaticamente: {}", erro)

    threading.Timer(1.0, _abrir).start()


if __name__ == "__main__":
    logger.info("Subindo Upscalling Videos na porta {}", PORTA_API)
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=PORTA_API,
        reload=False,
        log_config=None,
        access_log=False,
    )
