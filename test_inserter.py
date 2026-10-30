"""
Script de teste do inserir_pagina.
Roda fora do fluxo do scraping, só pra validar a camada db/inserter.py.

Uso:
    python test_inserter.py

Pré-requisitos:
    - Postgres rodando (docker compose up -d)
    - Schema já aplicado (npx prisma db push do projeto NestJS)
    - Pelo menos 1 usuário admin no banco (do seed)
    - .env com DATABASE_URL configurada
"""

import os
from uuid import uuid4

from dotenv import load_dotenv

from db.connection import criar_conexao
from db.inserter import contar_questoes, inserir_pagina

load_dotenv()


def montar_questao_1(admin_id: str) -> dict:
    """
    Questão 'completa' — todos os campos preenchidos, simulando o que
    o scraping real produz depois do normalizer.
    """
    return {
        "id": str(uuid4()),
        "idExterno": "teste-completa-001",
        "enunciado": "Qual é o ciclo biogeoquímico mais importante?",
        "segundoEnunciado": None,
        "textoAssociado": [
            "Os ciclos biogeoquímicos são processos que ocorrem na natureza "
            "para garantir a reciclagem de elementos químicos no meio. São esses "
            "ciclos que possibilitam que os elementos interajam com o meio ambiente "
            "e com os seres vivos."
        ],
        "alternativas": [
            {"chave": "A", "texto": "Ciclo do carbono"},
            {"chave": "B", "texto": "Ciclo do nitrogênio"},
            {"chave": "C", "texto": "Ciclo da água"},
            {"chave": "D", "texto": "Ciclo do oxigênio"},
        ],
        "respostaCorreta": "A",
        "tipo": "multipla_escolha",
        "dificuldade": "media",
        "bancaId": None,      # deixa None pra testar nullable
        "orgaoId": None,
        "prova": "Agente de Polícia",
        "ano": 2022,
        "imagens": [
            "https://provedor/exemplo-01.png",
            "https://provedor/exemplo-02.png",
        ],
        "explicacao": "",
        "origem": "importada",
        "statusValidacao": "aprovada",
        "criadoPor": admin_id,
        "taxonomias": [],     # sem taxonomias pra simplificar o teste
    }


def montar_questao_2(admin_id: str) -> dict:
    """
    Questão 'mínima' — só os campos obrigatórios.
    Testa como o inserter lida com NULLs em tudo que é opcional.
    """
    return {
        "id": str(uuid4()),
        "idExterno": "teste-minima-002",
        "enunciado": "Assinale a alternativa correta sobre a Constituição de 1988.",
        "segundoEnunciado": None,
        "textoAssociado": None,
        "alternativas": [
            {"chave": "A", "texto": "É a primeira constituição brasileira."},
            {"chave": "B", "texto": "Foi promulgada em 1988 e é a vigente."},
            {"chave": "C", "texto": "Foi outorgada por um imperador."},
        ],
        "respostaCorreta": "B",
        "tipo": "multipla_escolha",
        "dificuldade": "facil",
        "bancaId": None,
        "orgaoId": None,
        "prova": None,
        "ano": None,
        "imagens": None,
        "explicacao": "",
        "origem": "importada",
        "statusValidacao": "aprovada",
        "criadoPor": admin_id,
        "taxonomias": [],
    }


def consultar_questao(conn, id_externo: str) -> dict | None:
    """Busca a questão pelo id_externo e devolve o registro completo."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, id_externo, enunciado, alternativas, resposta_correta,
                   tipo, dificuldade, texto_associado, imagens, prova, ano,
                   origem, status_validacao, criado_por, criado_em
            FROM questoes
            WHERE id_externo = %s
            """,
            (id_externo,),
        )
        return cur.fetchone()


def main():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL não configurada no .env")

    print("🔌 Conectando ao banco...")
    conn = criar_conexao(database_url)

    try:
        admin_id = "923661f1-d5fc-4495-95e2-96d65c48977f"
        print(f"👤 Admin usado como criado_por: {admin_id}")

        total_antes = contar_questoes(conn)
        print(f"📊 Total de questões antes: {total_antes}\n")

        # ============================================================
        # PRIMEIRA INSERÇÃO
        # ============================================================
        print("=" * 60)
        print("RODADA 1 — Inserindo 2 questões de teste")
        print("=" * 60)

        q1 = montar_questao_1(admin_id)
        q2 = montar_questao_2(admin_id)

        contadores = inserir_pagina(conn, [q1, q2])
        conn.commit()

        print(f"  ✓ Inseridas:  {contadores['inseridas']}")
        print(f"  ↷ Ignoradas:  {contadores['ignoradas']}")
        print(f"  ✗ Erros:      {contadores['erros']}\n")

        # ============================================================
        # CONSULTA — confirma que gravou certo
        # ============================================================
        print("=" * 60)
        print("CONSULTA — verificando o que foi gravado")
        print("=" * 60)

        for id_ext in ["teste-completa-001", "teste-minima-002"]:
            row = consultar_questao(conn, id_ext)
            if not row:
                print(f"  ✗ {id_ext}: NÃO ENCONTRADA")
                continue

            print(f"\n  ✓ {id_ext}:")
            print(f"      id (banco):       {row['id']}")
            print(f"      enunciado:        {row['enunciado'][:60]}...")
            print(f"      tipo:             {row['tipo']}")
            print(f"      dificuldade:      {row['dificuldade']}")
            print(f"      resposta_correta: {row['resposta_correta']}")
            print(f"      ano:              {row['ano']}")
            print(f"      prova:            {row['prova']}")
            print(f"      alternativas:     {len(row['alternativas'])} itens")
            print(f"      texto_associado:  {row['texto_associado']}")
            print(f"      imagens:          {row['imagens']}")
            print(f"      status_validacao: {row['status_validacao']}")

        # ============================================================
        # SEGUNDA INSERÇÃO — idempotência
        # ============================================================
        print("\n" + "=" * 60)
        print("RODADA 2 — Mesmas questões de novo (teste de ON CONFLICT)")
        print("=" * 60)

        # Regenera o dict com novos UUIDs de `id` (mas mesmo idExterno)
        # pra provar que o idExterno é quem controla a idempotência.
        q1_dup = montar_questao_1(admin_id)
        q2_dup = montar_questao_2(admin_id)

        contadores2 = inserir_pagina(conn, [q1_dup, q2_dup])
        conn.commit()

        print(f"  ✓ Inseridas:  {contadores2['inseridas']}  (esperado: 0)")
        print(f"  ↷ Ignoradas:  {contadores2['ignoradas']}  (esperado: 2)")
        print(f"  ✗ Erros:      {contadores2['erros']}  (esperado: 0)\n")

        # ============================================================
        # CONTAGEM FINAL
        # ============================================================
        total_depois = contar_questoes(conn)
        print("=" * 60)
        print(f"📊 Total de questões depois: {total_depois}")
        print(f"   Diferença: +{total_depois - total_antes} (esperado: +2)")
        print("=" * 60)

        # Veredito
        if total_depois - total_antes == 2 and contadores2["inseridas"] == 0:
            print("\n✅ TESTE PASSOU — INSERT e ON CONFLICT funcionando")
        else:
            print("\n❌ TESTE FALHOU — verifique os números acima")

    finally:
        conn.close()


if __name__ == "__main__":
    main()