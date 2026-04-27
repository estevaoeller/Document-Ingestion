# Document-Ingestion

Pipeline em Python para **coleta, classificação e organização de conteúdos web/PDF** com apoio de IA, usando uma planilha Excel como fonte e destino dos metadados.

## Visão geral

Este repositório reúne três scripts principais:

1. `automacao_ia_diretrizes.py` — lê links da planilha, extrai texto (HTML/PDF), envia para o Gemini e preenche campos estruturados.
2. `baixar_tudo_pdf.py` — percorre os links e salva um PDF por item (download direto quando possível, ou impressão via Playwright).
3. `scratch_renomear.py` — renomeia arquivos `.txt` de conteúdo bruto usando `Título` e `Fonte` da planilha.

## Estrutura esperada

```text
Document-Ingestion/
├── README.md
├── automacao_ia_diretrizes.py
├── baixar_tudo_pdf.py
├── scratch_renomear.py
├── .env                              # você cria localmente
├── IAFGVP_DIRETRIZES_PREENCHIDA.xlsx # você fornece localmente
├── conteudos_brutos/                 # opcional (usado no script de renomear)
└── pdfs_catalogo/                    # criado automaticamente
```

## Requisitos

- Python 3.10+
- Pip atualizado
- Dependências Python:
  - `pandas`
  - `requests`
  - `beautifulsoup4`
  - `PyMuPDF`
  - `google-generativeai`
  - `python-dotenv`
  - `openpyxl`
  - `playwright`
- Navegador do Playwright instalado (Chromium)

## Instalação

### 1) Criar ambiente virtual (recomendado)

```bash
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate    # Windows PowerShell
```

### 2) Instalar dependências

```bash
pip install pandas requests beautifulsoup4 pymupdf google-generativeai python-dotenv openpyxl playwright
python -m playwright install chromium
```

### 3) Configurar variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
GEMINI_API_KEY=sua_chave_api_aqui
```

## Formato da planilha

Os scripts esperam o arquivo `IAFGVP_DIRETRIZES_PREENCHIDA.xlsx` na raiz, com pelo menos estas colunas:

- `Link`
- `Título`
- `Resumo`
- `Fonte`
- `Tipo`
- `Tags`
- `Relevância`

> Observação: os scripts foram escritos para começar do índice 1 da planilha (pulando a primeira linha de instrução).

## Como usar

### 1) Enriquecer a planilha com IA

```bash
python automacao_ia_diretrizes.py
```

O script:
- Lê URLs da coluna `Link` (faixa de teste atual: linhas 1 a 9).
- Extrai texto de HTML ou PDF.
- Pede ao Gemini para retornar campos no formato definido.
- Atualiza a própria planilha.

### 2) Baixar/gerar PDFs para catálogo

```bash
python baixar_tudo_pdf.py
```

O script:
- Cria a pasta `pdfs_catalogo` se não existir.
- Tenta baixar PDF direto quando `content-type` for PDF.
- Se for HTML, abre em navegador headless e exporta para PDF (A4).
- Evita reprocessar arquivos já existentes.

### 3) Renomear conteúdos brutos (`.txt`)

```bash
python scratch_renomear.py
```

O script:
- Procura arquivos no padrão `conteudos_brutos/link_<indice>.txt`.
- Renomeia com base em `Título` e `Fonte` da planilha.
- Sanitiza caracteres inválidos para nome de arquivo.

## Fluxo recomendado

1. Preencha/valide a coluna `Link` na planilha.
2. Rode `automacao_ia_diretrizes.py` para gerar metadados.
3. Rode `baixar_tudo_pdf.py` para materializar o acervo em PDF.
4. (Opcional) Rode `scratch_renomear.py` para organizar `.txt` brutos.

## Solução de problemas

- **`GEMINI_API_KEY` não encontrada**: confira se o `.env` está na raiz e com a chave correta.
- **Erro no Playwright**: execute novamente `python -m playwright install chromium`.
- **Bloqueio de scraping (403 / anti-bot)**: alguns sites podem impedir coleta automática; nesses casos, a linha pode ficar com “não identificado”.
- **Problemas no Excel**: confirme se `openpyxl` está instalado e se o arquivo não está aberto em outro programa.

## Limitações conhecidas

- O script de IA está com recorte de teste (`urls[1:10]`) e não processa toda a planilha por padrão.
- O parsing da resposta da IA depende de rótulos exatos (`Título:`, `Resumo:`, etc.).
- Conteúdos muito longos podem ser truncados antes de enviar ao modelo.

## Próximas melhorias (sugestões)

- Adicionar `requirements.txt`.
- Incluir logs estruturados e relatório final por execução.
- Parametrizar faixa de linhas via CLI.
- Implementar retries/backoff para requisições HTTP.
- Criar testes automatizados para funções utilitárias.
