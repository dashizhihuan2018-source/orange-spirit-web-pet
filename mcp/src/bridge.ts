import { createServer, type ServerResponse } from 'node:http'
import { randomUUID } from 'node:crypto'

export type PetCommand =
  | { id: string; type: 'action'; action: string }
  | { id: string; type: 'speak'; text: string }
  | { id: string; type: 'state'; state: string }
  | { id: string; type: 'show' | 'hide' }

export type NewPetCommand =
  | { type: 'action'; action: string }
  | { type: 'speak'; text: string }
  | { type: 'state'; state: string }
  | { type: 'show' | 'hide' }

const localHost = (host = '') => /^(127\.0\.0\.1|localhost)(:\d+)?$/.test(host)
const localOrigin = (origin = '') => !origin || /^https?:\/\/(127\.0\.0\.1|localhost)(:\d+)?$/.test(origin)

export function createPetBridge(port = 8765) {
  const clients = new Set<ServerResponse>()
  let lastCommand: PetCommand | null = null
  const server = createServer((request, response) => {
    if (!localHost(request.headers.host)) { response.writeHead(403).end('loopback_only'); return }
    const origin = request.headers.origin || ''
    if (!localOrigin(origin)) { response.writeHead(403).end('origin_denied'); return }
    if (origin) response.setHeader('Access-Control-Allow-Origin', origin)
    response.setHeader('Cache-Control', 'no-store')
    if (request.url === '/events' && request.method === 'GET') {
      response.writeHead(200, { 'Content-Type': 'text/event-stream', Connection: 'keep-alive', 'X-Accel-Buffering': 'no' })
      response.write(`event: ready\ndata: ${JSON.stringify({ pet: 'orange-spirit' })}\n\n`)
      clients.add(response); request.on('close', () => clients.delete(response)); return
    }
    if (request.url === '/health' && request.method === 'GET') {
      response.setHeader('Content-Type', 'application/json'); response.end(JSON.stringify({ ok: true, clients: clients.size, lastCommand })); return
    }
    response.writeHead(404).end('not_found')
  })
  const heartbeat = setInterval(() => { for (const client of clients) client.write(': keepalive\n\n') }, 15_000)
  return {
    async listen() { await new Promise<void>((resolve, reject) => { server.once('error', reject); server.listen(port, '127.0.0.1', resolve) }); return (server.address() as { port: number }).port },
    broadcast(command: NewPetCommand) { lastCommand = { id: randomUUID(), ...command } as PetCommand; const data = `data: ${JSON.stringify(lastCommand)}\n\n`; for (const client of clients) client.write(data); return { commandId: lastCommand.id, deliveredTo: clients.size } },
    status() { return { connectedBrowsers: clients.size, lastCommand } },
    async close() { clearInterval(heartbeat); for (const client of clients) client.end(); await new Promise<void>(resolve => server.close(() => resolve())) },
  }
}
