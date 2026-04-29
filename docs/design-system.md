# Design System e Interface (UI)

O design e a interface gráfica deste projecto obedecem a regras estritas ditadas por um *Design System* centralizado. A coesão visual e funcionalidade fluída são prioritárias na arquitetura de UI.

## Fonte de Verdade
O ficheiro `@design_system/design-system.html` documenta todo o design system (baseado na referência original do NexusFlow). A renderização dos componentes na aplicação (ex. botões customizados via HTML injectado, styling da página, etc.) DEVE ser uma cópia exata do que lá está descrito.

### Extracção Direta
Ao implementar ou refatorar componentes da UI da nossa aplicação baseada em Streamlit (através do uso de Markdown/HTML injection se necessário, mantendo compatibilidade com os wrappers nativos), o desenvolvimento tem de reutilizar:
- **Paleta de Cores e Gradientes**: Exatamente as mesmas cores e stops de gradiente.
- **Tipografia**: Fontes, tamanhos, pesos e regras de escala de Headings e Paragraphs.
- **Cards e Botões**: Aplicar as mesmas sombras, layouts de "Bento box" (quando aplicável a estatísticas) e estilos visuais (`glassmorphism`, `overlays`).
- **Animações e Efeitos Visuais**: Usar os mesmos comportamentos em *hover*, transições ou estados.
- **Nomes das Classes CSS**: Os mesmos usados no design-system HTML.

### Restrições Adicionais
- **É estritamente proibido** inventar novos estilos visuais soltos. Se precisar de um estilo, procure a solução equivalente já presente no ficheiro `design-system.html`.
- **Frameworks Externos**: Não acrescente livrarias extra (como Bootstrap ou injectar o CDN do Tailwind de novo, visto que as instruções já indicam como o design usa o Tailwind + Iconify). Toda a estilização obedece às regras originais sem excepções.