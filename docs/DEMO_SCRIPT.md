# Roteiro do Video de Demonstracao — Simples Editor

> Duracao: 2-3 minutos | Formato: gravacao de tela com narracao

---

## Instrucoes para Gravacao

- Ferramenta sugerida: OBS Studio (gratuito) ou Loom
- Resolucao: 1920x1080
- Audio: Narracao clara, sem ruido de fundo
- Arquivo final: `docs/demo.mp4`

---

## Roteiro

### 0:00-0:15 — Abertura

**[Tela: Homepage do Simples Editor]**

"O Simples Editor e uma plataforma web para ensino de programacao usando a linguagem SIMPLES. Com ele, alunos podem escrever, compilar e executar codigo direto do navegador, sem instalar nada."

---

### 0:15-0:45 — Editor e Syntax Highlight

**[Tela: Editor Monaco com codigo SIMPLES]**

"O editor usa o Monaco — o mesmo do VS Code — com syntax highlight customizado para as 27 palavras-chave da linguagem SIMPLES. Vejam como `programa`, `inicio`, `se`, `enquanto` aparecem em ciano com negrito."

**[Digitar codigo simples]**

```
programa
inicio
  inteiro x
  leia x
  escreva "O dobro e: "
  escreval x * 2
fim
```

"O layout tem tres paineis: editor a esquerda, painel NASM a direita, e terminal interativo embaixo. Os paineis sao redimensionaveis — da pra arrastar a divisoria."

---

### 0:45-1:30 — Compilacao e Execucao

**[Clicar botao Run]**

"Ao clicar em Run, o codigo e enviado pro backend. O compilador `simplesc` traduz SIMPLES para assembly NASM, que aparece no painel direito em tempo real."

**[Mostrar painel NASM populado]**

"Reparem no assembly gerado: declaracao de string, chamada para `leia`, operacao de multiplicacao."

**[Interagir no terminal]**

"O terminal usa xterm.js e se comunica via WebSocket. Quando o programa pede um valor com `leia`, o terminal espera input do usuario. Vou digitar 21..."

**[Digitar 21 no terminal]**

"E o programa responde: 'O dobro e: 42'. Tudo executado dentro de um sandbox Docker seguro, sem acesso a rede, com filesystem read-only."

---

### 1:30-2:00 — Tratamento de Erros

**[Criar erro: remover 'fim']**

"Se eu esquecer a palavra `fim`, o compilador detecta o erro e mostra um marker vermelho exatamente na linha do problema."

**[Mostrar marker de erro no Monaco]**

"O painel de saida mostra a mensagem: 'Erro: esperado `fim` no final do programa'. O aluno sabe exatamente o que corrigir."

---

### 2:00-2:30 — Infraestrutura e CI/CD

**[Tela: GitHub Actions ou terminal com docker compose ps]**

"Por tras, o projeto usa Docker Compose com 4 servicos: nginx, frontend React, backend Flask, e sandbox isolado."

**[Mostrar CI verde no GitHub]**

"O CI/CD no GitHub Actions roda 4 jobs paralelos: lint e testes no frontend e backend, build das imagens Docker, e smoke tests que sobem todo o stack e verificam health checks."

---

### 2:30-3:00 — Encerramento

**[Tela: Homepage novamente]**

"O Simples Editor esta pronto para deploy em producao na Oracle Cloud Ampere A1 com TLS valido e dominio proprio."

"O projeto completo, incluindo codigo-fonte, documentacao e instrucoes de deploy, esta disponivel no GitHub."

"Obrigado!"

---

## Checklist da Gravacao

- [ ] Abrir o projeto localmente (`docker compose up`)
- [ ] Preparar o programa de exemplo (com `leia`)
- [ ] Preparar o programa com erro (sem `fim`)
- [ ] Testar audio do microfone
- [ ] Gravar em 1080p
- [ ] Salvar como `docs/demo.mp4`
- [ ] Atualizar README.md com link para o video
