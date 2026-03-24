"""Extrai dados públicos do produto da Shopee sem interromper o fluxo principal."""

from __future__ import annotations

import re

import httpx
from bs4 import BeautifulSoup
from loguru import logger

from backend.config import TIMEOUT_SCRAPING_SHOPEE


def _extrair_texto_nome(sopa: BeautifulSoup) -> str:
    """Busca o nome do produto em metadados e títulos da página."""

    seletores = [
        'meta[property="og:title"]',
        'meta[name="twitter:title"]',
        "h1",
        "title",
    ]
    for seletor in seletores:
        elemento = sopa.select_one(seletor)
        if not elemento:
            continue
        if elemento.name == "meta":
            conteudo = elemento.get("content", "").strip()
        else:
            conteudo = elemento.get_text(strip=True)
        if conteudo:
            return conteudo
    return ""


def _extrair_texto_preco(sopa: BeautifulSoup) -> str:
    """Busca um preço legível em metadados ou no conteúdo textual da página."""

    metadados = [
        'meta[property="product:price:amount"]',
        'meta[property="og:price:amount"]',
        'meta[itemprop="price"]',
    ]
    for seletor in metadados:
        elemento = sopa.select_one(seletor)
        if elemento:
            conteudo = elemento.get("content", "").strip()
            if conteudo:
                return conteudo

    texto_completo = sopa.get_text(" ", strip=True)
    correspondencia = re.search(r"R\$\s*[\d\.,]+", texto_completo)
    if correspondencia:
        return correspondencia.group(0)

    return ""


def extrair_dados_produto(url: str) -> dict[str, str]:
    """Tenta extrair nome e preço do produto e, se falhar, retorna valores seguros."""

    dados_padrao = {"nome": "Produto", "preco": "", "url": url}

    try:
        logger.info("Iniciando scraping do produto: {}", url)
        resposta = httpx.get(
            url,
            timeout=httpx.Timeout(TIMEOUT_SCRAPING_SHOPEE, connect=TIMEOUT_SCRAPING_SHOPEE),
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 UpscallingVideos/1.0"},
        )
        resposta.raise_for_status()

        sopa = BeautifulSoup(resposta.text, "html.parser")
        nome = _extrair_texto_nome(sopa) or dados_padrao["nome"]
        preco = _extrair_texto_preco(sopa)

        logger.info("Scraping concluído: nome='{}' preco='{}'", nome, preco)
        return {"nome": nome, "preco": preco, "url": url}
    except Exception as erro:  # noqa: BLE001
        logger.exception("Falha ao extrair dados do produto: {}", erro)
        return dados_padrao
