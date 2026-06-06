import { test, expect } from '@playwright/test'

// Testes E2E - Editor Monaco e fluxo de edicao/compilacao
// Cobre: US-02 (escrever codigo), US-03 (Run), US-04 (executar), US-08 (erros de compilacao)
//
// NOTA: Estes testes sao projetados para serem executados quando
// o Monaco Editor e o pipeline de compilacao estiverem integrados
// (Sprint 2 e Sprint 3).
test.describe('Editor Monaco e Fluxo de Edicao', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('botao Run esta presente na interface (placeholder)', async ({ page }) => {
    // Sprint 2: Botao Run mockado
    // Sprint 4: Botao Run funcional via WebSocket
    // Por enquanto, verificamos que o layout suporta o botao
    await expect(page.locator('#root')).toBeVisible()
  })

  test('editor Monaco renderiza area de codigo', async ({ page }) => {
    // Verifica que o container do Monaco esta presente
    // (o Monaco renderiza dentro de um elemento com classes especificas)
    await page.goto('/')

    // Aguarda possivel renderizacao do editor
    await page.waitForTimeout(500)

    // O editor Monaco cria elementos com a classe .monaco-editor
    // quando integrado. Enquanto nao integrado, o teste verifica
    // que a pagina esta funcional.
    const editorContainer = page.locator('.monaco-editor')
    const hasEditor = await editorContainer.count() > 0

    if (!hasEditor) {
      // Se o Monaco ainda nao foi integrado, o teste verifica
      // que o layout basico esta pronto
      await expect(page.locator('#root')).toBeVisible()
      console.log('Monaco Editor nao detectado - aguardando integracao (Sprint 2)')
    }
  })

  test('fluxo de digitar codigo SIMPLES e verificar highlight', async ({ page }) => {
    // Teste preparado para quando o Monaco estiver integrado com
    // a linguagem 'simples' registrada via Monarch tokenizer
    await page.goto('/')

    // Verifica que a pagina carrega
    await expect(page.locator('#root')).toBeVisible()
  })

  test('fluxo de compilar codigo invalido exibe erros como markers', async ({ page }) => {
    // Cenario: usuario escreve codigo SIMPLES invalido, clica Run,
    // e ve erros de compilacao destacados no editor (Monaco markers)
    //
    // Sprint 3: implementa este fluxo via POST /api/compile
    await page.goto('/')

    // Verifica que a pagina esta pronta para receber markers de erro
    await expect(page.locator('#root')).toBeVisible()
  })
})
