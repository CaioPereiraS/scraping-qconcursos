import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key
import uuid
import os
from colorama import Fore, Style, init

# Inicializa o colorama para sistemas Windows
init(autoreset=True)

def conectar_dynamodb():
    region_name_os = os.getenv("AWS_REGION_NAME").replace("\n", "")
    aws_access_key_id_os = os.getenv("AWS_ACCESS_KEY_ID").replace("\n", "")
    aws_secret_access_key_os = os.getenv("AWS_SECRET_ACCESS_KEY").replace("\n", "")
    try:
        # Configura o cliente do DynamoDB local
        dynamodb = boto3.resource(
            "dynamodb",
            region_name=region_name_os,  # região  para local
            aws_access_key_id=aws_access_key_id_os,  # chave 
            aws_secret_access_key=aws_secret_access_key_os,  # chave 
        )  # chave secreta fictícia

        # Lista todas as tabelas (pode não haver nenhuma inicialmente)
        tables = list(dynamodb.tables.all())
        if not tables:
            print("Conexão bem-sucedida, mas nenhuma tabela foi encontrada.")
            return dynamodb
        if tables:
            print("Conexão bem-sucedida! Tabelas existentes:")
            for table in tables:
                print(table.table_name)
            return dynamodb
        else:
            print("Conexão bem-sucedida, mas nenhuma tabela foi encontrada.")
            return dynamodb
    except NoCredentialsError:
        print("Erro de credenciais. Verifique suas configurações.")
    except PartialCredentialsError:
        print("Credenciais incompletas fornecidas.")
    except Exception as e:
        print(f"Ocorreu um erro: {e}")

# Função para dropar todas as tabelas
def dropar_tabelas(dynamodb):
    try:
        tables = list(dynamodb.tables.all())
        for table in tables:
            table_name = table.table_name
            print(f"Dropping table: {table_name}")
            table.delete()
            table.wait_until_not_exists()
        print("Todas as tabelas foram excluídas com sucesso.")
    except ClientError as e:
        print(f"Erro ao dropar tabelas: {e}")

def criar_tabela_questoes(dynamodb=None):
    if not dynamodb:
        dynamodb = conectar_dynamodb()

    table = dynamodb.create_table(
        TableName="Questoes_qconcursos",
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],  # Partition Key
        AttributeDefinitions=[
            {"AttributeName": "id", "AttributeType": "S"},  # UUID será uma string
            {
                "AttributeName": "disciplina",
                "AttributeType": "S",  # Disciplina será uma string
            },
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "DisciplinaIndex",
                "KeySchema": [
                    {
                        "AttributeName": "disciplina",
                        "KeyType": "HASH",  # Disciplina como Partition Key no índice secundário
                    }
                ],
                "Projection": {
                    "ProjectionType": "ALL"  # Projeta todos os atributos para o índice
                },
                "ProvisionedThroughput": {
                    "ReadCapacityUnits": 5,
                    "WriteCapacityUnits": 5,
                },
            }
        ],
        ProvisionedThroughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
    )

    # Aguarda a tabela estar ativa
    table.meta.client.get_waiter("table_exists").wait(TableName="Questoes_qconcursos")
    print(f"Tabela {table.table_name} criada com sucesso.")
    return table

# Função para inserir uma questão no DynamoDB
def inserir_questao(dynamodb, questao,table_name):
    table = dynamodb.Table(table_name)

    try:
        # Inserir a questão no banco
        table.put_item(Item=questao)
        print(f"Questão inserida com sucesso. ID: {questao['id']}")
    except Exception as e:
        print(f"Erro ao inserir a questão: {str(e)}")

def retornar_questao_exemplo():
    questao = {
        "id": str(uuid.uuid4()),
        "ano": 2022,
        "banca": "CESPE",
        "orgao": "Polícia Federal",
        "prova": "Agente de Polícia",
        "enunciado": "Qual é o ciclo biogeoquímico mais importante?",
        "segundo_enunciado": "",
        "texto_associado": "Os ciclos biogeoquímicos são processos que ocorrem na natureza para garantir a reciclagem de "
        "elementos químicos no meio. São esses ciclos que possibilitam que os elementos interajam com o "
        "meio ambiente e com os seres vivos, ou seja, garantem que o elemento flua pela atmosfera, "
        "hidrosfera, litosfera e biosfera.",
        "alternativas": [
            {"texto": "Ciclo do carbono", "correta": True},
            {"texto": "Ciclo do nitrogênio", "correta": False},
            {"texto": "Ciclo da água", "correta": False},
            {"texto": "Ciclo do oxigênio", "correta": False},
        ],
        "disciplina": "Biologia",
        "assuntos": ["Ecologia", "Ciclos Biogeoquímicos"],
        "imagens": [
            "https://provedor/f47ac10b-58cc-4372-a567-0e02b2c3d479-01.png",
            "https://provedor/f47ac10b-58cc-4372-a567-0e02b2c3d479-02.png",
        ],
    }
    return questao

def contar_linhas_tabela(dynamodb, table_name):
    """
    Conta o número total de itens (linhas) em uma tabela do DynamoDB,
    considerando a paginação para contagem exata.
    """
    table = dynamodb.Table(table_name)
    total_count = 0
    last_evaluated_key = None

    try:
        while True:
            # Realiza um scan com Select='COUNT' e inclui ExclusiveStartKey somente se ela for válida
            if last_evaluated_key:
                response = table.scan(
                    Select='COUNT',
                    ExclusiveStartKey=last_evaluated_key
                )
            else:
                response = table.scan(Select='COUNT')

            total_count += response['Count']

            # Verifica se há mais dados para escanear
            last_evaluated_key = response.get('LastEvaluatedKey')
            if not last_evaluated_key:
                break  # Sai do loop se todos os dados foram escaneados

        print(f"{Fore.GREEN}A tabela '{table_name}' contém {total_count} itens.{Style.RESET_ALL}")
        return total_count
    except Exception as e:
        print(f"{Fore.RED}Erro ao contar itens da tabela '{table_name}': {e}{Style.RESET_ALL}")
        return None

def buscar_assuntos_por_disciplina(disciplina, dynamodb=None):
   
    if not dynamodb:
        dynamodb = conectar_dynamodb()

    table = dynamodb.Table("Questoes_qconcursos")

    # Consulta o índice secundário DisciplinaIndex
    response = table.query(
        IndexName="DisciplinaIndex",
        KeyConditionExpression=Key("disciplina").eq(disciplina)
    )

    # Extrai e acumula os assuntos
    assuntos = set()
    for item in response["Items"]:
        if "assuntos" in item:
            assuntos.update(item["assuntos"])  # Adiciona assuntos únicos à lista

    return list(assuntos)  # Converte o set para lista

if __name__ == "__main__":
    
    # Conectando ao DynamoDB
    dynamodb = conectar_dynamodb()
    
    print(buscar_assuntos_por_disciplina("Biologia", dynamodb))
    
    table_name = "questoes_enem"  
    #contar_linhas_tabela(dynamodb, table_name)
    
    table_name = "Questoes_qconcursos"  
    #contar_linhas_tabela(dynamodb, table_name)
    
    

