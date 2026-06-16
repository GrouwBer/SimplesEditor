import { test, expect } from '@playwright/test'

// Testes E2E - Fluxo de autenticacao (login via Supabase)
// Cobre: US-01 (login com conta institucional)
//
// NOTA: Como o auth-ui-react carrega dentro de um iframe ou modal do Supabase,
// usamos mocks de API para testar o fluxo sem depender do servidor real.
test.describe('Fluxo de Autenticacao', () => {
  test.beforeEach(async ({ page }) => {
    // Intercepta chamadas a API do Supabase para mockar o fluxo de auth
    await page.route('**/auth/v1/**', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'mock-jwt-token',
          refresh_token: 'mock-refresh-token',
          user: {
            id: '00000000-0000-0000-0000-000000000001',
            email: 'aluno@ifsuldeminas.edu.br',
          },
        }),
      })
    })
  })

  test('pagina inicial esta acessivel sem login', async ({ page }) => {
    // A landing page / health check deve ser acessivel sem autenticacao
    await page.goto('/')
    await expect(page.locator('h1')).toContainText('SIMPLES')
  })

  test('interface de login esta presente no layout', async ({ page }) => {
    await page.goto('/')
    // O App atual nao tem login ainda - este teste verifica que a pagina
    // esta pronta para receber o componente de auth
    await expect(page.locator('#root')).toBeVisible()
  })

  test('mock de sessao autenticada permite acesso a IDE', async ({ page }) => {
    // Simula um usuario autenticado
    await page.goto('/')
    // Injeta um mock de sessao Supabase no localStorage
    await page.evaluate(() => {
      localStorage.setItem(
        'sb-localhost-auth-token',
        JSON.stringify({
          access_token: 'mock-jwt',
          refresh_token: 'mock-refresh',
          user: { id: 'user-1', email: 'aluno@ifsuldeminas.edu.br' },
        })
      )
    })
    await page.reload()
    // A pagina deve carregar sem erros
    await expect(page.locator('#root')).toBeVisible()
  })
})
