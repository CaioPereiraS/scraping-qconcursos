from psycopg import Connection


class ResolvedorCatalogo:
    """
    Cache em memória dos catálogos (bancas, órgãos, taxonomias).
    Carrega tudo uma vez, resolve por slug em O(1).

    Estratégia de resolução:
    - banca/orgao: match exato por nome (case-insensitive) → slug
    - se não achar, cria automaticamente (auto_discover=True)
    - taxonomia: disciplina → tipo='disciplina'; assuntos → tipo='assunto' com pai=disciplina
    """

    def __init__(self, conn: Connection, auto_discover: bool = True):
        self.conn = conn
        self.auto_discover = auto_discover

        self._bancas: dict[str, str] = {}      # nome_lower → id
        self._orgaos: dict[str, str] = {}      # nome_lower → id
        self._taxonomias: dict[str, str] = {}  # slug → id

        self._carregar()

    # ============================================================
    # Carregamento inicial
    # ============================================================

    def _carregar(self) -> None:
        with self.conn.cursor() as cur:
            cur.execute("SELECT id, nome FROM bancas WHERE esta_ativo = true")
            for row in cur.fetchall():
                self._bancas[row["nome"].strip().lower()] = row["id"]

            cur.execute("SELECT id, nome FROM orgaos WHERE esta_ativo = true")
            for row in cur.fetchall():
                self._orgaos[row["nome"].strip().lower()] = row["id"]

            cur.execute("SELECT id, slug, nome, tipo FROM taxonomias WHERE esta_ativo = true")
            for row in cur.fetchall():
                self._taxonomias[row["slug"]] = row["id"]
                # também indexa por nome (fallback)
                self._taxonomias[f"nome:{row['nome'].strip().lower()}"] = row["id"]

    # ============================================================
    # Banca
    # ============================================================

    def banca_id(self, nome: str | None) -> str | None:
        if not nome or not nome.strip():
            return None
        chave = nome.strip().lower()
        if chave in self._bancas:
            return self._bancas[chave]

        if not self.auto_discover:
            return None

        # Cria banca nova
        slug = self._slugify(nome)
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO bancas (id, slug, nome, esta_ativo, criado_em, atualizado_em)
                VALUES (gen_random_uuid(), %s, %s, true, now(), now())
                ON CONFLICT (slug) DO UPDATE SET nome = EXCLUDED.nome
                RETURNING id
                """,
                (slug, nome.strip()),
            )
            novo_id = cur.fetchone()["id"]
        self._bancas[chave] = novo_id
        return novo_id

    # ============================================================
    # Órgão
    # ============================================================

    def orgao_id(self, nome: str | None) -> str | None:
        if not nome or not nome.strip():
            return None
        chave = nome.strip().lower()
        if chave in self._orgaos:
            return self._orgaos[chave]

        if not self.auto_discover:
            return None

        slug = self._slugify(nome)
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO orgaos (id, slug, nome, esta_ativo, criado_em, atualizado_em)
                VALUES (gen_random_uuid(), %s, %s, true, now(), now())
                ON CONFLICT (slug) DO UPDATE SET nome = EXCLUDED.nome
                RETURNING id
                """,
                (slug, nome.strip()),
            )
            novo_id = cur.fetchone()["id"]
        self._orgaos[chave] = novo_id
        return novo_id

    # ============================================================
    # Taxonomia
    # ============================================================

    def taxonomia_id(self, nome: str, tipo: str = "assunto", pai_id: str | None = None) -> str | None:
        if not nome or not nome.strip():
            return None

        slug = self._slugify(nome)
        if slug in self._taxonomias:
            return self._taxonomias[slug]

        if not self.auto_discover:
            return None

        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO taxonomias (id, pai_id, nome, slug, tipo, posicao, esta_ativo, criado_em, atualizado_em)
                VALUES (gen_random_uuid(), %s, %s, %s, %s, 0, true, now(), now())
                ON CONFLICT (slug) DO UPDATE SET nome = EXCLUDED.nome
                RETURNING id
                """,
                (pai_id, nome.strip(), slug, tipo),
            )
            novo_id = cur.fetchone()["id"]
        self._taxonomias[slug] = novo_id
        return novo_id

    def disciplina_id(self, nome: str) -> str | None:
        return self.taxonomia_id(nome, tipo="disciplina", pai_id=None)

    def assunto_id(self, nome: str, disciplina_id: str | None) -> str | None:
        return self.taxonomia_id(nome, tipo="assunto", pai_id=disciplina_id)

    # ============================================================
    # Helper
    # ============================================================

    @staticmethod
    def _slugify(texto: str) -> str:
        import unicodedata
        import re

        texto = unicodedata.normalize("NFKD", texto)
        texto = texto.encode("ascii", "ignore").decode("ascii")
        texto = re.sub(r"[^\w\s-]", "", texto).strip().lower()
        texto = re.sub(r"[-\s]+", "-", texto)
        return texto[:110] or "sem-slug"