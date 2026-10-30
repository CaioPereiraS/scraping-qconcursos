import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


def _bool(v: str | None, default: bool = False) -> bool:
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Config:
    # QConcursos
    qc_email: str
    qc_senha: str

    # Banco
    database_url: str
    admin_user_id: str

    # Playwright
    headless: bool
    slow_mo_ms: int

    # Limites de scraping
    max_paginas_por_execucao: int


def carregar_config() -> Config:
    obrigatorias = [
        "QC_EMAIL_ENV",
        "QC_EMAIL_PASS",
        "DATABASE_URL",
        "ADMIN_USER_ID",
    ]
    faltando = [v for v in obrigatorias if not os.getenv(v)]
    if faltando:
        raise RuntimeError(
            f"Variáveis de ambiente faltando no .env: {', '.join(faltando)}"
        )

    return Config(
        qc_email=os.environ["QC_EMAIL_ENV"],
        qc_senha=os.environ["QC_EMAIL_PASS"],
        database_url=os.environ["DATABASE_URL"],
        admin_user_id=os.environ["ADMIN_USER_ID"],
        headless=_bool(os.getenv("HEADLESS"), default=False),
        slow_mo_ms=int(os.getenv("SLOW_MO_MS", "50")),
        max_paginas_por_execucao=int(os.getenv("MAX_PAGINAS", "10")),
    )