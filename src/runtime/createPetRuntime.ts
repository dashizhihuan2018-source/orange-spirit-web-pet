import * as THREE from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import type { PetAction, PetDefinition, WebPetMountOptions, WebPetState } from '../contracts'
import { canUseNaturalBlink, createNaturalBlinkScheduler } from './naturalBlink'
import { PET_CSS } from './styles'

type Recognition = { lang: string; interimResults: boolean; continuous: boolean; start(): void; stop(): void; onresult: ((event: any) => void) | null; onerror: (() => void) | null; onend: (() => void) | null }
const STATE_ACTION: Record<WebPetState, PetAction> = { idle: 'Idle', listening: 'Listen', thinking: 'Think', speaking: 'Speak', success: 'Celebrate', error: 'Error', sleeping: 'Sleep' }
const ONE_SHOT = new Set<PetAction>(['Blink', 'Wave', 'Celebrate', 'Error', 'Bounce', 'Spin', 'Shy', 'Mischief'])

export function shouldReturnToIdleAfterFinished(eventAction: THREE.AnimationAction, activeAction: THREE.AnimationAction | null) {
  return eventAction === activeAction && eventAction.getClip().name !== 'Sleep'
}

export function createPetRuntime(definition: PetDefinition) {
  const storage = `webpet.${definition.id}.`
  let root: HTMLElement | null = null
  let state: WebPetState = 'idle'
  let options: WebPetMountOptions | null = null
  let recorder: MediaRecorder | null = null
  let recognition: Recognition | null = null
  let chunks: Blob[] = []
  let cleanup3d: (() => void) | null = null
  let audio: HTMLAudioElement | null = null
  let eventSource: EventSource | null = null
  let actions = new Map<string, THREE.AnimationAction>()
  let activeAction: THREE.AnimationAction | null = null
  let mixer: THREE.AnimationMixer | null = null
  let motionQuery: MediaQueryList | null = null
  let motionChangeListener: (() => void) | null = null

  const bubble = (text: string) => { const el = root?.querySelector<HTMLElement>('[data-pet-bubble]'); if (el) { el.textContent = text; el.hidden = !text } }
  const playAction = (name: PetAction) => {
    const next = actions.get(name); if (!next) return false
    activeAction?.fadeOut(.18); next.stop().reset().fadeIn(.18)
    if (ONE_SHOT.has(name)) { next.setLoop(THREE.LoopOnce, 1); next.clampWhenFinished = true } else { next.setLoop(THREE.LoopRepeat, Infinity); next.clampWhenFinished = false }
    next.play(); activeAction = next
    if (root) root.dataset.lastAction = name
    root?.dispatchEvent(new CustomEvent('webpet-action', { detail: { name } }))
    return true
  }
  const setState = (next: WebPetState) => { state = next; if (root) root.dataset.state = next; root?.querySelector('[data-pet-status]')?.replaceChildren(document.createTextNode(next)); playAction(STATE_ACTION[next]) }
  const browserSpeak = (text: string) => new Promise<void>(resolve => { if (!('speechSynthesis' in window)) return resolve(); window.speechSynthesis.cancel(); const utterance = new SpeechSynthesisUtterance(text); utterance.lang = 'zh-CN'; utterance.pitch = 1.18; utterance.rate = .95; utterance.onend = () => resolve(); utterance.onerror = () => resolve(); window.speechSynthesis.speak(utterance) })
  const speak = async ({ text, audioUrl }: { text: string; audioUrl?: string }) => {
    if (!root) throw new Error('web_pet_not_mounted')
    bubble(text); setState('speaking')
    if (audioUrl) { audio = new Audio(audioUrl); await new Promise<void>(resolve => { audio!.onended = () => resolve(); audio!.onerror = () => resolve(); void audio!.play().catch(() => resolve()) }) }
    else if (options?.adapters?.synthesize) { const sound = await options.adapters.synthesize(text); if (sound.size) { audio = new Audio(URL.createObjectURL(sound)); await new Promise<void>(resolve => { audio!.onended = () => resolve(); audio!.onerror = () => resolve(); void audio!.play().catch(() => resolve()) }) } }
    else await browserSpeak(text)
    setState('idle')
  }
  const send = async (text: string) => {
    if (!options || !text.trim()) return
    setState('thinking'); bubble('嗯，让我想一想……'); let response = ''
    try {
      if (options.adapters?.chat) await options.adapters.chat(text.trim(), delta => { response += delta; bubble(response) })
      else { response = `我听到你说：“${text.trim()}”。我是${definition.name}，今天也会陪着你。`; bubble(response) }
      await speak({ text: response })
    } catch { setState('error'); bubble('抱歉，我暂时没有听清或连接失败，请再试一次。') }
  }
  const startListening = async () => {
    if (!options) return
    const Ctor = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    if (!options.adapters?.transcribe && Ctor) {
      recognition = new Ctor(); recognition!.lang = 'zh-CN'; recognition!.interimResults = false; recognition!.continuous = false
      recognition!.onresult = event => { const text = event.results?.[0]?.[0]?.transcript || ''; if (text) void send(text) }
      recognition!.onerror = () => { setState('error'); bubble('语音识别失败，请再试一次。') }
      recognition!.onend = () => { if (state === 'listening') setState('idle') }
      recognition!.start(); setState('listening'); bubble('我在听，请说吧。'); return
    }
    if (!navigator.mediaDevices?.getUserMedia || !options.adapters?.transcribe) { bubble('当前浏览器不支持语音识别，可以直接输入文字。'); return }
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true }); chunks = []; recorder = new MediaRecorder(stream)
    recorder.ondataavailable = event => chunks.push(event.data)
    recorder.onstop = async () => { stream.getTracks().forEach(track => track.stop()); setState('thinking'); try { void send(await options!.adapters!.transcribe!(new Blob(chunks, { type: recorder?.mimeType }))) } catch { setState('error') } }
    recorder.start(); setState('listening'); bubble('我在听，再点一次结束录音。')
  }
  const stopListening = () => { recognition?.stop(); recognition = null; if (recorder?.state === 'recording') recorder.stop() }
  const naturalBlink = createNaturalBlinkScheduler({
    schedule: (callback, delay) => window.setTimeout(callback, delay),
    cancel: handle => window.clearTimeout(handle),
    delay: () => 4_000 + Math.random() * 3_000,
    canBlink: () => canUseNaturalBlink({ state, activeActionName: activeAction?.getClip().name, hasBlinkAction: Boolean(root && actions.has('Blink')), reducedMotion: motionQuery?.matches === true, visible: Boolean(root && !root.hidden) }),
    blink: () => { playAction('Blink') },
  })
  const syncNaturalBlink = () => {
    if (root && !root.hidden && !motionQuery?.matches) naturalBlink.start()
    else naturalBlink.stop()
  }
  const observeMotionPreference = () => {
    motionQuery = window.matchMedia?.('(prefers-reduced-motion: reduce)') || null
    motionChangeListener = syncNaturalBlink
    motionQuery?.addEventListener('change', motionChangeListener)
    motionChangeListener()
  }
  const stopObservingMotionPreference = () => {
    if (motionQuery && motionChangeListener) motionQuery.removeEventListener('change', motionChangeListener)
    motionQuery = null
    motionChangeListener = null
  }

  const init3d = (canvas: HTMLCanvasElement, assetUrl: string) => {
    try {
      const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true }); renderer.setPixelRatio(Math.min(devicePixelRatio, 2)); renderer.setSize(280, 320, false); renderer.outputColorSpace = THREE.SRGBColorSpace
      const scene = new THREE.Scene(); const camera = new THREE.PerspectiveCamera(32, 280 / 320, .1, 100); camera.position.set(...(definition.camera || [0, .78, 3.15])); camera.lookAt(0, .70, 0)
      scene.add(new THREE.HemisphereLight(0xfff0cc, 0x4a2408, 2.1)); const key = new THREE.DirectionalLight(0xffffff, 3.2); key.position.set(-2, -3, 4); scene.add(key); const rim = new THREE.PointLight(0x9bff78, 3.2); rim.position.set(2, 1, 2); scene.add(rim)
      new GLTFLoader().load(assetUrl, gltf => { const pet = gltf.scene; pet.scale.setScalar(definition.modelScale || 1); pet.position.y = -.03; scene.add(pet); mixer = new THREE.AnimationMixer(pet); mixer.addEventListener('finished', event => { const finishedAction = (event as THREE.Event & { action?: THREE.AnimationAction }).action; if (finishedAction && shouldReturnToIdleAfterFinished(finishedAction, activeAction)) playAction('Idle') }); actions = new Map(gltf.animations.map(clip => [clip.name, mixer!.clipAction(clip)])); playAction('Idle'); root?.dispatchEvent(new CustomEvent('webpet-ready', { detail: { actions: [...actions.keys()] } })) }, undefined, () => bubble('3D 资源暂时未加载，文字与语音仍可使用。'))
      let frame = 0, previous = performance.now(); const animate = (now: number) => { const dt = Math.min((now - previous) / 1000, .05); previous = now; mixer?.update(dt); renderer.render(scene, camera); frame = requestAnimationFrame(animate) }; frame = requestAnimationFrame(animate); cleanup3d = () => { cancelAnimationFrame(frame); renderer.dispose() }
    } catch { canvas.hidden = true }
  }
  const makeDraggable = (panel: HTMLElement) => { let startX = 0, startY = 0, originX = 0, originY = 0; panel.addEventListener('pointerdown', event => { if ((event.target as HTMLElement).closest('button,input')) return; startX = event.clientX; startY = event.clientY; originX = Number(localStorage.getItem(storage + 'x') || 0); originY = Number(localStorage.getItem(storage + 'y') || 0); panel.setPointerCapture(event.pointerId) }); panel.addEventListener('pointermove', event => { if (!panel.hasPointerCapture(event.pointerId)) return; const x = originX + event.clientX - startX, y = originY + event.clientY - startY; panel.style.transform = `translate(${x}px, ${y}px)`; localStorage.setItem(storage + 'x', String(x)); localStorage.setItem(storage + 'y', String(y)) }) }

  const api = {
    async mount(next: WebPetMountOptions) {
      if (root) return; options = next; root = document.createElement('div'); root.dataset.webPetRoot = ''; root.dataset.petId = definition.id; root.dataset.state = state; root.style.setProperty('--pet-accent', definition.accent); root.style.setProperty('--pet-dark', definition.accentDark)
      root.innerHTML = `<style>${PET_CSS}</style><section class="webpet-panel" aria-label="${definition.name}桌宠"><div class="webpet-bubble" data-pet-bubble hidden></div><span class="webpet-status" data-pet-status aria-live="polite">idle</span><canvas width="280" height="320" aria-label="${definition.name}三维动画"></canvas><div class="webpet-actions" aria-label="快捷动作"><button data-action="Blink">眨眼</button><button data-action="Bounce">蹦跳</button><button data-action="Mischief">调皮</button><button data-pet-record aria-label="语音输入">●</button><button data-pet-chat aria-label="文字对话">…</button><button class="webpet-close" data-pet-hide aria-label="隐藏">×</button></div><div class="webpet-controls" hidden><input data-pet-input aria-label="消息" placeholder="${definition.placeholder}" autocomplete="off"/><button data-pet-send aria-label="发送">➜</button></div></section>`
      const panel = root.querySelector<HTMLElement>('.webpet-panel')!; panel.style.transform = `translate(${localStorage.getItem(storage + 'x') || 0}px, ${localStorage.getItem(storage + 'y') || 0}px)`; next.target.append(root); root.hidden = localStorage.getItem(storage + 'visible') === 'false'
      const controls = root.querySelector<HTMLElement>('.webpet-controls')!; const input = root.querySelector<HTMLInputElement>('[data-pet-input]')!; const submit = () => { const text = input.value; input.value = ''; controls.hidden = true; void send(text) }; input.addEventListener('keydown', event => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); submit() } }); root.querySelector('[data-pet-send]')?.addEventListener('click', submit); root.querySelector('[data-pet-chat]')?.addEventListener('click', () => { controls.hidden = !controls.hidden; if (!controls.hidden) input.focus() }); root.querySelector('[data-pet-record]')?.addEventListener('click', () => (recognition || recorder?.state === 'recording') ? stopListening() : void startListening()); root.querySelector('[data-pet-hide]')?.addEventListener('click', () => api.hide()); root.querySelectorAll<HTMLElement>('[data-action]').forEach(button => button.addEventListener('click', () => playAction(button.dataset.action as PetAction))); makeDraggable(panel)
      observeMotionPreference()
      init3d(root.querySelector('canvas')!, `${next.assetBaseUrl || '.'}/${definition.modelPath}`)
      if (next.bridgeUrl) { eventSource = new EventSource(`${next.bridgeUrl.replace(/\/$/, '')}/events`); eventSource.onmessage = event => { try { const command = JSON.parse(event.data); if (command.type === 'action') playAction(command.action); if (command.type === 'speak') void speak({ text: command.text }); if (command.type === 'state') setState(command.state); if (command.type === 'show') api.show(); if (command.type === 'hide') api.hide() } catch { /* local malformed event */ } } }
    },
    async unmount() { stopObservingMotionPreference(); naturalBlink.stop(); stopListening(); audio?.pause(); eventSource?.close(); cleanup3d?.(); root?.remove(); root = null; options = null; actions.clear(); activeAction = null; mixer = null },
    show() { if (root) root.hidden = false; localStorage.setItem(storage + 'visible', 'true'); syncNaturalBlink() }, hide() { if (root) root.hidden = true; localStorage.setItem(storage + 'visible', 'false'); syncNaturalBlink() }, setState, playAction, startListening, stopListening, speak,
  }
  return api
}
