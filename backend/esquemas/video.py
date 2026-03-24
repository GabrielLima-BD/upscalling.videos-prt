"""Schemas Pydantic usados para validar entradas e serializar respostas da API."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class VideoEntrada(BaseModel):
    """Valida o payload enviado pelo painel web antes de iniciar o pipeline."""

    link_video: str = Field(..., min_length=5, description="Link do vídeo no formato esperado")
    link_shopee: str = Field(..., min_length=5, description="Link do produto na Shopee")
    canal_destino: int = Field(..., ge=1, le=2, description="Canal de destino, 1 ou 2")

    @field_validator("link_video", "link_shopee")
    @classmethod
    def validar_links(cls, valor: str) -> str:
        """Garante que os links recebidos estejam preenchidos e normalizados."""

        valor_limpo = valor.strip()
        if not valor_limpo.startswith(("http://", "https://")):
            raise ValueError("O link precisa começar com http:// ou https://")
        return valor_limpo


class VideosEntradaLote(BaseModel):
    """Agrupa várias entradas para envio sequencial, com limite máximo por requisição."""

    videos: list[VideoEntrada] = Field(..., min_length=1, max_length=50)


class VideoCriadoResposta(BaseModel):
    """Retorna o identificador do registro criado e o índice da linha no formulário."""

    indice: int
    id: int
    status: str


class VideoResposta(BaseModel):
    """Representa o estado completo de um vídeo para exibição no frontend."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    link_original: str
    link_shopee: str
    nome_produto: str
    preco_produto: str
    caminho_video_processado: str
    canal_destino: int
    status: str
    mensagem_erro: str
    criado_em: datetime
    atualizado_em: datetime
