import psycopg
from psycopg.rows import dict_row


def criar_conexao(database_url: str) -> psycopg.Connection:
    """
    Conexão com Postgres.
    Use autocommit=False (default) — o commit é feito explicitamente no inserter
    para agrupar páginas em uma transação só.
    """
    return psycopg.connect(
        database_url,
        row_factory=dict_row,
        autocommit=False,
    )