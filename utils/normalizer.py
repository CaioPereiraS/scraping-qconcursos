from uuid import uuid4


def normalizar_questao(scraped: dict, resolvedor, admin_user_id: str) -> dict | None:
    """
    Recebe o dict bruto do scraping e devolve o formato pronto pro INSERT.

    Retorna None se a questão for inválida (sem alternativas, sem correta, etc).
    """

    # ---------- enunciado ----------
    enunciado = (scraped.get("enunciado") or "").strip()
    if not enunciado:
        return None

    segundo_enunciado = (scraped.get("segundo_enunciado") or "").strip() or None

    # ---------- texto_associado: sempre lista ou None ----------
    ta = scraped.get("texto_associado") or ""
    if isinstance(ta, str):
        texto_associado = [ta.strip()] if ta.strip() else None
    elif isinstance(ta, list):
        texto_associado = [t.strip() for t in ta if t and t.strip()] or None
    else:
        texto_associado = None

    # ---------- imagens ----------
    imagens = scraped.get("imagens") or []
    if not isinstance(imagens, list):
        imagens = [imagens] if imagens else []
    imagens = [u.strip() for u in imagens if u and u.strip()] or None

    # ---------- alternativas ----------
    alternativas_raw = scraped.get("alternativas") or []
    if len(alternativas_raw) < 2:
        return None

    letras = "ABCDEFGH"
    alternativas = []
    resposta_correta = None

    for i, alt in enumerate(alternativas_raw):
        if i >= len(letras):
            break
        texto = (alt.get("texto") or "").strip()
        if not texto:
            continue
        chave = letras[i]
        alternativas.append({"chave": chave, "texto": texto})
        if alt.get("correta"):
            resposta_correta = chave

    if not alternativas or not resposta_correta:
        return None

    # ---------- tipo derivado ----------
    if len(alternativas) == 2 and {a["chave"] for a in alternativas} == {"A", "B"}:
        tipo = "certo_errado"
    else:
        tipo = "multipla_escolha"

    # ---------- catálogos ----------
    banca_id = resolvedor.banca_id(scraped.get("banca"))
    orgao_id = resolvedor.orgao_id(scraped.get("orgao"))

    disciplina = (scraped.get("disciplina") or "").strip()
    disciplina_id = resolvedor.disciplina_id(disciplina) if disciplina else None

    assuntos_ids = []
    for assunto in scraped.get("assuntos") or []:
        if not assunto:
            continue
        aid = resolvedor.assunto_id(assunto.strip(), disciplina_id)
        if aid and aid not in assuntos_ids:
            assuntos_ids.append(aid)

    # ---------- ano ----------
    try:
        ano = int(scraped.get("ano")) if scraped.get("ano") else None
    except (ValueError, TypeError):
        ano = None

    return {
        "id": str(uuid4()),
        "idExterno": scraped.get("id"),
        "enunciado": enunciado,
        "segundoEnunciado": segundo_enunciado,
        "textoAssociado": texto_associado,
        "alternativas": alternativas,
        "respostaCorreta": resposta_correta,
        "tipo": tipo,
        "dificuldade": "media",
        "bancaId": banca_id,
        "orgaoId": orgao_id,
        "prova": (scraped.get("prova") or "").strip() or None,
        "ano": ano,
        "imagens": imagens,
        "explicacao": "",
        "origem": "scraping",
        "statusValidacao": "aprovada",
        "criadoPor": admin_user_id,
        "taxonomias": assuntos_ids,
    }