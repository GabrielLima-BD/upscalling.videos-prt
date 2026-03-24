# BotShopee

![Python](https://img.shields.io/badge/Python-3.12%2B-blue)
![Licença](https://img.shields.io/badge/Licença-MIT-green)
![Status](https://img.shields.io/badge/Status-Em%20desenvolvimento-yellow)

BotShopee é um projeto local em Python que automatiza a preparação de vídeos para envio ao Telegram a partir de um link de vídeo e de um link de produto da Shopee. O fluxo foi pensado para funcionar inteiramente no computador do usuário, com backend FastAPI, banco SQLite e interface web servida pelo próprio servidor local.

A aplicação baixa o vídeo, aplica um processamento padronizado com FFmpeg, tenta extrair nome e preço do produto e publica o resultado em um canal do Telegram. O painel também mantém um histórico visual dos envios, permitindo acompanhar status, erros e remoções com poucos cliques.

> imagem em breve

## Tecnologias

- FastAPI: expõe a API local e serve o frontend.
- Uvicorn: executa o servidor ASGI.
- SQLAlchemy: persistência local com SQLite.
- Pydantic: validação dos dados recebidos e enviados.
- python-decouple: leitura de variáveis sensíveis do arquivo .env.
- loguru: logs estruturados e legíveis.
- httpx: requisições HTTP para o scraping.
- BeautifulSoup4: leitura do HTML do produto.
- yt-dlp: download do vídeo a partir do link informado.
- ffmpeg-python: reencodificação e otimização do vídeo.
- python-telegram-bot: envio assíncrono do arquivo para o Telegram.
- pytest e pytest-asyncio: testes automatizados.

## Como rodar

1. Clone o repositório.
2. Crie e ative um ambiente virtual.
3. Instale as dependências:

   ```bash
   pip install -r requirements.txt
   ```

4. Copie o arquivo .env.exemplo para .env e preencha os valores.
5. Inicie a aplicação:

   ```bash
   python backend/principal.py
   ```

6. Abra o navegador em http://localhost:8000, caso ele não abra automaticamente.

## Estrutura do projeto

```text
botshopee/
├── backend/
│   ├── __init__.py
│   ├── principal.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── rotas_videos.py
│   │   └── rotas_status.py
│   ├── servicos/
│   │   ├── __init__.py
│   │   ├── processador_video.py
│   │   ├── scraping_shopee.py
│   │   └── envio_telegram.py
│   ├── banco/
│   │   ├── __init__.py
│   │   ├── conexao.py
│   │   └── modelos.py
│   ├── esquemas/
│   │   ├── __init__.py
│   │   └── video.py
│   └── config.py
├── frontend/
│   ├── index.html
│   ├── css/
│   │   └── estilos.css
│   └── js/
│       └── painel.js
├── videos/
│   ├── originais/
│   └── processados/
├── testes/
│   ├── __init__.py
│   ├── teste_processador.py
│   ├── teste_scraping.py
│   └── teste_telegram.py
├── .env.exemplo
├── .gitignore
├── requirements.txt
└── README.md
```

## Como contribuir

1. Crie uma branch para a sua alteração.
2. Faça as mudanças seguindo o padrão de nomes e comentários em português.
3. Garanta que os testes continuem passando.
4. Abra um pull request com uma descrição clara do que foi alterado.

## Licença

Projeto distribuído sob a licença MIT.
