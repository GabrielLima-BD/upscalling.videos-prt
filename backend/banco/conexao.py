"""Configura o SQLite local, a sessão SQLAlchemy e a criação automática das tabelas."""

from __future__ import annotations

from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from backend.config import BASE_DIR

# Banco local armazenado junto ao executável ou na raiz do projeto para manter o app portátil.
ARQUIVO_BANCO = BASE_DIR / "botshopee.db"
ARQUIVO_BANCO.parent.mkdir(parents=True, exist_ok=True)

# URL SQLite usada por SQLAlchemy para persistência local.
URL_BANCO = f"sqlite:///{ARQUIVO_BANCO}"

# Engine com configuração compatível com SQLite em ambiente local e FastAPI.
engine = create_engine(URL_BANCO, connect_args={"check_same_thread": False})

# Fábrica de sessões utilizada tanto pelas rotas quanto pelos processos em background.
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    """Base declarativa compartilhada entre todos os modelos."""


def obter_sessao() -> Generator[Session, None, None]:
    """Disponibiliza uma sessão por requisição para uso como dependência do FastAPI."""

    sessao = SessionLocal()
    try:
        yield sessao
    finally:
        sessao.close()


def criar_tabelas() -> None:
    """Importa os modelos e cria as tabelas automaticamente na primeira execução."""

    from . import modelos  # noqa: F401

    Base.metadata.create_all(bind=engine)


criar_tabelas()
