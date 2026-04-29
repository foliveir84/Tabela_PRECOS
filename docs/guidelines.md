# Guidelines e Padrões Técnicos

O desenvolvimento do Verificador de Preços obedece a regras restritas de código e idioma para garantir consistência, robustez e facilidade de manutenção.

## Regras de Código (Não Negociáveis)

1. **Simplicidade e Modularidade:**
   - As funções devem ser curtas e ter apenas **uma responsabilidade**.
   - Limite sugerido: máximo de 40 linhas por função.

2. **Formatação PEP 8:**
   - O código tem de respeitar integralmente a norma PEP 8.
   - O limite de largura de linha é de **88 caracteres** (compatível com a ferramenta de linting *Black*).

3. **Uso de Strings:**
   - Utilizar **SEMPRE** aspas simples (`'`) para definir strings em Python.
   - Aspas duplas (`"`) só devem ser usadas quando tecnicamente obrigatório (ex: uma f-string que já contenha plicas no seu interior).

4. **Tratamento de Excepções e Conversões:**
   - **Nunca** ignorar falhas de conversão de tipos de dados silenciosamente (evitar `dropna()` agressivos em colunas chave como o `CNP` ou preços sem registar o que foi apagado).
   - Conversões de moeda (strings com vírgulas para floats) devem ser feitas com robustez em módulos dedicados (`validators.py`).

## Regras de Idioma

Para manter a base de dados organizada e a interface focada no utilizador final:

- **Código-Fonte (100% Inglês):** Todos os nomes de variáveis, métodos, classes, ficheiros e comentários técnicos no código Python têm de ser escritos em Inglês.
- **Interface de Utilizador (Português de Portugal):** Todos os textos exibidos no ecrã (labels, tooltips, alertas de erro `st.error`, mensagens de sucesso e headers) devem estar rigorosamente em Português de Portugal (pt-PT). É proibida a utilização de strings informais ou com mistura de idiomas.