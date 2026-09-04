import { createWebPetPlugin, ORANGE_SPIRIT } from './index'
const plugin = createWebPetPlugin()
await plugin.mount({ target: document.body, assetBaseUrl: location.origin, bridgeUrl: new URLSearchParams(location.search).get('bridge') || 'http://127.0.0.1:8765', adapters: {
  async chat(text, onDelta) { const answer = `嗯，收到你的问题：“${text}”。\n\n我是橙子精灵，一个可独立加载的三维桌宠。接入你的私有对话服务后，我就能回答真实业务问题。`; for (const token of answer) { onDelta(token); await new Promise(resolve => setTimeout(resolve, 14)) } },
} })
document.querySelector('#show-pet')?.addEventListener('click', () => plugin.show())
document.querySelector('#blink-pet')?.addEventListener('click', () => plugin.playAction('Blink'))
document.querySelector('#mischief-pet')?.addEventListener('click', () => plugin.playAction('Mischief'))
document.querySelector('#bounce-pet')?.addEventListener('click', () => plugin.playAction('Bounce'))
document.querySelector('#wave-pet')?.addEventListener('click', () => plugin.playAction('Wave'))
document.querySelector('#speak-pet')?.addEventListener('click', () => void plugin.speak({ text: `你好，我是${ORANGE_SPIRIT.name}！` }))
