from bs4 import BeautifulSoup

from session import SessaoQConcursos
from db.inserter import inserir_pagina
from db.connection import criar_conexao
from utils.normalizer import normalizar_questao
from utils.resolvers import ResolvedorCatalogo
from config import Config
from config import carregar_config

def extrair_questoes_da_pagina(html: str) -> list[dict]:
    """
    Extrai todas as questões do HTML da página no MESMO formato do bot antigo.
    Mantenho a lógica de BeautifulSoup porque funciona e é fácil de ajustar.
    """
    soup = BeautifulSoup(html, "html.parser")
    questoes_html = soup.find_all("div", class_="js-question-item")

    resultados = []

    for questao_site in questoes_html:
        try:
            q = _extrair_uma_questao(questao_site)
            if q:
                resultados.append(q)
        except Exception as e:
            print(f"   ⚠ Erro ao extrair questão: {e}")
            continue

    return resultados


def _extrair_uma_questao(questao_site) -> dict | None:
    questao_info = questao_site.find("div", class_="q-question-info")
    if not questao_info:
        return None

    # ano
    ano = None
    try:
        spans = questao_info.find_all("span")
        if spans:
            ano_txt = spans[0].text.replace("Ano:", "").replace("Ano", "").strip()
            ano = int(ano_txt) if ano_txt.isdigit() else None
    except Exception:
        pass

    # banca
    banca = ""
    try:
        banca_span = questao_info.find_all("span")[1]
        banca = banca_span.find("a").text.strip()
    except Exception:
        pass

    # órgão
    orgao = ""
    try:
        orgao_span = questao_info.find_all("span")[2]
        orgao = orgao_span.find("a").text.strip()
    except Exception:
        pass

    # prova
    prova = ""
    try:
        prova_span = questao_info.find("span", class_="q-exams")
        prova = prova_span.find("a").text.strip()
    except Exception:
        pass

    # corpo
    questao_body = questao_site.find("div", class_="q-question-body")
    if not questao_body:
        return None

    enunciado, segundo_enunciado, imagens_enunciado = _extrair_enunciado(questao_body)

    texto_associado = _extrair_texto_associado(questao_body)

    # alternativa correta
    alternativa_correta = "A"
    resposta_div = questao_body.find("div", class_="q-question-buttons")
    if resposta_div:
        span = resposta_div.find("span", class_="js-question-right-answer")
        if span and span.get_text(strip=True):
            alternativa_correta = span.get_text(strip=True)

    # alternativas
    alternativas = []
    fieldset = questao_body.find("fieldset", class_="form-group")
    if fieldset:
        for div in fieldset.find_all("div"):
            label = div.find("label", class_="q-radio-button js-choose-alternative")
            if not label:
                continue
            letra_span = label.find("span", class_="q-option-item")
            texto_div = label.find("div", class_="q-item-enum js-alternative-content")
            if not letra_span or not texto_div:
                continue
            letra = letra_span.get_text(strip=True)
            alternativas.append({
                "texto": texto_div.get_text(strip=True),
                "correta": letra == alternativa_correta,
            })

    if not alternativas:
        return None

    # disciplina + assuntos
    disciplina = ""
    assuntos = []
    cabecalho = questao_site.find("div", class_="q-question-breadcrumb")
    if cabecalho:
        try:
            links = cabecalho.find_all("a", class_="q-link")
            if links:
                disciplina = links[0].get_text(strip=True)
                for assunto_link in links[1:]:
                    a = assunto_link.get_text(strip=True).replace(",", "").strip()
                    if a:
                        assuntos.append(a)
        except Exception:
            pass

    return {
        "id": None,  # vai ser preenchido depois (uuid do banco é diferente do idExterno)
        "ano": ano,
        "banca": banca,
        "orgao": orgao,
        "prova": prova,
        "enunciado": enunciado,
        "segundo_enunciado": segundo_enunciado,
        "texto_associado": texto_associado,
        "imagens": imagens_enunciado,
        "alternativas": alternativas,
        "disciplina": disciplina,
        "assuntos": assuntos,
    }


def _extrair_enunciado(questao_body) -> tuple[str | None, str | None, list[str]]:
    """Espelha a lógica do `processar_enunciado_e_imagem` antigo."""
    enunciado_div = questao_body.find("div", class_="q-question-enunciation")
    if not enunciado_div:
        return None, None, []

    texto_1 = []
    texto_2 = []
    imagens = []
    encontrou_imagem = False

    for elem in enunciado_div.contents:
        if elem.name == "img":
            imagens.append(elem.get("src"))
            encontrou_imagem = True
        elif elem.get_text(strip=True):
            if encontrou_imagem:
                texto_2.append(elem.get_text(separator=" ", strip=True))
            else:
                texto_1.append(elem.get_text(separator=" ", strip=True))

    enunciado = " ".join(texto_1).strip() or None
    segundo = " ".join(texto_2).strip() or None

    if not enunciado and imagens:
        enunciado = "Observe a(s) imagem(ns) abaixo"

    return enunciado, segundo, imagens


def _extrair_texto_associado(questao_body) -> str | None:
    container = questao_body.find("div", class_="q-question-text")
    if not container:
        return None
    div = container.find("div")
    if not div:
        return None
    texto = div.get_text(separator=" ", strip=True)
    return texto or None


def executar(cfg: Config, max_paginas: int) -> None:
    print(f"🚀 Iniciando scraping (máx {max_paginas} páginas)\n")

    conn = criar_conexao(cfg.database_url)
    try:
        resolvedor = ResolvedorCatalogo(conn, auto_discover=True)

        with SessaoQConcursos(cfg) as sessao:
            sessao.login()
            sessao.ir_para_questoes()

            total_inseridas = 0
            total_ignoradas = 0
            total_erros = 0

            for pagina in range(1, max_paginas + 1):
                print(f"\n📄 Página {pagina}/{max_paginas}")

                sessao.revelar_respostas_da_pagina()

                html = sessao.page.content()
                questoes_brutas = extrair_questoes_da_pagina(html)
                print(f"   → {len(questoes_brutas)} questões extraídas")

                if not questoes_brutas:
                    print("   ⚠ Nenhuma questão extraída, parando.")
                    break

                normalizadas = []
                for bruta in questoes_brutas:
                    # id_externo precisa ser único — usa hash do enunciado se não tiver
                    if not bruta.get("id"):
                        import hashlib
                        bruta["id"] = hashlib.sha256(
                            f"{bruta.get('banca')}|{bruta.get('ano')}|{bruta.get('enunciado')}".encode()
                        ).hexdigest()[:32]

                    n = normalizar_questao(bruta, resolvedor, cfg.admin_user_id)
                    if n:
                        normalizadas.append(n)

                print(f"   → {len(normalizadas)} normalizadas")

                contadores = inserir_pagina(conn, normalizadas)
                conn.commit()

                total_inseridas += contadores["inseridas"]
                total_ignoradas += contadores["ignoradas"]
                total_erros += contadores["erros"]

                print(
                    f"   ✓ {contadores['inseridas']} inseridas, "
                    f"{contadores['ignoradas']} já existiam, "
                    f"{contadores['erros']} erros"
                )

                if not sessao.ir_para_proxima_pagina():
                    print("\n🏁 Última página atingida.")
                    break

            print(f"\n📊 Total: {total_inseridas} inseridas, "
                  f"{total_ignoradas} ignoradas, {total_erros} erros")

    finally:
        conn.close()

if __name__ == "__main__":
    cfg = carregar_config()
    executar(cfg,1)