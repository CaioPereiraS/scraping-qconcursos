from colorama import Fore, Style, init

from config import carregar_config
from browser.runner import executar
from db.connection import criar_conexao
from db.inserter import contar_questoes

init(autoreset=True)


def menu():
    print("\n" + "=" * 40)
    print(" SCRAPING QCONCURSOS ".center(40, "="))
    print("=" * 40)

    cfg = carregar_config()
    conn = criar_conexao(cfg.database_url)
    try:
        total = contar_questoes(conn)
    finally:
        conn.close()

    print(f"Questões no banco hoje: {total}\n")
    print("1. Rodar scraping (N páginas)")
    print("2. Contar questões")
    print("3. Sair")

    escolha = input("\nEscolha: ").strip()

    if escolha == "1":
        n = input(f"Quantas páginas? (default {cfg.max_paginas_por_execucao}): ").strip()
        n_paginas = int(n) if n.isdigit() else cfg.max_paginas_por_execucao
        try:
            executar(cfg, n_paginas)
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Interrompido pelo usuário.")
        except Exception as e:
            print(f"{Fore.RED}Erro: {e}")
            raise

    elif escolha == "2":
        conn = criar_conexao(cfg.database_url)
        try:
            total = contar_questoes(conn)
            print(f"{Fore.GREEN}Total de questões: {total}")
        finally:
            conn.close()

    elif escolha == "3":
        print(f"{Fore.YELLOW}Até mais!")

    else:
        print(f"{Fore.RED}Opção inválida.")


if __name__ == "__main__":
    while True:
        menu()