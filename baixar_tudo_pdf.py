import os
import re
import pandas as pd
import requests
import asyncio
from playwright.async_api import async_playwright

def sanitize_filename(name):
    # Transforma texto em um nome de arquivo válido para o Windows
    nome_limpo = re.sub(r'[\\/:*?"<>|]', '-', str(name)).strip()
    return nome_limpo[:150]  # Evita arquivos com nomes gigantes que o Windows possa travar

async def baixar_ou_imprimir_pdf(url, caminho_salvamento):
    """Verifica se é PDF direto. Se não for, abre num navegador invisível e "imprime" a página em PDF."""
    try:
        # 1. Tentar fazer uma requisição rápida para entender o que é o link
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=15, stream=True)
        response.raise_for_status()
        
        content_type = response.headers.get('content-type', '')
        
        # Se o link já for o próprio arquivo PDF
        if 'application/pdf' in content_type.lower() or url.lower().endswith('.pdf'):
            print(f" -> É um PDF nativo! Baixando direto: {url}")
            with open(caminho_salvamento, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
            
    except Exception as e:
        print(f" -> Erro ao verificar PDF direto. Tentaremos via Navegador: {e}")

    # 2. Se for um site HTML puro (ex: G1, Blogs, Jornais, Instituições)
    # Vamos usar um Robô Navegador Invisível para abrir a tela dele e dar "Ctrl+P" (Salvar como PDF)
    try:
        print(f" -> É um site (HTML). O robô vai abrir a página e gerar o PDF de tela...")
        async with async_playwright() as p:
            # Roda o navegador em segundo plano sem você ver (headless)
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Vai até a URL e espera ela terminar de carregar
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            # "Imprime" a página inteira nativamente como PDF com margens formatadas
            await page.pdf(path=caminho_salvamento, format="A4", print_background=True, margin={"top":"1cm", "bottom":"1cm", "left":"1cm", "right":"1cm"})
            
            await browser.close()
            return True
    except Exception as e:
        print(f" -> X Erro mortal no site (talvez anti-robô ou senha): {url}\n{e}")
        return False

async def processar_lote_pdf():
    pasta_destino = 'pdfs_catalogo'
    if not os.path.exists(pasta_destino):
        os.makedirs(pasta_destino)

    arquivo_excel = 'IAFGVP_DIRETRIZES_PREENCHIDA.xlsx'
    df = pd.read_excel(arquivo_excel)

    # Varre as linhas pulando a primeira de instrução 
    for index in range(1, len(df)):
        url = df.at[index, "Link"]
        titulo = df.at[index, "Título"]
        fonte = df.at[index, "Fonte"]

        if pd.isna(url):
            continue
            
        print(f"\n[{index}] Analisando Link...")
        
        # Pula se já soubermos que foi erro 403, ou cria nome padronizado
        if pd.notna(titulo) and "não identificado" not in str(titulo).lower() and "block" not in str(titulo).lower() and "403" not in str(titulo):
            if pd.notna(fonte) and "não identificado" not in str(fonte).lower():
                nome_pdf = sanitize_filename(f"{titulo} - {fonte}") + ".pdf"
            else:
                nome_pdf = sanitize_filename(titulo) + ".pdf"
        else:
            nome_pdf = f"Documento_Link_{index}.pdf"

        caminho_salvo = os.path.join(pasta_destino, nome_pdf)

        # Se já baixou antes, pule (ótimo se a internet cair e tiver que rodar o script de novo)
        if os.path.exists(caminho_salvo):
            print(f" -> Já existe: {nome_pdf}")
            continue

        sucesso = await baixar_ou_imprimir_pdf(url, caminho_salvo)
        
        if sucesso:
            print(f"[OK] Sucesso: Salvo em '{nome_pdf}'")
        else:
            print(f"[ERRO] Falha: Nao foi possivel capturar o PDF de '{url}'")

if __name__ == "__main__":
    print("Iniciando varredura automatizada e download de PDFs...")
    asyncio.run(processar_lote_pdf())
    print("\nPROCESSO FINALIZADO! Todos os arquivos disponíveis estão na pasta 'pdfs_catalogo'")
