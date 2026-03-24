"""Contém as rotas REST responsáveis por criar, consultar, reenviar e remover vídeos."""

from __future__ import annotations

import asyncio
import math
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from loguru import logger
from sqlalchemy.orm import Session

from backend.banco.conexao import SessionLocal, obter_sessao
from backend.banco.modelos import StatusVideo, Video
from backend.config import PASTA_VIDEOS
from backend.esquemas.video import VideoCriadoResposta, VideoEntrada, VideoResposta, VideosEntradaLote
from backend.servicos.envio_telegram import enviar_video
from backend.servicos.processador_video import baixar_video, processar_video
from backend.servicos.scraping_shopee import extrair_dados_produto

router = APIRouter(prefix="/api/videos", tags=["videos"])


def _video_para_resposta(video: Video) -> VideoResposta:
    """Converte o modelo do banco em um schema serializável para o frontend."""

    return VideoResposta.model_validate(video)


async def _executar_pipeline_video(video_id: int) -> None:
    """Executa download, processamento, scraping e envio sem bloquear a requisição original."""

    logger.info("Iniciando pipeline em background para o vídeo {}", video_id)

    with SessionLocal() as sessao:
        video = sessao.get(Video, video_id)
        if video is None:
            logger.warning("Vídeo {} não encontrado para processamento em background", video_id)
            return

        try:
            video.status = StatusVideo.PROCESSANDO
            video.mensagem_erro = ""
            video.atualizado_em = datetime.utcnow()
            sessao.commit()

            pasta_originais = PASTA_VIDEOS / "originais"
            pasta_processados = PASTA_VIDEOS / "processados"

            caminho_baixado = await asyncio.to_thread(baixar_video, video.link_original, pasta_originais)
            caminho_processado = await asyncio.to_thread(processar_video, caminho_baixado, pasta_processados)
            dados_produto = await asyncio.to_thread(extrair_dados_produto, video.link_shopee)

            video.nome_produto = dados_produto.get("nome", "Produto")
            video.preco_produto = dados_produto.get("preco", "")
            video.caminho_video_processado = str(caminho_processado)
            video.atualizado_em = datetime.utcnow()
            sessao.commit()

            envio_ok = await enviar_video(
                caminho_video=caminho_processado,
                nome_produto=video.nome_produto,
                preco=video.preco_produto,
                link_shopee=video.link_shopee,
                canal=video.canal_destino,
            )

            if envio_ok:
                video.status = StatusVideo.ENVIADO
                video.mensagem_erro = ""
                video.atualizado_em = datetime.utcnow()
                sessao.commit()
                logger.info("Vídeo {} enviado com sucesso", video_id)
            else:
                video.status = StatusVideo.ERRO
                video.mensagem_erro = "Falha ao enviar o vídeo para o Telegram."
                video.atualizado_em = datetime.utcnow()
                sessao.commit()
                logger.warning("Vídeo {} finalizado com erro de envio", video_id)

            try:
                if caminho_baixado.exists():
                    caminho_baixado.unlink()
            except OSError as erro_limpeza:
                logger.warning("Não foi possível remover o vídeo original {}: {}", caminho_baixado, erro_limpeza)
        except Exception as erro:  # noqa: BLE001
            logger.exception("Falha ao processar o vídeo {}: {}", video_id, erro)
            video.status = StatusVideo.ERRO
            video.mensagem_erro = str(erro)
            video.atualizado_em = datetime.utcnow()
            sessao.commit()


def _criar_video(sessao: Session, dados: VideoEntrada) -> Video:
    """Persiste um novo registro com os dados recebidos do painel."""

    agora = datetime.utcnow()

    video = Video(
        link_original=dados.link_video,
        link_shopee=dados.link_shopee,
        canal_destino=dados.canal_destino,
        status=StatusVideo.PENDENTE,
        nome_produto="",
        preco_produto="",
        caminho_video_processado="",
        mensagem_erro="",
        criado_em=agora,
        atualizado_em=agora,
    )
    sessao.add(video)
    sessao.commit()
    sessao.refresh(video)
    return video


def _agendar_processamento(background_tasks: BackgroundTasks, video_id: int) -> None:
    """Coloca o vídeo na fila de processamento do próprio FastAPI."""

    background_tasks.add_task(_executar_pipeline_video, video_id)


def _resposta_criacao(indice: int, video: Video) -> VideoCriadoResposta:
    """Converte o resultado de criação para o formato esperado pelo frontend."""

    return VideoCriadoResposta(indice=indice, id=video.id, status=video.status.value)


@router.post("", status_code=status.HTTP_202_ACCEPTED)
def criar_video(
    dados: VideoEntrada,
    background_tasks: BackgroundTasks,
    sessao: Session = Depends(obter_sessao),
) -> VideoCriadoResposta:
    """Cria o registro inicial do vídeo e agenda o pipeline completo em segundo plano."""

    video = _criar_video(sessao, dados)
    _agendar_processamento(background_tasks, video.id)
    logger.info("Vídeo {} registrado e pipeline agendado", video.id)

    return _resposta_criacao(0, video)


@router.post("/lote", status_code=status.HTTP_202_ACCEPTED)
def criar_videos_lote(
    dados: VideosEntradaLote,
    background_tasks: BackgroundTasks,
    sessao: Session = Depends(obter_sessao),
) -> dict[str, object]:
    """Cria até 50 vídeos de uma vez e mantém cada linha visível no painel após o envio."""

    videos_criados: list[VideoCriadoResposta] = []

    for indice, entrada in enumerate(dados.videos):
        video = _criar_video(sessao, entrada)
        _agendar_processamento(background_tasks, video.id)
        videos_criados.append(_resposta_criacao(indice, video))

    logger.info("Lote com {} vídeo(s) registrado e agendado", len(videos_criados))
    return {"itens": [video.model_dump(mode="json") for video in videos_criados], "total": len(videos_criados)}


@router.get("")
def listar_videos(
    pagina: int = 1,
    tamanho: int | None = None,
    sessao: Session = Depends(obter_sessao),
) -> dict[str, object]:
    """Retorna a listagem paginada dos vídeos já processados ou em processamento."""

    pagina = max(pagina, 1)
    total = sessao.query(Video).count()

    query = sessao.query(Video).order_by(Video.atualizado_em.desc(), Video.criado_em.desc())

    if tamanho is None or tamanho <= 0:
        videos = query.all()
        tamanho_real = total if total else 0
        total_paginas = 1 if total else 0
    else:
        tamanho_real = max(tamanho, 1)
        total_paginas = math.ceil(total / tamanho_real) if total else 0
        videos = query.offset((pagina - 1) * tamanho_real).limit(tamanho_real).all()

    return {
        "itens": [VideoResposta.model_validate(video).model_dump(mode="json") for video in videos],
        "pagina": pagina,
        "tamanho": tamanho_real,
        "total": total,
        "total_paginas": total_paginas,
    }


@router.get("/{video_id}", response_model=VideoResposta)
def obter_video(video_id: int, sessao: Session = Depends(obter_sessao)) -> VideoResposta:
    """Retorna os detalhes completos de um vídeo específico."""

    video = sessao.get(Video, video_id)
    if video is None:
        raise HTTPException(status_code=404, detail="Vídeo não encontrado")
    return VideoResposta.model_validate(video)


@router.post("/{video_id}/reprocessar", status_code=status.HTTP_202_ACCEPTED)
def reprocessar_video(
    video_id: int,
    background_tasks: BackgroundTasks,
    sessao: Session = Depends(obter_sessao),
) -> VideoCriadoResposta:
    """Permite tentar novamente apenas os itens que ficaram com erro."""

    video = sessao.get(Video, video_id)
    if video is None:
        raise HTTPException(status_code=404, detail="Vídeo não encontrado")

    if video.status != StatusVideo.ERRO:
        raise HTTPException(status_code=400, detail="Apenas vídeos com erro podem ser reenviados")

    video.status = StatusVideo.PENDENTE
    video.mensagem_erro = ""
    video.atualizado_em = datetime.utcnow()
    sessao.commit()
    sessao.refresh(video)

    _agendar_processamento(background_tasks, video.id)
    logger.info("Vídeo {} agendado novamente para processamento", video.id)
    return _resposta_criacao(0, video)


@router.delete("/{video_id}")
def deletar_video(video_id: int, sessao: Session = Depends(obter_sessao)) -> dict[str, str | int]:
    """Remove o registro e os arquivos locais associados ao vídeo selecionado."""

    video = sessao.get(Video, video_id)
    if video is None:
        raise HTTPException(status_code=404, detail="Vídeo não encontrado")

    caminho_processado = Path(video.caminho_video_processado) if video.caminho_video_processado else None
    if caminho_processado and caminho_processado.exists():
        try:
            caminho_processado.unlink()
        except OSError as erro:
            logger.warning("Não foi possível remover o arquivo processado {}: {}", caminho_processado, erro)

    sessao.delete(video)
    sessao.commit()

    return {"mensagem": "Vídeo removido com sucesso", "id": video_id}
