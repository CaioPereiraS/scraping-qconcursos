
import uuid
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import WebDriverException
from bs4 import BeautifulSoup
from time import sleep
from dynamodb_tools import conectar_dynamodb, inserir_questao, contar_linhas_tabela
import os
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
from colorama import Fore, Style, init

# Carrega as variaveis do .env
load_dotenv()

# Inicializa o colorama para suportar cores no console
init(autoreset=True)

ano_global = ''
banca_global=''
orgao_global=''
prova_global=''
enunciado_global=''
segundo_enunciado_global=''
texto_associado_global=''
imagens_global=[]
alternativas_global= []
disciplina_global=''
assuntos_global=[]

dynamodb = None

def criar_questao(ano, banca, orgao, prova, enunciado, segundo_enunciado, texto_associado, imagem, alternativas, disciplina, assuntos):
    questao = {
        "id": str(uuid.uuid4()),
        "ano": ano,
        "banca": banca,
        "orgao": orgao,
        "prova": prova,
        "enunciado": enunciado,
        "segundo_enunciado": segundo_enunciado,
        "texto_associado": texto_associado,
        "imagens": imagem,
        "alternativas": alternativas,
        "disciplina": disciplina,
        "assuntos": assuntos
    }
    return questao

def initialize(browser):
   print("Iniciando scraping...")
   
   email = os.getenv("QC_EMAIL_ENV")
   senha = os.getenv("QC_EMAIL_PASS")

   browser.get("https://www.qconcursos.com/conta/entrar")
   sleep(2)

   input_login = browser.find_element(By.ID, "login_email")
   input_login.send_keys(email)

   input_password = browser.find_element(By.ID, "login_password")
   input_password.send_keys(senha)

   input_submit = browser.find_element(By.NAME, "commit")
   input_submit.click()

   browser.get('https://www.qconcursos.com/questoes-de-concursos/questoes')
   sleep(1)

def selecionar_filtro(browser):
   print("Selecionando filtro...")
   btn_ultimo_filtro = browser.find_element(By.CLASS_NAME,'js-apply-last-filter-btn')
   btn_ultimo_filtro.click()
   sleep(5)
   
def definir_questoes(browser):
   sleep(3)
   print("Definindo questões...")
   lista = browser.find_element(By.CLASS_NAME, 'q-questions-list')
   lista_questoes= lista.find_elements(By.CLASS_NAME, 'q-question-item')

   for index, questao in enumerate(lista_questoes):
      alternativa_a = questao.find_element(By.CLASS_NAME, 'js-choose-alternative')
      sleep(1)
      alternativa_a.click()
      
      questao_body = questao.find_element(By.CLASS_NAME, 'q-question-body')
      try:
         mostrar_texto_associado = questao_body.find_element(By.CLASS_NAME, 'q-link')
         mostrar_texto_associado.click()
      except Exception as e:
         pass
                  
   lista_botoes_responder = browser.find_elements(By.CLASS_NAME, 'js-answer-btn')
   for index, botao_responder in enumerate(lista_botoes_responder):
      botao_responder.click()
      sleep(1)

def raspar_dados(browser):
   print("Raspando dados...")
   
   site = BeautifulSoup(browser.page_source, 'html.parser')
   
   # Pegando a lista de questões
   questoes_site = site.find_all('div', class_='js-question-item')
   for index, questao_site in enumerate(questoes_site):
      questao_info = questao_site.find('div', class_='q-question-info')
      
      # Extraindo o ano
      ano = questao_info.find('span').text.replace('Ano: ', '').strip()
      ano_global = ano

      # Extraindo a banca
      try:
        banca_span = questao_info.find_all('span')[1]
        banca = banca_span.find('a').text.strip()
        banca_global = banca
      except (Exception):
        banca_global = ""
      
      # Extraindo o órgão
      try:
        orgao_span = questao_info.find_all('span')[2]
        orgao = orgao_span.find('a').text.strip()
        orgao_global = orgao
      except (Exception):
        orgao_global = ""
           
      # Extraindo a prova
      try:
        prova_span = questao_info.find('span', class_='q-exams')
        prova = prova_span.find('a').text.strip()
        prova_global = prova
      except (Exception):
        prova_global = ""

      
      # Extraindo o enunciado da questão
      questao_body = questao_site.find('div', class_='q-question-body')
      enunciado_div = questao_body.find('div', class_='q-question-enunciation')
      processar_enunciado_e_imagem(enunciado_div)  
      
      texto_associado_container = questao_body.find('div', class_='q-question-text')
      if texto_associado_container:
         processar_texto_associado(questao_body)
      
      # Encontrar a alternativa correta
      resposta_div = questao_body.find('div', class_='q-question-buttons')
      
      # Verifica se a div com a resposta correta está presente
      resposta_span = resposta_div.find('span', class_='js-question-right-answer')
      
      # Extrair a letra da resposta correta
      if resposta_span and resposta_span.get_text(strip=True):
         alternativa_correta = resposta_span.get_text(strip=True)
      else:
         # Caso não haja texto na resposta, assumir que a correta é 'A'
         alternativa_correta = 'A'
         
      # Encontrar o fieldset que contém as alternativas
      fieldset = questao_body.find('fieldset', class_='form-group')
      
      # Extrair as alternativas
      alternativas = []
      for div in fieldset.find_all('div'):
         label = div.find('label', class_='q-radio-button js-choose-alternative')
         if label:
            letra = label.find('span', class_='q-option-item').get_text(strip=True)  # Letra da alternativa
            if letra == alternativa_correta:
               correta = True
            else:
               correta = False
            texto_alternativa = label.find('div', class_='q-item-enum js-alternative-content').get_text(strip=True)  # Texto da alternativa
            
            # Adiciona a letra e o texto da alternativa ao dicionário
            alternativas.append({
                  'texto': texto_alternativa,
                  'correta': correta
            })
      
      alternativas_global = alternativas
            
      # Extrair a disciplina (primeiro link)
      questao_cabecalho = questao_site.find('div', class_='q-question-breadcrumb')
      disciplina = questao_cabecalho.find('a', class_='q-link').get_text(strip=True)
      disciplina_global = disciplina
      

      # Extrair todos os assuntos (links subsequentes)
      assuntos = []
      for assunto in questao_cabecalho.find_all('a', class_='q-link')[1:]:  # Ignorar o primeiro link que é a disciplina
         assunto_texto = assunto.get_text(strip=True)
         assunto_texto = assunto_texto.replace(',', '').strip()
         assuntos.append(assunto_texto)
      assuntos_global = assuntos
      # Exibir os resultados
      questao = criar_questao(ano_global, banca_global, orgao_global, prova_global, enunciado_global, segundo_enunciado_global,texto_associado_global, imagens_global, alternativas_global, disciplina_global, assuntos_global)
      inserir_questao(dynamodb, questao,"Questoes_qconcursos")

def processar_enunciado_e_imagem(enunciado_div):
    # Inicializa variáveis
    enunciado_texto_1 = []
    enunciado_texto_2 = []
    imagens = []

    encontrou_imagem = False

    # Itera sobre os elementos da div principal
    for elem in enunciado_div.contents:
        # Verifica se o elemento é uma imagem
        if elem.name == 'img':
            imagens.append(elem['src'])
            encontrou_imagem = True  # Marca que encontramos uma imagem
        elif elem.get_text(strip=True):  # Ignora elementos vazios
            # Se já encontrou uma imagem, o texto é colocado em enunciado_texto_2
            if encontrou_imagem:
                enunciado_texto_2.append(elem.get_text(separator=' ', strip=True))
            else:
                # Caso contrário, o texto vai para enunciado_texto_1
                enunciado_texto_1.append(elem.get_text(separator=' ', strip=True))

    # Junta os textos, se houver
    enunciado_texto_1 = ' '.join(enunciado_texto_1).strip() if enunciado_texto_1 else None
    enunciado_texto_2 = ' '.join(enunciado_texto_2).strip() if enunciado_texto_2 else None

    # Define o enunciado padrão se houver imagens, mas sem texto antes delas
    if not enunciado_texto_1 and imagens:
        enunciado_texto_1 = "Observe a(s) imagem(ns) abaixo"

    # Armazena os resultados globais, se existirem
    if enunciado_texto_1:
        global enunciado_global
        enunciado_global = enunciado_texto_1

    if enunciado_texto_2:
        global segundo_enunciado_global
        segundo_enunciado_global = enunciado_texto_2

    if imagens:
        global imagens_global
        imagens_global = imagens

def processar_texto_associado(questao_body):
    # Localizar o container do texto associado
    texto_associado_container = questao_body.find('div', class_='q-question-text')
    
    if texto_associado_container:
        # Encontrar o link que pode ser clicado para mostrar o texto
        mostrar_mais = texto_associado_container.find('a', class_='q-link')
        
        # Encontrar a div que contém o texto associado
        texto_associado_div = texto_associado_container.find('div')

        # Se a div existir, extrair todo o texto dela
        if texto_associado_div:
            # Extrair o texto de todos os elementos dentro da div
            texto_associado = texto_associado_div.get_text(separator=' ', strip=True)

            # Global para armazenar o texto associado
            global texto_associado_global
            texto_associado_global = texto_associado
            
            # Encontrar todas as imagens dentro da div associada
            imagens = texto_associado_div.find_all('img')
            imagem_urls = []
            
            # Extrair a URL de cada imagem
            for img in imagens:
                imagem_urls.append(img['src'])
            
            # Global para armazenar as URLs das imagens
            global imagens_global
            imagens_global = imagem_urls

def existe_proxima_pagina(browser):
   try:
      botao_proxima = browser.find_element(By.CLASS_NAME, 'q-next')
      botao_proxima.click()
      print("Há mais páginas disponíveis.")
      return True
   except Exception as e:
      print("Não há mais páginas disponíveis.")
      return False

# Função para lidar com erros e tentar executar novamente uma função em caso de falha
def handle_errors(browser, func, retries=3, *args, **kwargs):
    for attempt in range(retries):
        try:
            return func(browser, *args, **kwargs)  # Tenta executar a função
        except WebDriverException as e:
            print(f"Erro na tentativa {attempt + 1} ao executar {func.__name__}: {e}")
            browser.refresh()  # Atualiza a página
            sleep(2)  # Espera para garantir que a página recarregue totalmente
    print(f"Falha ao executar {func.__name__} após {retries} tentativas.")
    return None  # Retorna None se todas as tentativas falharem

def verificar_variaveis_ambiente():
    variaveis = [
        "QC_EMAIL_ENV",
        "QC_EMAIL_PASS",
        "AWS_REGION_NAME",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY"
    ]

    print(f"{Style.BRIGHT}Verificando variáveis de ambiente:\n")
    todas_configuradas = True  # Flag para checar se todas estão configuradas

    for var in variaveis:
        valor = os.getenv(var)
        if valor:
            print(f"{Fore.GREEN}✔ {var}: Configurada")
        else:
            print(f"{Fore.RED}✘ {var}: Não configurada")
            todas_configuradas = False  # Marca como False se uma estiver ausente

    # Mensagem final
    if todas_configuradas:
        print(f"\n{Fore.GREEN}Todas as variáveis estão configuradas!")
    else:
        print(f"\n{Fore.RED}Algumas variáveis não estão configuradas. Verifique o arquivo .env ou as variáveis de ambiente.")

    return todas_configuradas

def realizar_scraping():
    
    chrome_options = Options()
    chrome_options.add_experimental_option('detach', True)
    chrome_options.add_argument('window-size=1600x900')
    
    browser_ = webdriver.Chrome(options=chrome_options)
    
    #Executa as funções com handle de erro, sem modificar as funções internas
    handle_errors(browser_, initialize)
    handle_errors(browser_, selecionar_filtro)
    
    while True:
        handle_errors(browser_, definir_questoes)
        handle_errors(browser_, raspar_dados)
        
        if not handle_errors(browser_, existe_proxima_pagina):
            break
    
def inicializar_sistema():
    print("Inicializando o sistema...\n")

    # Verifica variáveis de ambiente
    print("1. Verificando variáveis de ambiente...")
    if not verificar_variaveis_ambiente():
        print(f"{Fore.RED}Erro: Variáveis de ambiente ausentes. Verifique o arquivo .env.")
        return None

    # Conecta ao DynamoDB
    print("2. Conectando ao DynamoDB...")
    dynamodb = conectar_dynamodb()
    if not dynamodb:
        print(f"{Fore.RED}Erro: Falha ao conectar ao DynamoDB.")
        return None

    print(f"{Fore.GREEN}Sistema inicializado com sucesso!")
    return dynamodb

def menu_console(dynamodb):
    while True:
        print("\n" + "=" * 30)
        print(" MENU DE OPERAÇÕES ".center(30, "="))
        print("=" * 30)
        print("1. Realizar scraping")
        print("2. Contar linhas da tabela 'questoes_enem'")
        print("3. Contar linhas da tabela 'Questoes_qconcursos'")
        print("4. Sair")
        print("=" * 30)

        escolha = input("Escolha uma opção: ")

        if escolha == "1":
            # Realizar scraping
            print(f"{Fore.GREEN}Iniciando scraping...")
            realizar_scraping()

        elif escolha == "2":
            # Contar linhas na tabela 'questoes_enem'
            print(f"{Fore.GREEN}Contando linhas na tabela 'questoes_enem'...")
            contar_linhas_tabela(dynamodb, "questoes_enem")

        elif escolha == "3":
            # Contar linhas na tabela 'Questoes_qconcursos'
            print(f"{Fore.GREEN}Contando linhas na tabela 'Questoes_qconcursos'...")
            contar_linhas_tabela(dynamodb, "Questoes_qconcursos")

        elif escolha == "4":
            # Sair do programa
            print(f"{Fore.YELLOW}Saindo do programa. Até mais!")
            break

        else:
            print(f"{Fore.RED}Opção inválida. Tente novamente.")

# Exemplo de uso
if __name__ == "__main__":
      
    dynamodb = inicializar_sistema()
    if dynamodb:
        menu_console(dynamodb)
