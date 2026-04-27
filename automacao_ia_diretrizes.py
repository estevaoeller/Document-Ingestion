import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import os
import fitz # PyMuPDF
import google.generativeai as genai
from dotenv import load_dotenv

# ==========================================
# CONFIGURAÇÃO
# ==========================================
# 1. Carrega as configurações secretas do arquivo .env
load_dotenv()

# 2. Puxa a chave com segurança para dentro do código
CHAVE_API = os.getenv("GEMINI_API_KEY")

if not CHAVE_API:
    print("ERRO: Sua chave API não foi encontrada!")
    print("Por favor, crie um arquivo chamado '.env' e coloque sua chave lá.")
    exit()

genai.configure(api_key=CHAVE_API)
model = genai.GenerativeModel('gemini-1.5-flash')

def clean_text(text):
    """Limpa quebras de linha excessivas e espaços em branco."""
    return re.sub(r'\s+', ' ', text).strip()

def extrair_texto_da_web(url):
    """Acessa o site e limpa o HTML ou lê o PDF para pegar apenas texto legível"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        content_type = response.headers.get('content-type', '')
        
        # Estratégia para PDF
        if 'application/pdf' in content_type.lower() or url.lower().endswith('.pdf'):
            with open("temp.pdf", 'wb') as f:
                f.write(response.content)
            
            texto = ""
            with fitz.open("temp.pdf") as doc:
                # Limitamos a leitura às primeiras 30 páginas para não sobrecarregar
                for page in doc[:30]:
                    texto += page.get_text()
            
            # Limpa o arquivo temporário
            if os.path.exists("temp.pdf"):
                os.remove("temp.pdf")
                
            return clean_text(texto)

        # Estratégia HTML (Web Sites padrão)
        else:
            soup = BeautifulSoup(response.content, 'html.parser')
            # Extraindo elementos visuais que não são texto de leitura
            for script in soup(["script", "style", "nav", "header", "footer"]):
                script.extract()
                
            return clean_text(soup.get_text())

    except Exception as e:
        return f"Erro ao acessar conteúdo: {e}"

def analisar_com_ia(texto_bruto, url_original):
    """Envia o texto cru para a IA do Google e devolve formatado no padrão exigido."""
    
    # Este é exatamente o mega-prompt de engenharia validado por você
    prompt = f"""
Função
Você é um assistente responsável por analisar conteúdos a partir de links e gerar um registro estruturado para um sistema de Read Later, com foco em clareza, consistência e utilidade futura.

Entrada
Link: {url_original}

Saída (formato obrigatório)
Retorne sempre no seguinte formato:

Link:
Título:
Resumo:
Fonte:
Tipo:
Tags:
Relevância:

Não inclua explicações adicionais fora desses campos.

Regras gerais
• Seja objetivo e consistente e não invente informações.
• Se não for possível identificar algum campo, indique "não identificado".
• Priorize utilidade prática e recuperação futura.
• Evite linguagem genérica ou vaga.

Regras por campo:
• Link: Retorne a URL fornecida, removendo parâmetros de rastreamento irrelevantes.
• Título: O título real e completo.
• Resumo: Foque no viés sobre Inteligência artificial nas empresas e universo corporativo.
• Relevância: Alta, Média ou Baixa de acordo com o poder estratégico e valor prático.

Texto base para ser lido:
------------------------------------------
{texto_bruto[:15000]} # Limitando quantidade de caracteres de texto bruto para economia de tokens
------------------------------------------
"""
    
    # Processa na IA
    resposta = model.generate_content(prompt)
    return resposta.text

def processar_e_salvar_planilha():
    arquivo = 'IAFGVP_DIRETRIZES_PREENCHIDA.xlsx'
    print(f"Lendo planilha: {arquivo}")
    
    # Lendo a planilha (necessário biblioteca openpyxl instalada via pip)
    df = pd.read_excel(arquivo)
    
    # Extrai as url da coluna chamada "Link"
    urls = df['Link'].tolist()
    
    # Defina aqui de qual linha até qual linha quer testar (ex: linhas 1 até 10)
    for index, url in enumerate(urls[1:10], start=1): 
        # Ignora linhas em branco
        if pd.isna(url):
            continue
            
        print(f"\n[{index}] Extraindo e Sumarizando: {url}")
        
        texto_site = extrair_texto_da_web(url)
        
        # Sucesso no download do texto
        if "Erro" not in texto_site and len(texto_site) > 50:
            print(" -> Sumarizando com a IA...")
            resposta_ia = analisar_com_ia(texto_site, url)
            
            # Divide os campos pelo formato de Enter (\n)
            linhas = resposta_ia.split('\n')
            for linha in linhas:
                if linha.startswith("Título:"):
                    df.at[index, "Título"] = linha.replace("Título:", "").strip()
                elif linha.startswith("Resumo:"):
                    df.at[index, "Resumo"] = linha.replace("Resumo:", "").strip()
                elif linha.startswith("Fonte:"):
                    df.at[index, "Fonte"] = linha.replace("Fonte:", "").strip()
                elif linha.startswith("Tipo:"):
                    df.at[index, "Tipo"] = linha.replace("Tipo:", "").strip()
                elif linha.startswith("Tags:"):
                    df.at[index, "Tags"] = linha.replace("Tags:", "").strip()
                elif linha.startswith("Relevância:"):
                    df.at[index, "Relevância"] = linha.replace("Relevância:", "").strip()
            print(" -> OK! Linha injetada no DataFrame temporário.")

        else:
            # Caso o servidor tenha barrado a coleta
            print(" -> Erro ao puxar os dados, preenchendo coluna com falha.")
            df.at[index, "Resumo"] = f"Não identificado (Falha no Scraping - {texto_site})"
            df.at[index, "Relevância"] = "Baixa - Inacessível"

    # Salva o arquivo sobrescrevendo a versão local
    df.to_excel(arquivo, index=False)
    print("\n[PROCESSO CONCLUÍDO] Planilha atualizada e salva com sucesso!")

if __name__ == "__main__":
    processar_e_salvar_planilha()
