"""Testes do fluxo de download e processamento de vídeo."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from backend.servicos import processador_video as modulo


def test_baixar_video_retorna_path_valido(monkeypatch, tmp_path):
    """Verifica se o downloader devolve o caminho preparado pelo yt-dlp."""

    instancia = MagicMock()
    instancia.extract_info.return_value = {"id": "123", "title": "video-teste", "ext": "mp4"}
    instancia.prepare_filename.return_value = str(tmp_path / "video-teste-123.mp4")

    fabrica = MagicMock()
    fabrica.return_value.__enter__.return_value = instancia
    fabrica.return_value.__exit__.return_value = False
    monkeypatch.setattr(modulo.yt_dlp, "YoutubeDL", fabrica)

    resultado = modulo.baixar_video("https://exemplo.com/video.mp4", tmp_path)

    assert isinstance(resultado, Path)
    assert resultado == tmp_path / "video-teste-123.mp4"
    assert instancia.extract_info.called


def test_processar_video_chama_ffmpeg_com_parametros_corretos(monkeypatch, tmp_path):
    """Confirma se o FFmpeg recebe os parâmetros esperados para reencodar o arquivo."""

    entrada_video = MagicMock()
    entrada_audio = MagicMock()
    stream_video = MagicMock()
    entrada = MagicMock()
    entrada.video.filter.return_value = stream_video
    entrada.audio = entrada_audio

    monkeypatch.setattr(modulo.ffmpeg, "input", MagicMock(return_value=entrada))

    chamadas_output = {}
    chamadas_scale = {}
    chamadas_pad = {}

    def _filter(nome, *args, **kwargs):
        if nome == "scale":
            chamadas_scale["args"] = args
            chamadas_scale["kwargs"] = kwargs
            return MagicMock()
        if nome == "pad":
            chamadas_pad["args"] = args
            chamadas_pad["kwargs"] = kwargs
            return MagicMock()
        return MagicMock()

    entrada.video.filter.side_effect = _filter

    def _saida(*args, **kwargs):
        chamadas_output["args"] = args
        chamadas_output["kwargs"] = kwargs
        return "comando-ffmpeg"

    monkeypatch.setattr(modulo.ffmpeg, "output", _saida)
    monkeypatch.setattr(modulo.ffmpeg, "run", MagicMock())

    caminho_entrada = tmp_path / "originais" / "video.mp4"
    caminho_entrada.parent.mkdir(parents=True, exist_ok=True)
    caminho_entrada.write_text("conteudo falso", encoding="utf-8")

    caminho_saida = tmp_path / "processados"
    resultado = modulo.processar_video(caminho_entrada, caminho_saida)

    assert resultado == caminho_saida / "video_processado.mp4"
    assert chamadas_scale["args"] == (modulo.LARGURA_SAIDA_VIDEO, modulo.ALTURA_SAIDA_VIDEO)
    assert chamadas_scale["kwargs"]["force_original_aspect_ratio"] == "decrease"
    assert chamadas_pad["args"] == (
        modulo.LARGURA_SAIDA_VIDEO,
        modulo.ALTURA_SAIDA_VIDEO,
        "(ow-iw)/2",
        "(oh-ih)/2",
    )
    assert chamadas_pad["kwargs"]["color"] == "black"
    assert chamadas_output["kwargs"]["vcodec"] == "libx264"
    assert chamadas_output["kwargs"]["video_bitrate"] == "2000k"
    assert chamadas_output["kwargs"]["movflags"] == "faststart"
    assert chamadas_output["kwargs"]["acodec"] == "aac"
    modulo.ffmpeg.run.assert_called_once()
