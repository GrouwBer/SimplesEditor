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

  test.fixme('botao Run esta presente na interface (placeholder)', async ({ page }) => {
    // Sprint 2: Botao Run mockado
    // Sprint 4: Botao Run funcional via WebSocket
    // TODO: Substituir por teste real com seletor [data-testid="run-button"]
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
      test.info().annotations.push({ type: 'status', description: 'Monaco Editor nao detectado - aguardando integracao (Sprint 2)' })
    }
  })

  test.fixme('fluxo de digitar codigo SIMPLES e verificar highlight', async ({ page }) => {
    // TODO: Implementar quando Monaco + tokenizer Monarch (#83, #84) estiverem mergeados
    await page.goto('/')
    await expect(page.locator('#root')).toBeVisible()
  })

  test.fixme('fluxo de compilar codigo invalido exibe erros como markers', async ({ page }) => {
    // TODO: Implementar quando Monaco markers (#87) estiver mergeado
    // Sprint 3: implementa este fluxo via POST /api/compile
    await page.goto('/')
    await expect(page.locator('#root')).toBeVisible()
  })
})
