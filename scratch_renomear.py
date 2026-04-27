import os
import re
import pandas as pd

def sanitize_filename(name):
    # Remove ou substitui caracteres inválidos para nomes de arquivos no Windows
    return re.sub(r'[\\/:*?"<>|]', '-', str(name)).strip()

def renomear_arquivos():
    pasta_brutos = 'conteudos_brutos'
    if not os.path.exists(pasta_brutos):
        print("Pasta 'conteudos_brutos' não encontrada.")
        return

    arquivo_excel = 'IAFGVP_DIRETRIZES_PREENCHIDA.xlsx'
    if not os.path.exists(arquivo_excel):
        print(f"Erro: Arquivo Excel '{arquivo_excel}' não encontrado.")
        return

    try:
        df = pd.read_excel(arquivo_excel)
    except Exception as e:
        print(f"Erro ao ler Excel: {e}")
        return

    # Quantidade de arquivos renomeados com sucesso
    renomeados = 0

    # Iterar apenas até o limite de links (ex: os 43 extraídos)
    # df a partir do índice 1 possui as linhas com os links 1 a 43
    for indice in range(1, len(df)):
        caminho_antigo = os.path.join(pasta_brutos, f"link_{indice}.txt")
        
        # Verifica se o arquivo TXT realmente existe
        if os.path.exists(caminho_antigo):
            titulo = df.at[indice, "Título"]
            fonte = df.at[indice, "Fonte"]
            
            # Se a linha não tiver Título ou estiver com Erro, pula
            if pd.isna(titulo) or "Acesso Bloqueado" in str(titulo) or titulo == "não identificado":
                # print(f"[{indice}] Título inválido ou arquivo bloqueado, não será renomeado.")
                continue
                
            # Verifica a fonte
            if pd.isna(fonte) or str(fonte).strip().lower() == "não identificado":
                nome_novo = sanitize_filename(titulo) + ".txt"
            else:
                nome_novo = sanitize_filename(titulo) + " - " + sanitize_filename(fonte) + ".txt"

            # Limita tamanho máximo do arquivo para evitar erro no Windows (255 caracteres totais)
            if len(nome_novo) > 150:
                nome_novo = nome_novo[:150].strip() + ".txt"

            caminho_novo = os.path.join(pasta_brutos, nome_novo)

            try:
                # Evita conflito se o nome do arquivo já existir
                if os.path.exists(caminho_novo):
                    continue
                os.rename(caminho_antigo, caminho_novo)
                print(f"[{indice}] Renomeado -> {nome_novo}")
                renomeados += 1
            except Exception as e:
                print(f"Erro ao renomear {caminho_antigo}: {e}")

    print(f"\nFinalizado! {renomeados} arquivos brutos foram renomeados.")

if __name__ == "__main__":
    renomear_arquivos()
