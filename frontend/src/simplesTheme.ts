import type { editor } from 'monaco-editor'

// Tema escuro profissional para o Simples Editor
// Inspirado no GitHub Dark + One Dark Pro, adaptado para SIMPLES
export const SIMPLES_DARK_THEME = 'simples-dark'

export function defineSimplesTheme(monaco: { editor: typeof editor }): void {
  monaco.editor.defineTheme(SIMPLES_DARK_THEME, {
    base: 'vs-dark',
    inherit: true,
    rules: [
      // Keywords SIMPLES — ciano vibrante com negrito
      { token: 'keyword', foreground: '56b6c2', fontStyle: 'bold' },

      // Numeros — laranja quente
      { token: 'number', foreground: 'd19a66' },
      { token: 'number.float', foreground: 'd19a66' },
      { token: 'number.hex', foreground: 'd19a66' },

      // Strings — amarelo dourado
      { token: 'string', foreground: 'e5c07b' },
      { token: 'string.escape', foreground: 'e5c07b', fontStyle: 'bold' },

      // Comentarios — verde suave em italico
      { token: 'comment', foreground: '98c379', fontStyle: 'italic' },
      { token: 'comment.line', foreground: '98c379', fontStyle: 'italic' },
      { token: 'comment.block', foreground: '98c379', fontStyle: 'italic' },

      // Operadores — roxo
      { token: 'operator', foreground: 'c678dd' },
      { token: 'operator.sql', foreground: 'c678dd' },

      // Delimitadores e pontuacao — cinza claro
      { token: 'delimiter', foreground: 'abb2bf' },
      { token: 'delimiter.parenthesis', foreground: '61afef' },
      { token: 'delimiter.square', foreground: '61afef' },
      { token: 'delimiter.curly', foreground: 'e06c75' },

      // Identificadores — cinza neutro
      { token: 'identifier', foreground: 'abb2bf' },
      { token: 'identifier.function', foreground: '61afef' },
      { token: 'identifier.macro', foreground: 'e06c75' },

      // Tipos — vermelho claro
      { token: 'type', foreground: 'e06c75' },
      { token: 'type.identifier', foreground: 'e5c07b' },

      // Variaveis — azul claro
      { token: 'variable', foreground: 'e06c75' },
      { token: 'variable.predefined', foreground: 'd19a66' },

      // Labels e diretivas — azul
      { token: 'label', foreground: '61afef', fontStyle: 'italic' },
      { token: 'directive', foreground: 'c678dd', fontStyle: 'bold' },

      // Registradores (para NASM) — laranja
      { token: 'register', foreground: 'd19a66' },

      // Erros — vermelho forte com fundo
      { token: 'invalid', foreground: 'f44747', background: '442222' },
      { token: 'invalid.deprecated', foreground: 'd19a66', fontStyle: 'strikethrough' },

      // Whitespace — invisivel mas presente
      { token: 'white', foreground: '3b4048' },
    ],
    colors: {
      // Fundo do editor — quase preto com tom azulado
      'editor.background': '#0d1117',
      'editor.foreground': '#c9d1d9',

      // Linha ativa — highlight sutil
      'editor.lineHighlightBackground': '#161b22',
      'editor.lineHighlightBorder': '#1c2128',

      // Selecao — azul escuro
      'editor.selectionBackground': '#264f78',
      'editor.selectionHighlightBackground': '#1c3856',
      'editor.inactiveSelectionBackground': '#1c3856',

      // Cursor — azul vivo
      'editorCursor.foreground': '#58a6ff',

      // Gutters (numeros de linha) — escuro consistente
      'editorGutter.background': '#0d1117',
      'editorGutter.addedBackground': '#1b4721',
      'editorGutter.modifiedBackground': '#1b3d5c',
      'editorGutter.deletedBackground': '#542426',

      // Linha do gutter ativa
      'editorLineNumber.foreground': '#484f58',
      'editorLineNumber.activeForeground': '#c9d1d9',

      // Borda de overview ruler
      'editorOverviewRuler.border': '#010409',

      // Scrollbar — escura e discreta
      'scrollbar.shadow': '#00000033',
      'scrollbarSlider.background': '#484f5833',
      'scrollbarSlider.hoverBackground': '#6e768133',
      'scrollbarSlider.activeBackground': '#8b949e66',

      // Minimap — escuro
      'minimap.background': '#0d1117',

      // Find/match — destaque
      'editor.findMatchBackground': '#9e6a03',
      'editor.findMatchHighlightBackground': '#3a2c17',

      // Indent guides
      'editorIndentGuide.background': '#21262d',
      'editorIndentGuide.activeBackground': '#30363d',

      // Breadcrumbs
      'breadcrumb.background': '#0d1117',

      // Widgets
      'editorWidget.background': '#161b22',
      'editorWidget.border': '#30363d',

      // Sugestoes/autocomplete
      'editorSuggestWidget.background': '#161b22',
      'editorSuggestWidget.border': '#30363d',
      'editorSuggestWidget.selectedBackground': '#1c3856',

      // Bracket matching
      'editorBracketMatch.background': '#1c3856',
      'editorBracketMatch.border': '#58a6ff',
    },
  })
}
