"""Testes da extração de dados do produto na Shopee."""

from __future__ import annotations

from types import SimpleNamespace

import httpx

from backend.servicos import scraping_shopee as modulo


def test_extrair_dados_produto_com_html_mockado(monkeypatch):
    """Valida a leitura de nome e preço quando a página responde corretamente."""

    html = """
    <html>
      <head>
        <meta property="og:title" content="Fone Bluetooth Premium">
        <meta property="product:price:amount" content="129.90">
      </head>
      <body><h1>Fone Bluetooth Premium</h1></body>
    </html>
    """

    resposta = SimpleNamespace(text=html, raise_for_status=lambda: None)
    monkeypatch.setattr(modulo.httpx, "get", lambda *args, **kwargs: resposta)

    dados = modulo.extrair_dados_produto("https://shopee.com.br/produto")

    assert dados["nome"] == "Fone Bluetooth Premium"
    assert dados["preco"] == "129.90"
    assert dados["url"] == "https://shopee.com.br/produto"


def test_extrair_dados_produto_faz_fallback_quando_falha(monkeypatch):
    """Garante que erros de scraping não interrompem o fluxo principal."""

    def _falhar(*args, **kwargs):
        raise httpx.RequestError("erro simulado")

    monkeypatch.setattr(modulo.httpx, "get", _falhar)

    dados = modulo.extrair_dados_produto("https://shopee.com.br/produto")

    assert dados == {
        "nome": "Produto Shopee",
        "preco": "",
        "url": "https://shopee.com.br/produto",
    }
