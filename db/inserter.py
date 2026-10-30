from psycopg import Connection
from psycopg.types.json import Jsonb


def inserir_pagina(conn: Connection, questoes: list[dict]) -> dict:
    """
    Insere uma lista de questões normalizadas em uma transação.
    Cada questão é:
      - INSERT ... ON CONFLICT (id_externo) DO NOTHING na tabela `questoes`
      - INSERT em `questoes_taxonomias` pra cada taxonomia associada

    Retorna contadores: {inseridas, ignoradas, erros}
    """

    inseridas = 0
    ignoradas = 0
    erros = 0

    with conn.cursor() as cur:
        for q in questoes:
            try:
                cur.execute(
                    """
                    INSERT INTO questoes (
                        id, id_externo, enunciado, segundo_enunciado, texto_associado,
                        alternativas, resposta_correta, tipo, dificuldade,
                        banca_id, orgao_id, prova, ano,
                        imagens, explicacao, origem, status_validacao, criado_por,
                        criado_em, atualizado_em
                    ) VALUES (
                        %(id)s, %(id_externo)s, %(enunciado)s, %(segundo_enunciado)s, %(texto_associado)s,
                        %(alternativas)s, %(resposta_correta)s, %(tipo)s, %(dificuldade)s,
                        %(banca_id)s, %(orgao_id)s, %(prova)s, %(ano)s,
                        %(imagens)s, %(explicacao)s, %(origem)s, %(status_validacao)s, %(criado_por)s,
                        now(), now()
                    )
                    ON CONFLICT (id_externo) DO NOTHING
                    RETURNING id
                    """,
                    {
                        "id": q["id"],
                        "id_externo": q["idExterno"],
                        "enunciado": q["enunciado"],
                        "segundo_enunciado": q["segundoEnunciado"],
                        "texto_associado": Jsonb(q["textoAssociado"]) if q["textoAssociado"] else None,
                        "alternativas": Jsonb(q["alternativas"]),
                        "resposta_correta": q["respostaCorreta"],
                        "tipo": q["tipo"],
                        "dificuldade": q["dificuldade"],
                        "banca_id": q["bancaId"],
                        "orgao_id": q["orgaoId"],
                        "prova": q["prova"],
                        "ano": q["ano"],
                        "imagens": Jsonb(q["imagens"]) if q["imagens"] else None,
                        "explicacao": q["explicacao"],
                        "origem": q["origem"],
                        "status_validacao": q["statusValidacao"],
                        "criado_por": q["criadoPor"],
                    },
                )

                row = cur.fetchone()
                if row is None:
                    ignoradas += 1
                    continue

                questao_id_real = row["id"]

                # Inserir taxonomias
                for tax_id in q["taxonomias"]:
                    cur.execute(
                        """
                        INSERT INTO questoes_taxonomias (questao_id, taxonomia_id)
                        VALUES (%s, %s)
                        ON CONFLICT DO NOTHING
                        """,
                        (questao_id_real, tax_id),
                    )

                inseridas += 1

            except Exception as e:
                erros += 1
                print(f"   ⚠ Erro ao inserir questão id_externo={q.get('idExterno')}: {e}")
                # Não damos rollback da transação inteira — continuamos.
                # Se quiser ser mais rigoroso, dá rollback só dessa questão (savepoint).

    return {"inseridas": inseridas, "ignoradas": ignoradas, "erros": erros}


def contar_questoes(conn: Connection) -> int:
    with conn.cursor() as cur:
        cur.execute("SELECT count(*) AS total FROM questoes")
        return cur.fetchone()["total"]