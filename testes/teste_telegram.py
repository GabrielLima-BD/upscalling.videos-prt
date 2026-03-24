"""Testes do envio assíncrono para o Telegram."""

from __future__ import annotations

from asyncio import run
from pathlib import Path
from unittest.mock import AsyncMock

from backend.servicos import envio_telegram as modulo


class _BotFalso:
    ultima_instancia = None

    def __init__(self, token: str) -> None:
        self.token = token
        self.send_document = AsyncMock()
        _BotFalso.ultima_instancia = self


def test_enviar_video_seleciona_canal_um(monkeypatch, tmp_path):
    """Confirma que o canal 1 é usado quando o parâmetro aponta para esse destino."""

    arquivo = tmp_path / "video.mp4"
    arquivo.write_bytes(b"conteudo falso")

    monkeypatch.setattr(modulo, "TOKEN_TELEGRAM_MARLI", "token-marli")
    monkeypatch.setattr(modulo, "TOKEN_TELEGRAM_GABRIEL", "token-gabriel")
    monkeypatch.setattr(modulo, "ID_GRUPO_MARLI", -100111)
    monkeypatch.setattr(modulo, "ID_GRUPO_GABRIEL", -100222)
    monkeypatch.setattr(modulo, "Bot", _BotFalso)

    resultado = run(modulo.enviar_video(arquivo, "Produto", "R$ 10,00", "https://shopee.com.br/a", 1))

    assert resultado is True
    assert _BotFalso.ultima_instancia is not None
    assert _BotFalso.ultima_instancia.send_document.await_args.kwargs["chat_id"] == -100111


def test_enviar_video_seleciona_canal_dois(monkeypatch, tmp_path):
    """Confirma que o canal 2 é usado quando o parâmetro aponta para esse destino."""

    arquivo = tmp_path / "video.mp4"
    arquivo.write_bytes(b"conteudo falso")

    monkeypatch.setattr(modulo, "TOKEN_TELEGRAM_MARLI", "token-marli")
    monkeypatch.setattr(modulo, "TOKEN_TELEGRAM_GABRIEL", "token-gabriel")
    monkeypatch.setattr(modulo, "ID_GRUPO_MARLI", -100111)
    monkeypatch.setattr(modulo, "ID_GRUPO_GABRIEL", -100222)
    monkeypatch.setattr(modulo, "Bot", _BotFalso)

    resultado = run(modulo.enviar_video(arquivo, "Produto", "R$ 10,00", "https://shopee.com.br/a", 2))

    assert resultado is True
    assert _BotFalso.ultima_instancia is not None
    assert _BotFalso.ultima_instancia.send_document.await_args.kwargs["chat_id"] == -100222
