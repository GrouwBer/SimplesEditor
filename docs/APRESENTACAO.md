# Apresentacao Final — Simples Editor

> Roteiro para apresentacao de 10-15 minutos | Sprint 6 — Junho 2026

---

## Slide 1 — Capa

**Simples Editor**
Plataforma Web para Ensino de Programacao com a Linguagem SIMPLES

Equipe: GrouwBer, JoaoGarciaM, Jkvzin
Disciplina: [nome] — Prof. [nome]

---

## Slide 2 — O Problema

- Alunos iniciantes enfrentam barreiras para instalar compiladores e configurar ambientes
- Ferramentas existentes sao complexas (IDEs pesadas, terminais intimidantes)
- Feedback lento: compilar → executar → ver erro → repetir

**Nossa solucao**: Um editor online completo que compila e executa codigo SIMPLES direto no navegador.

---

## Slide 3 — Arquitetura

```
┌─────────────┐    ┌──────────┐    ┌────────────────┐
│  Navegador   │────│  Nginx   │────│  Frontend (React)│
│  (xterm.js,  │    │  (proxy) │    │  Monaco Editor   │
│   Monaco)    │    └──────────┘    └────────────────┘
└─────────────┘                          │
       │                                 │ REST + WebSocket
       │                          ┌──────┴──────────┐
       │                          │  Backend (Flask) │
       └──────────────────────────│  + simplesc      │
                                  │  + gunicorn      │
                                  └──────┬──────────┘
                                         │ docker-py
                                  ┌──────┴──────────┐
                                  │  Sandbox         │
                                  │  (Docker + QEMU) │
                                  └─────────────────┘
```

- **Frontend**: React + TypeScript + Monaco Editor + xterm.js
- **Backend**: Flask + flask-sock + gevent + gunicorn
- **Compilador**: simplesc (C) → NASM → ld (i686)
- **Sandbox**: Docker com cap-drop=ALL, read-only, network=none
- **Infra**: Nginx reverse proxy, Docker Compose, CI/CD com GitHub Actions

---

## Slide 4 — Funcionalidades Principais

| Funcionalidade | Status |
|---|---|
| Editor Monaco com syntax highlight (27 keywords) | ✅ |
| Tema dark customizado (simples-dark) | ✅ |
| Layout 3 painéis resizable (editor, NASM, terminal) | ✅ |
| Compilador SIMPLES → NASM (via REST) | ✅ |
| Erros como Monaco markers (linha sublinhada) | ✅ |
| Execução interativa com `leia` (WebSocket + PTY) | ✅ |
| Sandbox seguro (sem rede, read-only, cap-drop) | ✅ |
| Rate limiting (30 exec/min) | ✅ |
| Logs estruturados JSON + métricas Prometheus | ✅ |
| Deploy Oracle Cloud Ampere A1 | 🔄 |

---

## Slide 5 — Demo ao Vivo

**Roteiro da demo (2-3 min)**:

1. Abrir http://simples.example.edu.br
2. Login com Supabase Auth
3. Digitar programa SIMPLES com `leia`:
   ```
   programa
   inicio
     inteiro x
     leia x
     escreva "O dobro e: "
     escreval x * 2
   fim
   ```
4. Clicar **Run** → ver NASM no painel direito
5. Interagir no terminal: digitar valor, ver resultado
6. Mostrar erro: esquecer `fim` → ver marker vermelho
7. (Opcional) Mostrar `/metrics` (Prometheus)

---

## Slide 6 — Engenharia de Software

**Processo**:
- 6 Sprints de 1-2 semanas
- GitHub Projects (Kanban) com labels por sprint
- PR flow: branch → commit → PR → code review → CI → merge
- Code review rigoroso com "Changes Requested"

**CI/CD** (GitHub Actions):
- `frontend`: npm ci → lint → build → test
- `backend`: pip install → flake8 → pytest
- `docker-stack`: docker compose build
- `smoke`: compose up → healthcheck → tear down

**Cobertura**: 27 PRs, 15+ issues fechadas

---

## Slide 7 — Desafios Tecnicos

| Desafio | Solucao |
|---|---|
| Healthcheck incompativel (Alpine vs Ubuntu) | curl no Ubuntu, sem healthcheck no Alpine |
| Merge conflicts massivos (7 arquivos) | Merge atomico local, revisao sistematica |
| Vite vs CRA (porta, output dir) | Configuracao explicita no compose override |
| Linker 32-bit (i686) | binutils-i686-linux-gnu no Dockerfile |
| WebSocket bidirecional stdin/stdout | GeventWebSocketWorker + PTY bridge |
| Timeout e seguranca do sandbox | cap-drop, read-only, cgroups, rate limit |

---

## Slide 8 — Licoes Aprendidas

- **Testes cedo**: Configurar lint e testes na Sprint 1 evita correria
- **Compatibilidade de imagens**: Alpine != Ubuntu — testar healthchecks em todas as bases
- **Code review salva vidas**: Revisoes pegaram YAML quebrado, paths errados, framework mismatch
- **CI/CD e iterativo**: Cada push revela um novo problema — resolver um por vez
- **Documentacao e paralelismo**: SPRINTS.md e specs de design permitiram trabalho assincrono

---

## Slide 9 — Conclusao

O **Simples Editor** entrega:

- Editor de codigo completo no navegador
- Compilacao e execucao interativa com seguranca de sandbox
- CI/CD automatizado com 4 jobs paralelos
- Pronto para deploy em producao (Oracle Cloud Ampere A1)

**Tecnologias**: React, Flask, Docker, GitHub Actions, Supabase, xterm.js, Monaco Editor, NASM, QEMU

**Obrigado! Perguntas?**
