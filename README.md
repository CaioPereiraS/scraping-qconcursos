# QConcursos Scraper

## ✨ **Descrição do Projeto**

O **QConcursos Scraper** é um bot de raspagem de dados (scraping) desenvolvido em Python que utiliza principalmente as bibliotecas **BeautifulSoup** e **Selenium**. O objetivo do projeto é acessar o site do QConcursos e extrair informações de questões de provas de forma automatizada. Esse projeto é útil para quem deseja reunir dados para análises, estudos ou integrações com outras aplicações.

O bot realiza o scraping de forma precisa e controlada, respeitando as regras de segurança e acessibilidade da página. O uso do Selenium permite navegar de forma programática pelas páginas e realizar a interação com elementos dinâmicos, enquanto o BeautifulSoup é usado para extrair o conteúdo HTML de forma eficiente.

---

## 🔧 **Requisitos Técnicos**

Para que o QConcursos Scraper funcione corretamente, é necessário configurar algumas dependências essenciais. Veja abaixo como configurar seu ambiente.

### 1. **Configurar o ChromeDriver**

O Selenium utiliza o **ChromeDriver** para interagir com o navegador Google Chrome. Para configurá-lo corretamente, siga os passos abaixo:

1. **Verifique a versão do Google Chrome instalada**

   - Abra o Chrome e digite `chrome://settings/help` na barra de endereço.
   - Anote a versão do Chrome instalada.
2. **Baixe o ChromeDriver compatível**

   - Acesse o site [https://chromedriver.chromium.org/downloads](https://chromedriver.chromium.org/downloads).
   - ou [https://googlechromelabs.github.io/chrome-for-testing/](https://googlechromelabs.github.io/chrome-for-testing/)
   - Baixe a versão correspondente ao seu Google Chrome.
3. **Configure o caminho do ChromeDriver**

   - Extraia o arquivo baixado.
   - Adicione o caminho do ChromeDriver ao seu PATH ou configure diretamente no arquivo `.env`.

> **Nota:** É recomendável manter o ChromeDriver em uma pasta de fácil acesso, como `C:/drivers` (Windows) ou `/usr/local/bin/` (Linux).

---

### 2. **Configurar Variáveis de Ambiente**

No arquivo `.env`, serão definidas as variáveis de ambiente necessárias para o funcionamento correto do bot. As variáveis de ambiente garantem a segurança e a flexibilidade da aplicação.

Exemplo de um arquivo `.env`:

```
QC_EMAIL_ENV=seu_email@exemplo.com
QC_EMAIL_PASS=sua_senha
AWS_REGION_NAME=us-east-1
AWS_ACCESS_KEY_ID=sua_chave_de_acesso
AWS_SECRET_ACCESS_KEY=sua_chave_secreta
```

> **Atenção:** Nunca compartilhe as variáveis de ambiente publicamente, especialmente as chaves de acesso AWS e senhas.

---

### 3. **Configurar o Docker**

O projeto possui suporte para **Docker**. Isso facilita a execução do bot de forma isolada e sem dependências externas complexas.

- Um arquivo `Dockerfile` é fornecido no repositório para que você possa criar uma instância de execução de forma simples.
- Caso não tenha o **AWS DynamoDB** configurado no servidor de produção, você pode utilizar o arquivo Docker para criar uma instância local do DynamoDB para testes.

> **Comando para subir a instância local do DynamoDB:**

```
docker-compose up -d
```

---

## 📚 **Configuração do Ambiente Python**

Para que o bot funcione, é necessário configurar o ambiente Python. Siga os passos abaixo:

1. **Crie um ambiente virtual**

   ```bash
   python -m venv venv
   ```
2. **Ative o ambiente virtual**

   - **Windows**: `venv\Scripts\activate`
   - **Linux/MacOS**: `source venv/bin/activate`
3. **Instale as dependências**

   ```bash
   pip install -r requirements.txt
   ```

> O arquivo `requirements.txt` contém todas as bibliotecas necessárias para a execução do projeto, incluindo BeautifulSoup, Selenium, boto3, entre outras.

---

## 🔓 **Autenticação e Filtros no QConcursos**

Para que o bot funcione corretamente, o usuário precisa seguir algumas regras de navegação e acesso ao site QConcursos:

1. **Aplicar o Filtro de Busca Manualmente**
   - Antes de executar o bot, é preciso ter feito login manualmente no QConcursos e feito um filtro PELO MENOS UMA VEZ.
   - Acesse o QConcursos e aplique os filtros desejados para a extração de questões.
   - O bot utilizará automaticamente o último filtro aplicado. Caso contrário, o bot pode falhar.
3. **Evite Crashs**
   - Se o filtro de questões não estiver definido corretamente, o bot pode falhar ou parar inesperadamente.

---

## ℹ️ **Outras Informações Relevantes**

- O bot é configurado para utilizar o DynamoDB, sendo necessário ter a instância ativa localmente (via Docker) ou em um servidor AWS.
- Certifique-se de que o Google Chrome esteja atualizado e compatível com o ChromeDriver.
- Evite fazer requisições em excesso para o QConcursos para evitar ser bloqueado.
- Não compartilhe suas variáveis de ambiente e credenciais AWS em repositórios públicos.

---

Se precisar de mais detalhes ou uma seção mais específica, é só avisar! 🚀
