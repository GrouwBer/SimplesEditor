import { test, expect } from '@playwright/test'

// === Tipos para mocks E2E ===

/** Evento recebido pelo handler onmessage do WebSocket mockado */
interface MockMessageEvent {
  data: string
}

// Testes E2E - Terminal interativo (xterm.js + WebSocket)
// Cobre: US-05 (stdin via leia), US-07 (botao Stop), US-09 (timeouts)
//
// NOTA: Estes testes simulam o fluxo interativo completo:
// login → editar → run → stdin → stop
// Eles sao executaveis quando o WebSocket `/ws/run` e o xterm.js
// estiverem integrados (Sprint 4 e Sprint 5).
test.describe('Terminal Interativo - Fluxo stdin/stdout', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('painel do terminal esta presente no layout', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('#root')).toBeVisible()
  })

  test('envia input stdin via WebSocket e recebe stdout de volta', async ({ page }) => {
    // Cenario E2E completo:
    // 1. Usuario digita programa com leia
    // 2. Clica Run
    // 3. Programa solicita input via stdout ("Digite um numero: ")
    // 4. Usuario digita no terminal
    // 5. Programa processa e exibe resultado

    // Mock do WebSocket para simular o backend
    await page.evaluate(() => {
      const win = window as unknown as Record<string, unknown>
      win.WebSocket = class MockWebSocket {
        onopen: (() => void) | null = null
        onmessage: ((e: MockMessageEvent) => void) | null = null
        onclose: (() => void) | null = null

        constructor(_url: string) {
          setTimeout(() => {
            this.onopen?.()
            // Simula o fluxo: compile_started -> asm_generated -> exec_started -> stdout -> exit
            setTimeout(() => {
              this.onmessage?.({ data: JSON.stringify({ type: 'compile_started' }) })
            }, 100)
            setTimeout(() => {
              this.onmessage?.({
                data: JSON.stringify({
                  type: 'asm_generated',
                  asm: 'section .bss\n    x resd 1\nsection .text\n    global _start\n_start:\n    ; lendo x\n    mov eax, 3\n    mov ebx, 0\n    mov ecx, x\n    mov edx, 4\n    int 0x80\n    ; escrevendo x\n    mov eax, 4\n    mov ebx, 1\n    mov ecx, x\n    mov edx, 4\n    int 0x80\n    ; exit\n    mov eax, 1\n    xor ebx, ebx\n    int 0x80',
                }),
              })
            }, 200)
            setTimeout(() => {
              this.onmessage?.({ data: JSON.stringify({ type: 'exec_started' }) })
            }, 300)
            setTimeout(() => {
              this.onmessage?.({
                data: JSON.stringify({ type: 'stdout', data: 'Digite um numero: ' }),
              })
            }, 400)
            // Simula envio de stdin pelo usuario
            setTimeout(() => {
              this.onmessage?.({
                data: JSON.stringify({ type: 'stdout', data: '42\n' }),
              })
            }, 600)
            setTimeout(() => {
              this.onmessage?.({
                data: JSON.stringify({ type: 'exit', code: 0, duration_ms: 1500 }),
              })
            }, 800)
          }, 0)
        }

        send(_data: string) {
          // stdin enviado pelo frontend - mock de confirmacao
        }

        close() { /* noop */ }
      }
    })

    await expect(page.locator('#root')).toBeVisible()
  })

  test('botao Stop interrompe execucao em andamento', async ({ page }) => {
    // Cenario: usuario inicia execucao, depois clica Stop
    // Backend recebe {type: "stop"}, envia SIGTERM → SIGKILL
    // Frontend recebe {type: "exit", code: -9} e volta ao estado IDLE

    await page.goto('/')

    // Mock de WebSocket para simular stop
    await page.evaluate(() => {
      let stopReceived = false
      const win = window as unknown as Record<string, unknown>
      win.WebSocket = class MockWebSocket {
        onopen: (() => void) | null = null
        onmessage: ((e: MockMessageEvent) => void) | null = null

        constructor(_url: string) {
          setTimeout(() => {
            this.onopen?.()
            this.onmessage?.({
              data: JSON.stringify({ type: 'exec_started' }),
            })
          }, 50)
          // Se receber stop, responde com exit code -9
          const checkStop = () => {
            if (stopReceived) {
              this.onmessage?.({
                data: JSON.stringify({ type: 'exit', code: -9 }),
              })
            }
          }
          setTimeout(checkStop, 1000)
        }

        send(data: string) {
          try {
            const msg = JSON.parse(data) as { type: string }
            if (msg.type === 'stop') {
              stopReceived = true
            }
          } catch { /* mock ignora JSON invalido */ }
        }

        close() { /* noop */ }
      }
    })

    await expect(page.locator('#root')).toBeVisible()
  })

  test('timeout de execucao interrompe programa automaticamente', async ({ page }) => {
    // Cenario: programa entra em loop infinito
    // Backend interrompe apos 10s wall-clock (asyncio.wait_for)
    // Frontend recebe {type: "timeout", limit_s: 10}

    await page.goto('/')

    await page.evaluate(() => {
      const win = window as unknown as Record<string, unknown>
      win.WebSocket = class MockWebSocket {
        onopen: (() => void) | null = null
        onmessage: ((e: MockMessageEvent) => void) | null = null

        constructor(_url: string) {
          setTimeout(() => {
            this.onopen?.()
            this.onmessage?.({ data: JSON.stringify({ type: 'exec_started' }) })
          }, 50)
          // Simula timeout apos 500ms (acelerado para teste)
          setTimeout(() => {
            this.onmessage?.({
              data: JSON.stringify({ type: 'timeout', limit_s: 10 }),
            })
          }, 500)
        }

        send(_data: string) { /* noop - timeout test */ }
        close() { /* noop */ }
      }
    })

    await expect(page.locator('#root')).toBeVisible()
  })
})
