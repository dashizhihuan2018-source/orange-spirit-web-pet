import { afterEach, describe, expect, it } from 'vitest'
import { request } from 'node:http'
import { createPetBridge } from './bridge.js'

let bridge: ReturnType<typeof createPetBridge> | undefined
afterEach(async () => { await bridge?.close(); bridge = undefined })

describe('loopback pet bridge', () => {
  it('reports health and broadcasts a structured command', async () => {
    bridge = createPetBridge(0)
    const port = await bridge.listen()
    const health = await fetch(`http://127.0.0.1:${port}/health`).then(response => response.json())
    expect(health).toMatchObject({ ok: true, clients: 0 })
    expect(bridge.broadcast({ type: 'action', action: 'Wave' })).toMatchObject({ deliveredTo: 0 })
    expect(bridge.status().lastCommand).toMatchObject({ type: 'action', action: 'Wave' })
  })

  it('rejects non-loopback Host headers', async () => {
    bridge = createPetBridge(0)
    const port = await bridge.listen()
    const status = await new Promise<number | undefined>((resolve, reject) => {
      const req = request({ hostname: '127.0.0.1', port, path: '/health', headers: { Host: 'example.com' } }, response => {
        response.resume(); resolve(response.statusCode)
      })
      req.on('error', reject); req.end()
    })
    expect(status).toBe(403)
  })
})
