import { test, expect } from '@playwright/test'

// Testes E2E - Pagina inicial / Landing page
// Verifica que o frontend carrega corretamente e exibe o estado do backend
test.describe('Landing Page', () => {
  test('carrega a pagina inicial com o titulo SIMPLES', async ({ page }) => {
    await page.goto('/')
    await expect(page).toHaveTitle('SIMPLES Editor')
  })

  test('exibe o cabecalho e descricao do editor', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('h1')).toContainText('SIMPLES')
    await expect(page.locator('p')).toContainText('Editor de c\u00f3digo')
  })

  test('exibe o painel de status da API do backend', async ({ page }) => {
    await page.goto('/')
    const statusPanel = page.locator('text=Status da API do Backend')
    await expect(statusPanel).toBeVisible()
  })

  test('exibe o status do Sprint 1 - Foundation & DevOps', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('h3')).toContainText('Sprint 1')
  })

  test('exibe o footer com copyright', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('footer')).toContainText('SimplesEditor')
  })

  test('renderiza o indicador de status de saude (ONLINE/OFFLINE)', async ({ page }) => {
    await page.goto('/')
    // O indicador deve estar presente (pode ser ONLINE, OFFLINE, ou checking...)
    const indicator = page.locator('span').filter({ hasText: /ONLINE|OFFLINE|checking|UNEXPECTED/ })
    await expect(indicator.first()).toBeVisible()
  })
})
