import { Client } from '@modelcontextprotocol/client'
import { StdioClientTransport } from '@modelcontextprotocol/client/stdio'

const transport = new StdioClientTransport({ command: 'node', args: ['build/server.js'], stderr: 'pipe', env: { ...process.env, ORANGE_PET_BRIDGE_PORT: '0' } })
const client = new Client({ name: 'orange-spirit-smoke', version: '1.0.3' })
await client.connect(transport)
const tools = await client.listTools()
const names = tools.tools.map(tool => tool.name).sort()
const required = ['orange_pet_hide', 'orange_pet_play_action', 'orange_pet_set_state', 'orange_pet_show', 'orange_pet_speak', 'orange_pet_status']
if (JSON.stringify(names) !== JSON.stringify(required)) throw new Error(`tool list mismatch: ${names}`)
const noBrowser = await client.callTool({ name: 'orange_pet_play_action', arguments: { action: 'Mischief' } })
if (noBrowser.isError) throw new Error(`Mischief rejected: ${noBrowser.content.find(block => block.type === 'text')?.text || 'unknown MCP error'}`)
const noBrowserResult = JSON.parse(noBrowser.content.find(block => block.type === 'text')?.text || '{}')
if (noBrowserResult.ok !== false || noBrowserResult.warning !== 'no_browser_connected') throw new Error(`zero-browser delivery must be explicit: ${JSON.stringify(noBrowserResult)}`)
for (const [name, args] of [
  ['orange_pet_speak', { text: '你好，我是橙子精灵。' }],
  ['orange_pet_set_state', { state: 'thinking' }],
  ['orange_pet_show', {}],
  ['orange_pet_hide', {}],
  ['orange_pet_status', {}],
]) {
  const result = await client.callTool({ name, arguments: args })
  if (result.isError) throw new Error(`${name} failed`)
}
console.log(JSON.stringify({ status: 'PASS', tools: names }, null, 2))
await client.close()
