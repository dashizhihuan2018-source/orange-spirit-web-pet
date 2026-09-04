import { chromium } from 'playwright'
import { Client } from '@modelcontextprotocol/client'
import { StdioClientTransport } from '@modelcontextprotocol/client/stdio'

const bridgePort = 8767
const transport = new StdioClientTransport({ command: 'node', args: ['mcp/build/server.js'], stderr: 'pipe', env: { ...process.env, ORANGE_PET_BRIDGE_PORT: String(bridgePort) } })
const client = new Client({ name: 'orange-spirit-browser-e2e', version: '1.0.3' })
await client.connect(transport)

const browser = await chromium.launch({ headless: true, executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' })
const page = await browser.newPage({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 })
const errors = []
const failed = []
page.on('console', message => { if (message.type() === 'error') errors.push(message.text()) })
page.on('pageerror', error => errors.push(error.message))
page.on('requestfailed', request => failed.push(`${request.url()} ${request.failure()?.errorText}`))
await page.addInitScript(() => {
  class Utterance { constructor(text) { this.text = text; this.lang = ''; this.pitch = 1; this.rate = 1; setTimeout(() => this.onend?.(), 10) } }
  Object.defineProperty(window, 'SpeechSynthesisUtterance', { value: Utterance })
  Object.defineProperty(window, 'speechSynthesis', { value: { cancel() {}, speak(utterance) { setTimeout(() => utterance.onend?.(), 10) } } })
})
let modelStatus = 0
page.on('response', response => { if (response.url().endsWith('/assets/models/orange-spirit-V1.0.3.glb')) modelStatus = response.status() })
await page.goto(`${process.env.E2E_URL || 'http://127.0.0.1:5173'}/demo.html?bridge=http://127.0.0.1:${bridgePort}`, { waitUntil: 'networkidle' })
await page.locator('[data-pet-id="orange-spirit"]').waitFor()
await page.waitForTimeout(1600)
if (modelStatus !== 200) throw new Error(`orange model status ${modelStatus}`)
if (await page.locator('.webpet-panel > header').count()) throw new Error('top strip still rendered')
if (await page.locator('.webpet-actions button').count() !== 6) throw new Error('quick controls must contain exactly six buttons including close')
if (!(await page.locator('.webpet-controls').getAttribute('hidden')) && await page.locator('.webpet-controls').isVisible()) throw new Error('text input must start collapsed')
const canvasBox = await page.locator('.webpet-panel canvas').boundingBox()
const actionBox = await page.locator('.webpet-actions').boundingBox()
if (!canvasBox || !actionBox || actionBox.y < canvasBox.y + canvasBox.height) throw new Error('quick controls overlap the pet canvas')
await page.evaluate(() => {
  ;(window).orangeSpiritActions = []
  document.querySelector('[data-web-pet-root]')?.addEventListener('webpet-action', event => window.orangeSpiritActions.push(event.detail.name))
})
await page.locator('[data-pet-hide]').click()
await page.waitForTimeout(7_500)
if (await page.locator('[data-web-pet-root]').isVisible()) throw new Error('hide failed')
if (await page.evaluate(() => window.orangeSpiritActions.includes('Blink'))) throw new Error('natural blink fired while hidden')
await page.locator('#show-pet').click()
if (!(await page.locator('[data-web-pet-root]').isVisible())) throw new Error('show failed')
for (const action of ['Blink', 'Mischief']) {
  if (await page.locator(`[data-action="${action}"]`).count() !== 1) throw new Error(`missing ${action} button`)
}
await page.locator('[data-action="Blink"]').click()
await page.waitForFunction(() => document.querySelector('[data-web-pet-root]')?.getAttribute('data-last-action') === 'Blink')
await page.waitForFunction(() => document.querySelector('[data-web-pet-root]')?.getAttribute('data-last-action') === 'Idle', undefined, { timeout: 3000 })
await page.locator('[data-action="Bounce"]').click()
await page.waitForFunction(() => document.querySelector('[data-web-pet-root]')?.getAttribute('data-last-action') === 'Bounce')
await page.waitForFunction(() => document.querySelector('[data-web-pet-root]')?.getAttribute('data-last-action') === 'Idle', undefined, { timeout: 3000 })
await page.locator('[data-action="Mischief"]').click()
await page.waitForFunction(() => document.querySelector('[data-web-pet-root]')?.getAttribute('data-last-action') === 'Mischief', undefined, { timeout: 3000 })
await page.waitForFunction(() => document.querySelector('[data-web-pet-root]')?.getAttribute('data-last-action') === 'Idle', undefined, { timeout: 3000 })
let status
for (let attempt = 0; attempt < 20; attempt += 1) {
  status = await client.callTool({ name: 'orange_pet_status', arguments: {} })
  const text = status.content?.find(block => block.type === 'text')?.text || '{}'
  if (JSON.parse(text).connectedBrowsers > 0) break
  await page.waitForTimeout(50)
}
const delivered = await client.callTool({ name: 'orange_pet_play_action', arguments: { action: 'Mischief' } })
const delivery = JSON.parse(delivered.content?.find(block => block.type === 'text')?.text || '{}')
if (!delivery.ok || delivery.deliveredTo !== 1) throw new Error(`MCP delivery failed: ${JSON.stringify(delivery)}`)
await page.waitForFunction(() => document.querySelector('[data-web-pet-root]')?.getAttribute('data-last-action') === 'Mischief')
await page.waitForFunction(() => document.querySelector('[data-web-pet-root]')?.getAttribute('data-last-action') === 'Idle', undefined, { timeout: 3000 })
const speech = await client.callTool({ name: 'orange_pet_speak', arguments: { text: 'MCP 已连接橙子精灵' } })
if (!JSON.parse(speech.content?.find(block => block.type === 'text')?.text || '{}').ok) throw new Error('MCP speech delivery failed')
await page.waitForFunction(() => document.querySelector('[data-pet-bubble]')?.textContent?.includes('MCP 已连接'))
await page.locator('[data-pet-chat]').click()
await page.locator('[data-pet-input]').fill('你好')
await page.locator('[data-pet-input]').press('Enter')
await page.waitForFunction(() => document.querySelector('[data-pet-bubble]')?.textContent?.includes('橙子精灵'), undefined, { timeout: 3000 })
await page.locator('[data-pet-hide]').click()
if (await page.locator('[data-web-pet-root]').isVisible()) throw new Error('hide failed')
await page.locator('#show-pet').click()
if (!(await page.locator('[data-web-pet-root]').isVisible())) throw new Error('show failed')
await page.screenshot({ path: '/tmp/orange-spirit-browser-V1.0.3.png', fullPage: true })
await browser.close()
await client.close()
if (errors.length || failed.length) throw new Error(JSON.stringify({ errors, failed }, null, 2))
console.log(JSON.stringify({ status: 'PASS', modelStatus, screenshot: '/tmp/orange-spirit-browser-V1.0.3.png', consoleErrors: errors.length, failedRequests: failed.length }))
