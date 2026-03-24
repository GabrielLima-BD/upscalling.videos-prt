"""Envia o vídeo processado para um canal do Telegram usando a API assíncrona."""

from __future__ import annotations

from pathlib import Path

from loguru import logger
from telegram import Bot

from backend.config import (
    ID_GRUPO_GABRIEL,
    ID_GRUPO_MARLI,
    TIMEOUT_TELEGRAM_ENVIO,
    TOKEN_TELEGRAM_GABRIEL,
    TOKEN_TELEGRAM_MARLI,
)


def _obter_configuracao_canal(canal: int) -> tuple[str, int] | None:
    """Seleciona o token e o grupo corretos para o canal escolhido no painel."""

    if canal == 1:
        if not TOKEN_TELEGRAM_MARLI or not ID_GRUPO_MARLI:
            return None
        return TOKEN_TELEGRAM_MARLI, ID_GRUPO_MARLI

    if canal == 2:
        if not TOKEN_TELEGRAM_GABRIEL or not ID_GRUPO_GABRIEL:
            return None
        return TOKEN_TELEGRAM_GABRIEL, ID_GRUPO_GABRIEL

    return None


async def enviar_video(
    caminho_video: Path,
    nome_produto: str,
    preco: str,
    link_shopee: str,
    canal: int,
) -> bool:
    """Publica o arquivo de vídeo com legenda formatada no canal escolhido."""

    try:
        configuracao = _obter_configuracao_canal(canal)
        if configuracao is None:
            logger.error("Token ou ID do grupo não configurado para o canal {}", canal)
            return False

        token_bot, destino = configuracao

        legenda = f"🛍️ {nome_produto}\n💰 {preco}\n🔗 {link_shopee}"
        logger.info("Enviando vídeo para o canal {}", canal)

        bot = Bot(token=token_bot)
        with caminho_video.open("rb") as arquivo_video:
            await bot.send_document(
                chat_id=destino,
                document=arquivo_video,
                caption=legenda,
                read_timeout=TIMEOUT_TELEGRAM_ENVIO,
                write_timeout=TIMEOUT_TELEGRAM_ENVIO,
                connect_timeout=TIMEOUT_TELEGRAM_ENVIO,
                pool_timeout=TIMEOUT_TELEGRAM_ENVIO,
            )

        logger.info("Vídeo enviado com sucesso para o canal {}", canal)
        return True
    except Exception as erro:  # noqa: BLE001
        logger.exception("Falha ao enviar o vídeo pelo Telegram: {}", erro)
        return False
