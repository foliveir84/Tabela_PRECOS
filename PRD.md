# Product Requirements Document — Verificador de Preços
**Version:** 3.0 (Consolidado)  
**Status:** Documento de Referência Definitivo  
**Idioma UI:** Português de Portugal (pt-PT) | **Idioma Código:** English

---

## 1. Executive Summary

O **Verificador de Preços** é uma aplicação web desenvolvida em Python e Streamlit, destinada a uso interno de farmácias. Actua como plataforma de validação e reconciliação entre três fontes de dados:

1. **Tabela Mestra (Google Sheets)** — referência canónica de Preço de Custo (`PC Atual`) e Preço de Venda ao Público (`PVP Atual`), organizada por laboratório em múltiplas abas.
2. **Exportação Sifarma (CSV)** — dump periódico do sistema de gestão da farmácia com os preços registados localmente.
3. **Exportação Infoprex (TXT)** — ficheiro de stock e preços proveniente do sistema secundário de gestão.

A plataforma identifica discrepâncias de preços, alerta para riscos financeiros críticos (custo acima do previsto), sinaliza erros de introdução de dados, calcula margens comerciais e produz relatórios de remediação exportáveis em Excel. O sistema é cloud-ready (Streamlit Community Cloud) e desenhado para uso diário por técnicos de farmácia sem formação técnica avançada.

---

## 2. Current State vs Future State

### 2.1 Google Sheets Master Data Module

| Aspecto | Estado Actual | Estado Futuro Requerido |
|---|---|---|
| Validação de estrutura | Procura colunas por regex; sem validação de `A1 = "CNP"` | **Obrigatório** validar `A1 == 'CNP'` por aba; registar abas corrompidas |
| Reporte de abas corrompidas | Silencioso — abas inválidas ignoradas sem aviso | Nomes das abas corrompidas exibidos em dropdown expansível no topo da UI |
| Cache TTL | 3600 segundos ✅ | Manter exactamente 60 minutos ✅ |
| Estado da tabela | Visível apenas no widget `st.status` (transitório) | Exibição **permanente** no sidebar: contagem de produtos + data/hora da última actualização da sheet |
| Data de actualização da sheet | Não implementado | Obter via HTTP header `Last-Modified` ou `Date` do link de publicação |
| Nomes de colunas internas | `PVP Actual` / `PC Actual` (grafia inglesa) | Renomear para `PVP Atual` / `PC Atual` (pt-PT) |
| Valores nulos/inválidos | `dropna()` silencioso | Capturar e expor em alerta dedicado; nunca descartar silenciosamente |

### 2.2 Sifarma Export Module

| Aspecto | Estado Actual | Estado Futuro Requerido |
|---|---|---|
| Alerta 1 — PVF > PC Atual | Threshold 1% ✅ | Manter ✅ |
| Alerta 2 — PVF << PC Atual | Threshold 5% | **Alterar** para 10% |
| Tratamento PVF = 0 | Não implementado | Deduplicação por CNP + alerta crítico se entrada única |
| Tabela de divergência PVP | Misturada com outros alertas | Secção **isolada** e claramente identificada |
| Formato de exportação | Misto CSV/XLSX parcial | **Todas** as exportações em `.xlsx`; `.csv` expressamente proibido |
| Colunas de exportação | Variável por alerta | Conjunto obrigatório e fixo (ver §6.2) |
| Dados inválidos PC/PVP | `dropna()` silencioso | Alertas exportáveis dedicados por tipo de falha |
| Label do botão "em falta" | "Enviar para Seomara" | Actualizar para **"Enviar para Gilda"** |

### 2.3 Infoprex Module

| Aspecto | Estado Actual | Estado Futuro Requerido |
|---|---|---|
| Detecção de formato | Tentativa única com fallback de separador | **Detecção explícita** Sistema Antigo vs Sistema Novo |
| Identificação dinâmica de linhas | Parcial | Filtros totalmente dinâmicos, sem offsets hardcoded |
| Filtro stock (`SAC > 0`) | Implementado ✅ | Manter ✅ |
| Filtros de divergência | Implementados ✅ | Manter ✅ |
| Edição interactiva de resultados | Não implementado | **`st.data_editor`** para remoção manual de linhas antes da exportação |
| Formato de exportação | `.csv` | **Exclusivamente `.xlsx`**; reflecte exactamente os filtros e edições activos |

### 2.4 UI/UX

| Aspecto | Estado Actual | Estado Futuro Requerido |
|---|---|---|
| Idioma | Misto pt-PT / informal | Estritamente pt-PT em todos os textos visíveis ao utilizador |
| Vídeo tutorial | Implementado ✅ | Preservar obrigatoriamente ✅ |
| Alerta abas corrompidas | Ausente | Dropdown expansível proeminente no topo da página principal |
| Estado da tabela mestra | Widget transitório | Permanente no sidebar, com data de última actualização |
| Encoding | Inconsistente | Garantido em todas as leituras e exportações (ver §6.5) |

---

## 3. System Architecture & Technical Guidelines

### 3.1 Estrutura de Projecto

```
verificador_precos/
├── app.py                  # Entrypoint Streamlit; apenas lógica de UI e orquestração
├── google_sheets.py        # Carregamento, validação e cache da tabela mestra
├── sifarma.py              # Parsing do CSV Sifarma e lógica de todas as comparações
├── infoprex.py             # Parsing do TXT Infoprex, detecção de formato, margens
├── infoprex_new_system.py  # Módulo isolado para transformação do "Sistema Novo" (fornecido externamente)
├── exporters.py            # Utilitário centralizado de exportação Excel
├── validators.py           # Helpers partilhados de validação de dados
├── requirements.txt
├── .streamlit/
│   └── secrets.toml        # git-ignorado; contém GOOGLE_SHEET_ID
└── assets/
    └── ExportarFicheiro.mp4
```

### 3.2 Responsabilidades por Módulo

- **`app.py`** — Configuração da página, layout de tabs, file uploaders, invocação dos módulos de negócio, renderização de resultados. **Sem lógica de negócio.**
- **`google_sheets.py`** — Construção do URL, fetch do Excel, validação estrutural por aba, logging de erros, caching, consolidação dos dados, obtenção da data de última actualização via HTTP headers.
- **`sifarma.py`** — Ingestão do CSV, deduplicação PVF=0, todas as seis funções de alerta, cada uma devolvendo um DataFrame.
- **`infoprex.py`** — Detecção da versão de formato, filtros dinâmicos, filtro de localização, filtro SAC, cálculo de margem. Delega o parsing do "Sistema Novo" para `infoprex_new_system.py`.
- **`infoprex_new_system.py`** — Módulo isolado e desacoplado, fornecido externamente. Expõe uma função de transformação com interface estandardizada. `infoprex.py` limita-se a invocá-la.
- **`exporters.py`** — Função única `to_excel_bytes(df, sheet_name)` que devolve `bytes`. Usada por todos os botões de download.
- **`validators.py`** — `is_valid_price()`, `to_float_safe()`, `to_int_safe()`.

### 3.3 Constrangimentos Técnicos (Não Negociáveis)

1. **Simplicidade:** Funções pequenas e de responsabilidade única. Nenhuma função deve exceder 40 linhas.
2. **PEP 8:** Cumprimento estrito. Comprimento máximo de linha: 88 caracteres (compatível com Black).
3. **Strings:** Sempre plicas (`'`), excepto onde tecnicamente impossível (ex. f-strings com plica interior).
4. **Idioma do código:** 100% Inglês — variáveis, funções, classes, comentários. Português de Portugal estritamente reservado para UI e outputs visíveis ao utilizador.
5. **Dependências:** `streamlit`, `pandas`, `openpyxl`. Nenhuma dependência adicional sem aprovação explícita.
6. **Encoding:** `latin-1` como padrão para leitura de ficheiros legacy; `utf-8-sig` ou `utf-8` para contextos modernos. Fallback sempre implementado.

### 3.4 Estratégia de Cache e Estado

- A Tabela Mestra é cacheada via `@st.cache_data(ttl=3600)`.
- A chave de cache é o URL da Google Sheet. Qualquer alteração ao URL força cache miss.
- Invalidação manual via `load_master_table.clear()` + `st.rerun()`.
- Toda a análise é stateless por upload — nenhum dado persiste entre reruns além do cache da tabela mestra.

### 3.5 Design System
O arquivo `design-system.html` contém o design system completo que DEVE ser seguido na renderização da interface. Extraia e reutilize EXATAMENTE:
- Paleta de cores (backgrounds, textos, acentos, gradientes)
- Tipografia (fontes, tamanhos, pesos, hierarquia)
- Componentes de UI (botões, cards, badges, inputs)
- Espaçamentos e grid (containers, paddings, gaps)
- Animações e transições (hover, entrada, scroll)
- Efeitos visuais (glassmorphism, sombras, bordas, overlays)
- Classes CSS originais — use os mesmos nomes de classe

NÃO invente estilos novos. NÃO use frameworks CSS externos (Bootstrap, Tailwind) a menos que o design system já os utilize (a nossa referência utiliza Tailwind CSS e Iconify via scripts na head). Toda estilização da UI deve derivar estritamente deste design system.

---

## 4. Detailed Feature Requirements

### 4.1 Module: Google Sheets Master Data

#### FR-GS-01 — Construção do URL
Suportar dois formatos de `GOOGLE_SHEET_ID`:
- Começa com `2PACX...` → URL "Published to Web" (`/pub?output=xlsx`).
- ID padrão → URL de export (`/export?format=xlsx`).
- Fallback: input manual no sidebar se secret/env var estiver ausente.

#### FR-GS-02 — Validação Estrutural por Aba
Para cada aba da workbook:
1. Ler a aba para um DataFrame raw.
2. Verificar se `df.columns[0]` (célula `A1`) é igual a `'CNP'` (normalizado: strip + uppercase).
3. Se falhar: adicionar o nome da aba à lista `corrupt_sheets` e **ignorar** a aba.
4. Se válida: localizar colunas `'PC Atual'` e `'PVP Atual'` por regex (ver FR-GS-03).
5. Se as colunas alvo estiverem ausentes mesmo com A1 válido: também adicionar a `corrupt_sheets`.

#### FR-GS-03 — Correspondência Flexível de Colunas
Correspondência case-insensitive, tolerando grafias `atual`/`actual`:
- PC pattern: `^pc\s*(atual|actual)$`
- PVP pattern: `^pvp\s*(atual|actual)$`

#### FR-GS-04 — Consolidação de Dados
Colunas extraídas renomeadas para `CNP`, `PC Atual`, `PVP Atual`. Todas as abas válidas são concatenadas. Limpeza pós-concat:
1. Drop de linhas onde todas as colunas são `NaN`.
2. Converter `CNP` para `int` (coerce, drop `NaN`).
3. Converter `PC Atual` e `PVP Atual` para `float` (substituir `,` por `.`, coerce). **Não fazer dropna silencioso** — ver FR-GS-05.
4. Arredondar `PVP Atual` a 2 casas decimais.

#### FR-GS-05 — Sinalização de Preços Nulos/Inválidos
Após conversão:
- Linhas onde `PC Atual` é `NaN`, `0` ou negativo → recolher em `df_invalid_pc`.
- Linhas onde `PVP Atual` é `NaN`, `0` ou negativo → recolher em `df_invalid_pvp`.
- Ambas as colecções são devolvidas juntamente com o DataFrame principal e exibidas na UI em secções dedicadas.

#### FR-GS-06 — Data de Última Actualização da Sheet
Ao fazer o fetch do ficheiro Excel, capturar o HTTP header `Last-Modified` (ou `Date` como fallback) da resposta. Este valor deve ser armazenado e exibido no sidebar como "Última actualização da tabela: DD/MM/AAAA HH:MM".

#### FR-GS-07 — UI: Estado Permanente no Sidebar
```
Estado do Sistema
─────────────────
✅ Tabela Mestra Carregada
📦 X produtos em memória
📅 Tabela actualizada em: DD/MM/AAAA HH:MM
🕐 Cache válido até: HH:MM
─────────────────
[🔄 Recarregar Tabela de Preços]
─────────────────
ℹ️ Versão: 3.0
```

#### FR-GS-08 — UI: Alerta de Abas Corrompidas
Se `corrupt_sheets` não estiver vazia, exibir no topo da área de conteúdo principal (antes da navegação por tabs):
```
⚠️ [Expansível] Laboratórios não processados — X abas com estrutura inválida
   └── lista com os nomes das abas ignoradas
```

---

### 4.2 Module: Sifarma Export Comparison

#### FR-SF-01 — Ingestão do Ficheiro
- Aceitar `.csv` com separador `;`.
- Encoding: tentar `utf-8`, fallback para `latin-1`.
- Colunas obrigatórias: `CNP`, `DESIGNAÇÃO`, `PVF`, `PVP`. Abortar com `st.error` claro se ausentes.
- Coluna opcional: `LÍQ.` (utilizada no display do Alerta 2).
- Renomear internamente: `CNP → CNP`, `DESIGNAÇÃO → description`, `PVF → pvf`, `PVP → pvp_sifarma`.

#### FR-SF-02 — Tratamento de PVF = 0 (Pré-análise Obrigatória)
Executar **antes** de qualquer comparação:

| Cenário | Acção |
|---|---|
| CNP duplicado; uma linha com `PVF > 0`, outra com `PVF = 0` | Remover a linha `PVF = 0` silenciosamente (bónus/desconto 100%) |
| CNP único com `PVF = 0` | Isolar produto e emitir **erro crítico**: "Linha de bónus sem desconto 100% registado no Sifarma" |
| CNP com todas as linhas `PVF = 0` | Mesmo erro crítico da linha anterior |

A deduplicação compara **apenas a coluna CNP** — as restantes colunas podem ter valores diferentes entre linhas duplicadas.

#### FR-SF-03 — Alerta 1: Custo Crítico (PVF > PC Atual)
- Condição: `pvf > pc_atual * 1.01`
- Severidade: 🔴 Crítico (`st.error`)
- Mensagem: count + dataframe + exportação `.xlsx` obrigatória.
- Colunas de exportação: conjunto fixo definido em §6.2.

#### FR-SF-04 — Alerta 2: Possível Erro de Introdução (PVF << PC Atual)
- Condição: `pvf < pc_atual * 0.90` (gap de 10%)
- Severidade: ⚠️ Aviso (`st.warning`)
- Incluir coluna `LÍQ.` no display se presente no ficheiro fonte.
- Colunas de exportação: conjunto fixo definido em §6.2.

#### FR-SF-05 — Alerta 3: Divergência de PVP
- Condição: `round(pvp_sifarma, 2) != pvp_atual`
- Severidade: 🔵 Informativo
- Display: secção **isolada** com label "PVP a Actualizar" — não misturar com outros alertas.
- Colunas no display UI: `CNP`, `Descrição`, `PVP Atual (Tabela)`, `PVP Sifarma`.
- Colunas de exportação: conjunto fixo definido em §6.2.

#### FR-SF-06 — Alerta 4: PC Atual Nulo/Inválido na Tabela Mestra
- Condição: CNP encontrado na Tabela Mestra mas `PC Atual` é `NaN`, `0`, negativo ou string não conversível.
- Severidade: ⚠️ Aviso
- Display: secção dedicada "Tabela Mestra Incompleta — PC Atual".
- Exportação `.xlsx` obrigatória.

#### FR-SF-07 — Alerta 5: PVP Atual Nulo/Inválido na Tabela Mestra
- Condição: CNP encontrado na Tabela Mestra mas `PVP Atual` é `NaN`, `0`, negativo ou string não conversível.
- Severidade: ⚠️ Aviso
- Display: secção dedicada **separada** do Alerta 4 — "Tabela Mestra Incompleta — PVP Atual".
- Exportação `.xlsx` obrigatória.

#### FR-SF-08 — Alerta 6: Produtos Não Encontrados na Tabela Mestra
- Condição: `CNP` do Sifarma ausente na Tabela Mestra.
- Severidade: ❓ Desconhecido
- Display: `st.expander` expandido por defeito.
- Colunas de exportação: **exclusivamente** `CNP`, `Descrição`, `PVF`.
- Label do botão: `"📥 Exportar Excel (Enviar para Gilda)"`.

#### FR-SF-09 — Vídeo Tutorial
O bloco expansível "🎥 Ver Tutorial: Como exportar o ficheiro?" com o vídeo `ExportarFicheiro.mp4` deve ser preservado. Se o ficheiro não existir, exibir aviso gracioso — nunca lançar excepção.

---

### 4.3 Module: Infoprex Upload Processing

#### FR-IP-01 — Detecção de Versão de Formato e Ingestão
O parser deve determinar automaticamente se o TXT pertence ao **Sistema Antigo** ou **Sistema Novo** através de critérios objectivos:
- **Sistema Novo:** Identificado pela presença obrigatória dos cabeçalhos `CPR` e `DUV`. Utiliza separador `\t`.
- **Estratégia de Encoding:** Tentar sequencialmente `utf-16` (comum no novo sistema), seguido de `utf-8` e `latin1`.
- **Otimização de Memória:** Sempre que possível (no Sistema Novo), utilizar `usecols` para carregar apenas as colunas estritamente necessárias (ex: `CPR`, `NOM`, `LOCALIZACAO`, `SAC`, `PVP`, `PCU`, colunas de vendas `V0` a `V14`).

Os critérios de detecção devem estar documentados em comentários inline em `infoprex.py`. Se o formato for indeterminado, exibir `st.error` descritivo.

#### FR-IP-02 — Arquitectura Extensível para Sistema Novo
O módulo `infoprex_new_system.py` será fornecido externamente e contém a função de transformação específica para o "Sistema Novo" (baseado no script `processar_infoprex_novo.py` de referência). `infoprex.py` deve:
- Importar e invocar essa função quando o formato "Novo" for detectado.
- Delegar a renomeação de colunas (`CPR` -> `CNP`, `NOM` -> `Descrição`, `SAC` -> `Stock`, `PCU` -> `PC Atual`) e o processamento de vendas dinâmicas (`V0`-`V14` para meses retroativos) para manter a compatibilidade com a UI existente.
- A interface da função de transformação deve ser: `def transform_new_system(filepath_or_buffer) -> pd.DataFrame`.

#### FR-IP-03 — Identificação Dinâmica de Linhas
A localização das linhas de dados deve ser feita por filtros dinâmicos (presença de colunas, padrões de valores). Offsets de linhas hardcoded são **proibidos**.

#### FR-IP-04 — Filtro de Localização (Sistema Novo)
Se as colunas `DUV` (Data de Última Venda) e `LOCALIZACAO` estiverem presentes:
1. Parsear `DUV` como datetime (formato `%d/%m/%Y`, convertendo erros para `NaT`).
2. Identificar a data mais recente com `max()`.
3. Extrair o valor exacto de `LOCALIZACAO` correspondente a essa data.
4. Filtrar o DataFrame para preservar **apenas** os registos com essa `LOCALIZACAO`.

#### FR-IP-05 — Limpeza Numérica
Para as colunas `PVP`, `PCU`, `IVA`, `SAC`:
1. Remover aspas envolventes.
2. Substituir `,` por `.`.
3. Converter para `float` via `pd.to_numeric(..., errors='coerce')`, preencher `NaN` com `0.0`.

#### FR-IP-06 — Filtro de Stock (Obrigatório)
Após limpeza: `df = df[df['SAC'] > 0]`. Este filtro é mandatório e precede qualquer comparação ou exportação.

#### FR-IP-07 — Cálculo de Margem
```
iva_divisor = 1 + (IVA / 100)
pvp_net     = PVP / iva_divisor
margin (%)  = ((pvp_net - PCU) / pvp_net) * 100
```
Arredondar `margin` a 1 casa decimal. Tratar divisão por zero com `.fillna(0)`.

#### FR-IP-08 — Filtros de Divergência (UI)
Quatro controlos de filtragem combinados:
- **Radio:** `'Todos'` | `'Infoprex < Master'` | `'Infoprex > Master'`
- **Toggle:** `'Margem > 30%'`

Aplicar sequencialmente: direcção primeiro, margem depois. O count exibido acima do dataframe reflecte os filtros activos.

#### FR-IP-09 — Edição Interactiva de Resultados
A grelha de resultados Infoprex deve ser renderizada com `st.data_editor` em vez de `st.dataframe`, permitindo ao utilizador:
- Seleccionar e remover manualmente linhas específicas que não deseje incluir na exportação.
- Ver as alterações reflectidas imediatamente na grelha.
- O botão de exportação deve usar o estado **editado** do DataFrame, não o original.

Configuração do `st.data_editor`:
- `num_rows='dynamic'` para permitir remoção de linhas.
- `use_container_width=True`.
- `hide_index=True`.

#### FR-IP-10 — Exportação
- Formato: exclusivamente `.xlsx`.
- O Excel gerado reflecte **exactamente** os dados visíveis na grelha no momento do clique — após aplicação de todos os filtros e edições manuais.
- Label do botão: `"📥 Descarregar Resultados (.xlsx)"`.

---

### 4.4 Module: UI/UX

#### FR-UI-01 — Idioma
Todos os textos visíveis ao utilizador (labels, botões, tooltips, erros, avisos, mensagens de sucesso, títulos de secções, títulos de expanders) em **Português de Portugal (pt-PT)** estrito. Sem strings mistas.

#### FR-UI-02 — Layout de Página
```
[Título da Página]
[Alerta de Abas Corrompidas — se aplicável]
[Tabs: Sifarma (CSV) | Infoprex (TXT)]

Sidebar:
[Estado permanente da tabela + data de actualização]
[Botão Recarregar]
[Versão]
```

#### FR-UI-03 — Botões de Download
Todos os botões de download devem:
- Usar formato `.xlsx`.
- Ter label com ícone 📥.
- Incluir nome de ficheiro descritivo e datado (ex: `alerta_pvf_superior_YYYYMMDD.xlsx`).
- Usar `mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'`.

---

## 5. Data Validation & Error Handling Rules

### 5.1 Validação de Presença de Colunas
Cada módulo deve validar as colunas obrigatórias imediatamente após a ingestão. Exibir `st.error` com a lista exacta de colunas em falta antes de qualquer processamento.

### 5.2 Validação da Chave CNP/CPR
- Converter para numérico, coerce de erros.
- Drop de linhas onde a chave é `NaN` após conversão.
- Cast para `int64` após drop.
- Nunca ignorar silenciosamente falhas de conversão — registar o count de linhas descartadas em `st.caption`.

### 5.3 Helper de Validação de Preço (Partilhado)
Implementar `is_valid_price(value: float) -> bool` em `validators.py`:
- Devolve `False` se `value` é `NaN`, `None`, `0`, negativo, ou string não numérica.
- Usado consistentemente em todos os módulos.

### 5.4 Cadeia de Fallback de Encoding
Para todas as operações de leitura de ficheiros:
```
1. Tentativa: encoding='utf-8'
2. Fallback 1: encoding='utf-8-sig'  (para ficheiros com BOM)
3. Fallback 2: encoding='latin-1'   (para outputs de sistemas legacy)
4. Em caso de falha: st.error com nome do ficheiro e mensagem da excepção
```
Registar o encoding efectivamente usado em `st.caption` para rastreabilidade.

### 5.5 Casos Extremos de PVF = 0
Ver tabela em FR-SF-02. A deduplicação é sempre executada como pré-processamento obrigatório antes de qualquer comparação.

### 5.6 Precisão de Comparação de Floats
Todas as comparações de PVP devem arredondar ambos os lados a 2 casas decimais antes de aplicar `!=`. Nunca comparar floats raw directamente.

---

## 6. Export & Encoding Specifications

### 6.1 Função de Exportação Centralizada
`exporters.py` expõe uma única função:

```python
def to_excel_bytes(df: pd.DataFrame, sheet_name: str = 'Dados') -> bytes:
    '''Returns an in-memory .xlsx file as bytes for st.download_button.'''
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return buffer.getvalue()
```

Toda a lógica de escrita Excel em `app.py` ou noutros módulos é **proibida**. Usar exclusivamente esta função.

### 6.2 Colunas Obrigatórias — Exportações Sifarma (Alertas de Preço)
Todos os alertas de discrepância de PC ou PVP exportam obrigatoriamente estas colunas, nesta ordem:

| # | Coluna no Export | Fonte |
|---|---|---|
| 1 | `CNP` | Sifarma / Tabela Mestra |
| 2 | `Descrição` | Sifarma (`DESIGNAÇÃO`) |
| 3 | `PC Atual` | Tabela Mestra |
| 4 | `PVF` | Sifarma |
| 5 | `PVP Sifarma` | Sifarma (`PVP`) |
| 6 | `PVP Atual` | Tabela Mestra |

**Excepção:** O Alerta 6 (Produtos Não Encontrados) exporta exclusivamente `CNP`, `Descrição`, `PVF`.

### 6.3 Colunas Obrigatórias — Exportação Infoprex
O Excel gerado deve reflectir as colunas da grelha após renaming:

| Coluna Interna | Label no Export |
|---|---|
| `CNP` (de `CPR`) | `CNP` |
| `NOM` | `Designação` |
| `SAC` | `Stock` |
| `pvp_atual` | `PVP Master` |
| `pvp_infoprex` | `PVP Infoprex` |
| `margin` | `Margem (%)` |

### 6.4 Convenção de Nomes de Ficheiros
Todos os exports usam nomes descritivos e datados:

| Alert | Nome do Ficheiro |
|---|---|
| Alerta 1 | `alerta_pvf_superior_YYYYMMDD.xlsx` |
| Alerta 2 | `alerta_pvf_inferior_YYYYMMDD.xlsx` |
| Alerta 3 | `alerta_pvp_divergente_YYYYMMDD.xlsx` |
| Alerta 4 | `alerta_pc_invalido_YYYYMMDD.xlsx` |
| Alerta 5 | `alerta_pvp_invalido_YYYYMMDD.xlsx` |
| Alerta 6 | `produtos_em_falta_tabela_YYYYMMDD.xlsx` |
| Infoprex | `divergencias_infoprex_YYYYMMDD.xlsx` |

Data injectada em runtime: `datetime.today().strftime('%Y%m%d')`.

### 6.5 Contrato de Encoding

| Contexto | Encoding |
|---|---|
| Leitura de TXT Infoprex (Sistema Antigo/Novo) | `latin-1` |
| Leitura de CSV Sifarma | `utf-8` → fallback `utf-8-sig` → fallback `latin-1` |
| Fetch Google Sheets (URL-based) | Gerido pelo `openpyxl`; sem parâmetro manual |
| Escrita de `.xlsx` (export) | Gerido pelo `openpyxl`; sem parâmetro manual |

---

## 7. Implementation Plan

### Fase 0 — Preparação
- [X] Criar estrutura de directorias definitiva conforme §3.1.
- [X] Mover lógica existente de `app.py` e `processador_infop.py` para os módulos adequados.
- [X] Fixar versões em `requirements.txt`.
- [X] Confirmar que `.streamlit/secrets.toml` está no `.gitignore`.
- [X] Criar `infoprex_new_system.py` com stub da função `transform_new_system()` para garantir que a interface está definida antes da implementação.

### Fase 1 — Infraestrutura Base
**Módulos:** `validators.py`, `exporters.py`

- [X] Implementar `validators.py`: `is_valid_price()`, `to_float_safe()`, `to_int_safe()`.
- [X] Implementar `exporters.py`: função centralizada `to_excel_bytes()`.
- [X] Definir a convenção de naming de ficheiros de export com datas.

### Fase 2 — Tabela Mestra e Motor de Validação
**Módulo:** `google_sheets.py`

- [X] FR-GS-01: Construção de URL (dois formatos de ID).
- [X] FR-GS-02/03: Validação por aba (A1 = 'CNP') e matching flexível de colunas.
- [X] FR-GS-04/05: Consolidação e captura de valores inválidos (sem `dropna` silencioso).
- [X] FR-GS-06: Captura da data de última actualização via HTTP headers.
- [ ] FR-GS-07/08: UI — sidebar permanente e dropdown de abas corrompidas.
- [X] Testar com workbook mock contendo abas válidas, corrompidas e vazias.

### Fase 3 — Módulo Sifarma
**Módulo:** `sifarma.py`

- [X] FR-SF-01: Ingestão CSV com fallback de encoding.
- [X] FR-SF-02: Lógica de deduplicação PVF=0 (pré-análise).
- [X] FR-SF-03 a FR-SF-08: Seis funções de alerta, cada uma retornando um DataFrame limpo.
- [X] Verificar threshold de 10% no Alerta 2.
- [X] Cada função: puro Python, sem imports de Streamlit.
- [X] Substituir todos os exports CSV por `.xlsx` via `exporters.to_excel_bytes()`.
- [X] Actualizar label do botão "Em Falta" para "Gilda".

### Fase 4 — Módulo Infoprex
**Módulo:** `infoprex.py`

- [X] FR-IP-01/02: Detecção de formato e delegação para `infoprex_new_system.py`.
- [X] FR-IP-03/04: Identificação dinâmica de linhas e filtro de localização.
- [X] FR-IP-05/06/07: Limpeza numérica, filtro SAC, cálculo de margem.
- [X] FR-IP-08: Filtros de UI (radio + toggle).
- [X] FR-IP-09: Substituir `st.dataframe` por `st.data_editor` com `num_rows='dynamic'`.
- [X] FR-IP-10: Export `.xlsx` do estado editado (não do DataFrame original).
- [X] Testar com amostras de ambos os formatos.

### Fase 5 — Montagem da UI e Design System
**Módulo:** `app.py` (reescrita completa) e `@design_system/design-system.html`

- [X] FR-UI-01: Auditoria de todos os strings; substituir por equivalentes pt-PT.
- [X] Ligar todos os seis alertas Sifarma com os respectivos botões `.xlsx`.
- [X] Ligar filtros Infoprex e exportação do estado editado.
- [X] FR-SF-09: Verificar que o vídeo tutorial está preservado.
- [X] Aplicar o **Design System** estrito (`@design_system/design-system.html`) injetando as classes do Tailwind CSS, tipografia e ícones.
- [X] FR-UI-02/03: Validar layout do sidebar e padrão dos botões de download.

### Fase 6 — QA e Hardening
- [ ] Teste end-to-end com exportação Sifarma real: verificar que todos os alertas disparam correctamente.
- [ ] Teste end-to-end com TXT Infoprex real (ambos os formatos).
- [ ] Testar Google Sheet com aba corrompida (A1 ≠ 'CNP') → verificar alerta na UI.
- [ ] Testar botão de reload do cache → verificar que os dados são refrescados.
- [ ] Testar `st.data_editor`: remover linhas → verificar que o export reflecte a edição.
- [ ] Verificar todos os downloads `.xlsx`: encoding, colunas, nome do ficheiro.
- [ ] Linting PEP8 (`ruff` ou `flake8`).
- [ ] Revisão manual: todos os strings visíveis ao utilizador em pt-PT.
- [ ] Teste de diacríticos: inputs e outputs com `ç`, `ã`, `á`, `ê`, etc.

### Fase 7 — Deployment
- [ ] Push para GitHub.
- [ ] Configurar `GOOGLE_SHEET_ID` nos Streamlit Community Cloud Secrets.
- [ ] Smoke-test no deployment cloud.
- [ ] Actualizar `CLAUDE.md` para reflectir a arquitectura v3.0.

---

*Fim do Documento — Verificador de Preços PRD v3.0*