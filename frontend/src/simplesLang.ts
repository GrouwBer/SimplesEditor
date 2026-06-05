import type { languages } from 'monaco-editor'

// 27 palavras reservadas da linguagem SIMPLES
const SIMPLES_KEYWORDS = [
  // Estrutura do programa
  'programa', 'inicio', 'fim',
  // Tipos
  'inteiro', 'flutuante', 'vazio',
  // Controle de fluxo
  'se', 'entao', 'senao', 'fimse',
  // Lacos
  'enquanto', 'fimenquanto',
  'para', 'de', 'ate', 'passo', 'faca', 'fimpara',
  // Entrada e saida
  'leia', 'escreva', 'escreval',
  // Operadores logicos
  'e', 'ou', 'nao',
  // Operador aritmetico
  'div',
  // Subprograma
  'procedimento', 'retorna',
] as const

export const SIMPLES_LANGUAGE_ID = 'simples'

// Tokenizer Monarch para a linguagem SIMPLES
// Ref: PRD 13 - Editor de codigo (Monaco)
export const simplesMonarchTokens: languages.IMonarchLanguage = {
  ignoreCase: true,
  keywords: SIMPLES_KEYWORDS as unknown as string[],

  operators: [
    '<-', '+', '-', '*', 'div', '>', '<', '=', '<>', '>=', '<=',
  ],

  symbols: /[=<>+\-*/]+/,

  tokenizer: {
    root: [
      // Comentarios de linha unica
      [/;.*$/, 'comment'],

      // Identificadores e palavras-chave
      [/[a-zA-Z_]\w*/, {
        cases: {
          '@keywords': 'keyword',
          '@default': 'identifier',
        },
      }],

      // Numeros flutuantes
      [/\d+\.\d+/, 'number.float'],

      // Numeros inteiros
      [/\d+/, 'number'],

      // Atribuicao (<-) como operador especial
      [/<-/, 'operator'],

      // Operadores simbolicos
      [/@symbols/, {
        cases: {
          '@operators': 'operator',
          '@default': '',
        },
      }],

      // Delimitadores
      [/[(),;]/, 'delimiter'],

      // Strings entre aspas duplas
      [/"[^"]*"/, 'string'],

      // Espacos em branco
      [/\s+/, 'white'],
    ],
  },
}

// Configuracao de tema escuro para SIMPLES
// Keywords em ciano (#56b6c2), numeros em laranja (#d19a66),
// comentarios em verde (#98c379), strings em amarelo (#e5c07b)
export const simplesDarkTheme: languages.IMonarchLanguageRule[] = []
