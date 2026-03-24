"""Baixa vídeos com yt-dlp e aplica um processamento padronizado com FFmpeg."""

from __future__ import annotations

import contextlib
import os
import subprocess
from pathlib import Path

import ffmpeg
import yt_dlp
from loguru import logger

from backend.config import ALTURA_SAIDA_VIDEO, LARGURA_SAIDA_VIDEO, TIMEOUT_DOWNLOAD_VIDEO


@contextlib.contextmanager
def _sem_janela_console() -> None:
    """Impede a abertura de janelas de console em subprocessos no Windows."""

    if os.name != "nt":
        yield
        return

    flags_no_window = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    original_popen = subprocess.Popen

    def _popen_sem_janela(*args, **kwargs):
        kwargs["creationflags"] = kwargs.get("creationflags", 0) | flags_no_window
        startupinfo = kwargs.get("startupinfo")

        if startupinfo is None and hasattr(subprocess, "STARTUPINFO"):
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= getattr(subprocess, "STARTF_USESHOWWINDOW", 1)
            startupinfo.wShowWindow = getattr(subprocess, "SW_HIDE", 0)
            kwargs["startupinfo"] = startupinfo

        return original_popen(*args, **kwargs)

    subprocess.Popen = _popen_sem_janela
    try:
        yield
    finally:
        subprocess.Popen = original_popen


def baixar_video(link: str, destino: Path) -> Path:
    """Baixa o vídeo informado e devolve o caminho do arquivo salvo localmente."""

    try:
        destino.mkdir(parents=True, exist_ok=True)
        logger.info("Iniciando download do vídeo: {}", link)

        opcoes = {
            "outtmpl": str(destino / "%(title)s-%(id)s.%(ext)s"),
            "noplaylist": True,
            "format": "bestvideo+bestaudio/best",
            "merge_output_format": "mp4",
            "quiet": True,
            "no_warnings": True,
            # O limite alto reduz falhas em conexões lentas ou vídeos maiores.
            "socket_timeout": TIMEOUT_DOWNLOAD_VIDEO,
            "retries": 10,
            "fragment_retries": 10,
            "extractor_retries": 10,
        }

        with _sem_janela_console():
            with yt_dlp.YoutubeDL(opcoes) as baixador:
                informacoes = baixador.extract_info(link, download=True)
                caminho_final = Path(baixador.prepare_filename(informacoes))

        logger.info("Download concluído em: {}", caminho_final)
        return caminho_final
    except Exception as erro:  # noqa: BLE001
        logger.exception("Falha ao baixar o vídeo: {}", erro)
        raise


def processar_video(caminho_entrada: Path, caminho_saida: Path) -> Path:
    """Reencoda o vídeo para H.264, limita bitrate e otimiza a entrega para web."""

    try:
        if caminho_saida.suffix:
            destino_final = caminho_saida
        else:
            caminho_saida.mkdir(parents=True, exist_ok=True)
            destino_final = caminho_saida / f"{caminho_entrada.stem}_processado.mp4"

        destino_final.parent.mkdir(parents=True, exist_ok=True)
        logger.info("Iniciando processamento de vídeo: {}", caminho_entrada)
        logger.info("Arquivo de saída configurado para: {}", destino_final)

        entrada = ffmpeg.input(str(caminho_entrada))

        # A seção abaixo preserva a proporção e força a saída final exatamente em 680x1080.
        video_redimensionado = entrada.video.filter(
            "scale",
            LARGURA_SAIDA_VIDEO,
            ALTURA_SAIDA_VIDEO,
            force_original_aspect_ratio="decrease",
        )
        video_final = video_redimensionado.filter(
            "pad",
            LARGURA_SAIDA_VIDEO,
            ALTURA_SAIDA_VIDEO,
            "(ow-iw)/2",
            "(oh-ih)/2",
            color="black",
        )
        audio = entrada.audio

        comando = ffmpeg.output(
            video_final,
            audio,
            str(destino_final),
            vcodec="libx264",
            video_bitrate="2000k",
            acodec="aac",
            audio_bitrate="128k",
            pix_fmt="yuv420p",
            movflags="faststart",
            preset="medium",
        )

        with _sem_janela_console():
            ffmpeg.run(comando, overwrite_output=True, capture_stdout=True, capture_stderr=True)
        logger.info("Processamento concluído em: {}", destino_final)
        return destino_final
    except Exception as erro:  # noqa: BLE001
        logger.exception("Falha ao processar o vídeo: {}", erro)
        raise
