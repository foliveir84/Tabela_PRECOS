# Arquitectura do Projecto

O sistema segue uma arquitectura modular, com clara separação de responsabilidades. Não existe mistura entre a lógica de negócio (parsing, comparação de dados) e a renderização da interface (UI).

## Estrutura de Ficheiros

```text
verificador_precos/
├── app.py                  # Entrypoint Streamlit; apenas lógica de UI e orquestração
├── google_sheets.py        # Carregamento, validação e cache da tabela mestra
├── sifarma.py              # Parsing do CSV Sifarma e lógica de todas as comparações
├── infoprex.py             # Parsing do TXT Infoprex, detecção de formato, margens
├── infoprex_new_system.py  # Módulo isolado para transformação do "Sistema Novo" (fornecido externamente)
├── exporters.py            # Utilitário centralizado de exportação Excel
├── validators.py           # Helpers partilhados de validação de dados
├── requirements.txt        # Dependências do projecto
├── .streamlit/
│   └── secrets.toml        # Ficheiro (ignorado no git) com a GOOGLE_SHEET_ID
└── assets/
    └── ExportarFicheiro.mp4
```

## Responsabilidades dos Módulos

- **`app.py`**: Configuração da página, tabs, uploads, renderização de resultados. **Nenhuma lógica de negócio** deve existir aqui.
- **`google_sheets.py`**: Lê, valida e faz cache do Excel da Google Sheet. Identifica abas corrompidas e devolve os dados agregados e validados.
- **`sifarma.py`**: Gere a ingestão do Sifarma, deduplica entradas inválidas (ex: `PVF=0` únicos) e gera os DataFrames limpos para cada alerta (Custo Alto, Divergências, etc.).
- **`infoprex.py`**: Identifica dinamicamente se o ficheiro do Infoprex é do formato Antigo ou Novo. Se for Novo, delega o processamento ao `infoprex_new_system.py`. Faz os cálculos de margens e aplica filtros de UI.
- **`exporters.py`**: Ponto único de verdade para gerar ficheiros XLSX. Nenhuma outra parte do código gera ficheiros de download diretamente.
- **`validators.py`**: Funções genéricas (`to_float_safe`, `is_valid_price`) partilhadas pelos módulos de leitura de ficheiros.