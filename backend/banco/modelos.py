"""Define as tabelas do banco local usadas pelo BotShopee."""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .conexao import Base


class StatusVideo(str, enum.Enum):
    """Estados possíveis de processamento do vídeo."""

    PENDENTE = "pendente"
    PROCESSANDO = "processando"
    ENVIADO = "enviado"
    ERRO = "erro"


class Video(Base):
    """Registro persistido para cada vídeo recebido pelo painel web."""

    __tablename__ = "videos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    link_original: Mapped[str] = mapped_column(String(2048), nullable=False)
    link_shopee: Mapped[str] = mapped_column(String(2048), nullable=False)
    nome_produto: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    preco_produto: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    caminho_video_processado: Mapped[str] = mapped_column(String(1024), nullable=False, default="")
    canal_destino: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[StatusVideo] = mapped_column(
        SAEnum(StatusVideo, native_enum=False, length=20),
        nullable=False,
        default=StatusVideo.PENDENTE,
    )
    mensagem_erro: Mapped[str] = mapped_column(Text, nullable=False, default="")
    criado_em: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
