# AI Agents Team Directory

Bem-vindo ao directório da equipa de agentes de Inteligência Artificial do projecto **Verificador de Preços**. Esta equipa foi desenhada para cobrir as necessidades específicas de implementação técnica e análise de negócio do sistema.

## Equipa de Agentes

### 1. [Backend Developer (Python & Data Engineering)](backend-developer.md)
**Especialidade:** Processamento de dados (Pandas), integrações (Google Sheets, CSV, TXT), validação de regras de negócio e engenharia de dados.
**Quando usar:** 
- Para implementar ou refatorar a lógica de parsing e limpeza de dados (`google_sheets.py`, `sifarma.py`, `infoprex.py`).
- Para criar funções utilitárias partilhadas (`validators.py`, `exporters.py`).
- Sempre que houver necessidade de lidar com tratamento de erros, deduplicação de dados, ou conversões complexas de tipos e encodings.

### 2. [Frontend Developer (Streamlit & UI/UX)](frontend-developer.md)
**Especialidade:** Construção de interfaces com Streamlit, integração de Design Systems (Tailwind + Iconify injectados via HTML/Markdown), e gestão de estado da aplicação (UI).
**Quando usar:** 
- Para implementar componentes visuais no `app.py`.
- Para criar layouts, gerir *tabs*, e integrar alertas visuais (`st.error`, `st.warning`, `st.data_editor`).
- Para aplicar os estilos estritos do `@design_system/design-system.html`.

### 3. [Pharmacy Data & Business Analyst](pharmacy-data-analyst.md)
**Especialidade:** Análise de dados de farmácia comunitária em Portugal, cálculo de margens de lucro, e compreensão aprofundada dos ecossistemas Sifarma e Infoprex.
**Quando usar:** 
- Para validar a precisão matemática dos cálculos de discrepância (ex: margens comerciais sem IVA, validação de regras do Alerta de 10%).
- Para avaliar cenários limite dos dados (ex: comportamentos quando PVF = 0, tratamentos de stock negativo/nulo).
- Para delinear testes end-to-end do ponto de vista do farmacêutico ou desenhar relatórios de remediação.