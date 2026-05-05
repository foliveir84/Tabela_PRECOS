# Funcionalidades e Módulos

O Verificador de Preços funciona através de três grandes módulos de ingestão e comparação de dados.

## 1. Módulo Tabela Mestra (Google Sheets)

A Tabela Mestra é a **referência canónica** para Preços de Custo e Venda.
- **Validação:** Cada laboratório está numa aba (sheet). Todas as abas válidas têm de ter a célula `A1` exactamente com o valor `CNP`. Abas que falhem são sinalizadas no topo da página.
- **Identificação de Colunas:** O módulo usa regex (`^pc\s*(atual|actual)$` e `^pvp\s*(atual|actual)$`) para encontrar colunas com tolerância a erros ortográficos.
- **Dados Inválidos:** Quaisquer CNPs encontrados em que o Preço de Custo ou Venda seja `0`, nulo, negativo ou contenha caracteres inválidos, não são apagados silenciosamente, mas sim capturados para dois alertas exportáveis independentes.
- **Status Permanente:** A barra lateral exibe permanentemente "Tabela Mestra Carregada", quantidade de produtos em memória, a "data da última atualização" obtida do HTTP header, e a duração do cache (1 hora).

## 2. Módulo Sifarma (Ficheiro CSV)

Recebe o dump de preços do Sifarma e compara-os contra a Tabela Mestra. Antes da comparação, linhas com `PVF=0` são deduplicadas caso existam duplicados com valores válidos, ou são sinalizadas como erro crítico se exclusivas.

Alertas implementados:
- **Alerta 1 (Custo Alto):** `PVF > PC_Mestre * 1.01` (Alerta Crítico)
- **Alerta 2 (Aviso Custo Baixo):** `PVF < PC_Mestre * 0.90` (Aviso de 10%)
- **Alerta 3 (Divergência PVP):** `PVP_Sifarma != PVP_Mestre`
- **Alerta 4 & 5 (Tabela Mestra Incompleta):** CNP presente mas com PC ou PVP inválido/inexistente.
- **Alerta 6 (Não Encontrados):** Produtos existentes no Sifarma mas omissos da Tabela Mestra.
- **Sucesso (Sem Divergências):** Se o ficheiro for processado e não existirem divergências em nenhum dos alertas anteriores, o sistema exibe uma mensagem de sucesso a verde.

## 3. Módulo Infoprex (Ficheiro TXT)

Recebe o ficheiro de stock do Infoprex (podendo ser gerado de um sistema Antigo ou de um Sistema Novo, que o módulo deteta automaticamente).
- **Sistema Novo:** Lê utilizando `usecols` para minimizar a memória (apenas `CPR`, `NOM`, etc.) com encoding `utf-16`. O ficheiro usa uma localização baseada na Data de Última Venda (`DUV`) mais recente (`max`).
- **Filtro de Stock:** Apenas processa e mostra produtos onde o `Stock Atual` (`SAC`) seja estritamente superior a zero.
- **Cálculo da Margem Comercial:** A margem é calculada removendo primeiro o IVA (`1 + (IVA / 100)`) ao PVP.
- **Filtros de Interação:** O utilizador pode filtrar na UI produtos com PVP Maior ou Menor que o Master e ocultar margens abaixo de 30%.
- **Edição Interativa:** A tabela visual usa o widget interactivo (`st.data_editor`), permitindo remover registos antes de efectuar o download.