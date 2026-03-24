"""Carrega as configurações sensíveis e caminhos usados pelo projeto."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from decouple import config

# Caminho base da aplicação: no EXE, aponta para a pasta do executável; no desenvolvimento, para a raiz do projeto.
BASE_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parents[1]


def _carregar_variaveis_ambiente() -> None:
	"""Carrega automaticamente o arquivo .env quando ele existir."""

	candidatos = []

	if getattr(sys, "frozen", False):
		candidatos.append(Path(getattr(sys, "_MEIPASS")) / ".env")

	candidatos.append(BASE_DIR / ".env")
	candidatos.append(Path(__file__).resolve().parents[1] / ".env")

	for arquivo_env in candidatos:
		if not arquivo_env.exists():
			continue

		with arquivo_env.open("r", encoding="utf-8") as arquivo:
			for linha in arquivo:
				linha = linha.strip()
				if not linha or linha.startswith("#") or "=" not in linha:
					continue

				chave, valor = linha.split("=", 1)
				os.environ.setdefault(chave.strip(), valor.strip())
		break


_carregar_variaveis_ambiente()

# Token do bot do Telegram usado no canal da Marli.
TOKEN_TELEGRAM_MARLI: str = config("TOKEN_TELEGRAM_MARLI", default=config("TOKEN_TELEGRAM", default=""))

# Token do bot do Telegram usado no canal do Gabriel.
TOKEN_TELEGRAM_GABRIEL: str = config("TOKEN_TELEGRAM_GABRIEL", default=config("TOKEN_TELEGRAM", default=""))

# ID do grupo da Marli, usado como destino quando o painel escolher esse canal.
ID_GRUPO_MARLI: int = config("ID_GRUPO_MARLI", default=config("ID_GRUPO_TELEGRAM", default=0), cast=int)

# ID do grupo do Gabriel, usado como destino quando o painel escolher esse canal.
ID_GRUPO_GABRIEL: int = config("ID_GRUPO_GABRIEL", default=config("ID_GRUPO_TELEGRAM_2", default=0), cast=int)

# Pasta raiz onde os vídeos originais e processados serão armazenados.
PASTA_VIDEOS: Path = BASE_DIR / "videos"

# Porta local em que a API FastAPI será executada.
PORTA_API: int = config("PORTA_API", default=8000, cast=int)

# Resolução padrão usada no processamento dos vídeos para manter o padrão vertical do painel.
LARGURA_SAIDA_VIDEO: int = config("LARGURA_SAIDA_VIDEO", default=680, cast=int)
ALTURA_SAIDA_VIDEO: int = config("ALTURA_SAIDA_VIDEO", default=1080, cast=int)

# Tempo máximo, em segundos, para as tentativas de download do vídeo via yt-dlp.
TIMEOUT_DOWNLOAD_VIDEO: int = 300

# Tempo máximo, em segundos, para a requisição HTTP usada no scraping da Shopee.
TIMEOUT_SCRAPING_SHOPEE: int = 60

# Tempo máximo, em segundos, para a comunicação com a API do Telegram ao enviar o vídeo.
TIMEOUT_TELEGRAM_ENVIO: int = 120
