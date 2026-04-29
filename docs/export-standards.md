# Padrões de Exportação e Encodings

O módulo de exportação e processamento do Verificador de Preços garante segurança e qualidade no momento de partilha de relatórios de dados pela farmácia.

## Formato e Utilitário Centralizado

- **Proibição Absoluta do formato `.csv`:** Todos os outputs para o utilizador, sem exceção, têm de ser fornecidos no formato `Excel (.xlsx)`.
- O código usa uma função de exportação estrita localizada no ficheiro `exporters.py` (usando o `openpyxl` através de um `io.BytesIO()`) que devolve bytes ao `st.download_button`. Nenhuma outra forma de gerar exportações deve ser desenvolvida ou introduzida no `app.py`.

## Colunas Rigorosas

### Sifarma (Alertas de Custo/PVP)
A dataframe de download dos Alertas (excluindo os "Produtos em falta") tem de conter obrigatoriamente (e exclusivamente) as seguintes colunas e respetiva nomenclatura:
1. `CNP`
2. `Descrição`
3. `PC Atual`
4. `PVF`
5. `PVP Sifarma`
6. `PVP Atual`

O alerta de "Produtos Não Encontrados" exporta estritamente: `CNP`, `Descrição`, `PVF`.

### Infoprex
O Excel gerado vai reflectir o DataFrame editado e final visto na tela pelo utilizador (via widget interativo), incluindo as seguintes colunas visíveis:
- `CNP`
- `Designação`
- `Stock`
- `PVP Master`
- `PVP Infoprex`
- `Margem (%)`

## Regras de Nomenclatura

Os botões de exportação geram nomes de ficheiro automáticos anexando a data de hoje.
- Alerta Custo Superior: `alerta_pvf_superior_YYYYMMDD.xlsx`
- Alerta Custo Inferior: `alerta_pvf_inferior_YYYYMMDD.xlsx`
- Alerta PVP Divergente: `alerta_pvp_divergente_YYYYMMDD.xlsx`
- Alerta PC Inválido: `alerta_pc_invalido_YYYYMMDD.xlsx`
- Alerta PVP Inválido: `alerta_pvp_invalido_YYYYMMDD.xlsx`
- Produtos em falta Tabela Mestra: `produtos_em_falta_tabela_YYYYMMDD.xlsx`
- Infoprex Export: `divergencias_infoprex_YYYYMMDD.xlsx`

## Segurança de Encodes

Para garantir que acentuações como `ç`, `ã`, ou `á` do português nunca se partam, o pipeline de ingestão testa codificações da seguinte forma:
1. Infoprex Sistema Novo: **`utf-16`** → `utf-8` → `latin-1`.
2. Infoprex Antigo: **`latin-1`**.
3. Sifarma: **`utf-8`** → `utf-8-sig` → `latin-1`.