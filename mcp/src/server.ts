import { McpServer } from '@modelcontextprotocol/server'
import { serveStdio } from '@modelcontextprotocol/server/stdio'
import * as z from 'zod/v4'
import { createPetBridge } from './bridge.js'

const actions = ['Idle', 'Blink', 'Listen', 'Think', 'Speak', 'Wave', 'Celebrate', 'Error', 'Sleep', 'Bounce', 'Spin', 'Shy', 'Mischief'] as const
const states = ['idle', 'listening', 'thinking', 'speaking', 'success', 'error', 'sleeping'] as const
const bridge = createPetBridge(Number(process.env.ORANGE_PET_BRIDGE_PORT || 8765))

function result(data: Record<string, unknown>) {
  return { content: [{ type: 'text' as const, text: JSON.stringify(data) }], structuredContent: data }
}

function delivery(command: Parameters<typeof bridge.broadcast>[0]) {
  const sent = bridge.broadcast(command)
  return result({ ok: sent.deliveredTo > 0, ...sent, warning: sent.deliveredTo ? null : 'no_browser_connected' })
}

export function createOrangeSpiritServer() {
  const server = new McpServer({ name: 'orange-spirit-web-pet', version: '1.0.3' }, { instructions: 'Use orange_pet_play_action for gestures, orange_pet_speak for visible and audible replies, and orange_pet_status to inspect browser delivery.' })
  server.registerTool('orange_pet_play_action', { description: 'Play one named Orange Spirit animation in the connected webpage.', inputSchema: z.object({ action: z.enum(actions) }), annotations: { readOnlyHint: false, destructiveHint: false, idempotentHint: false, openWorldHint: false } }, async ({ action }) => delivery({ type: 'action', action }))
  server.registerTool('orange_pet_speak', { description: 'Show text and speak it through the connected Orange Spirit webpage.', inputSchema: z.object({ text: z.string().trim().min(1).max(500) }), annotations: { readOnlyHint: false, destructiveHint: false, idempotentHint: false, openWorldHint: false } }, async ({ text }) => delivery({ type: 'speak', text }))
  server.registerTool('orange_pet_set_state', { description: 'Set the Orange Spirit interaction state and matching animation.', inputSchema: z.object({ state: z.enum(states) }), annotations: { readOnlyHint: false, destructiveHint: false, idempotentHint: true, openWorldHint: false } }, async ({ state }) => delivery({ type: 'state', state }))
  server.registerTool('orange_pet_show', { description: 'Show the Orange Spirit panel.', annotations: { readOnlyHint: false, destructiveHint: false, idempotentHint: true, openWorldHint: false } }, async () => delivery({ type: 'show' }))
  server.registerTool('orange_pet_hide', { description: 'Hide the Orange Spirit panel.', annotations: { readOnlyHint: false, destructiveHint: false, idempotentHint: true, openWorldHint: false } }, async () => delivery({ type: 'hide' }))
  server.registerTool('orange_pet_status', { description: 'Read local browser connection and last-command status.', annotations: { readOnlyHint: true, destructiveHint: false, idempotentHint: true, openWorldHint: false } }, async () => result({ ok: true, ...bridge.status() }))
  return server
}

await bridge.listen()
const handle = serveStdio(createOrangeSpiritServer)
console.error('Orange Spirit MCP V1.0.3 listening on stdio; bridge http://127.0.0.1:8765')
for (const signal of ['SIGINT', 'SIGTERM'] as const) process.on(signal, () => { void bridge.close().finally(() => handle.close()) })
