import { afterEach, describe, expect, it, vi } from 'vitest'
import { fireEvent } from '@testing-library/dom'
import { createWebPetPlugin } from './index'
import * as THREE from 'three'
import { shouldReturnToIdleAfterFinished } from './runtime/createPetRuntime'

const originalMatchMedia = Object.getOwnPropertyDescriptor(window, 'matchMedia')
afterEach(() => {
  document.body.innerHTML = ''
  localStorage.clear()
  vi.useRealTimers()
  if (originalMatchMedia) Object.defineProperty(window, 'matchMedia', originalMatchMedia)
  else delete (window as any).matchMedia
})

function reducedMotionMediaQuery(initial: boolean) {
  const listeners = new Set<(event: MediaQueryListEvent) => void>()
  const query = {
    matches: initial,
    media: '(prefers-reduced-motion: reduce)',
    addEventListener: vi.fn((type: string, listener: (event: MediaQueryListEvent) => void) => { if (type === 'change') listeners.add(listener) }),
    removeEventListener: vi.fn((type: string, listener: (event: MediaQueryListEvent) => void) => { if (type === 'change') listeners.delete(listener) }),
    setMatches(matches: boolean) { this.matches = matches; listeners.forEach(listener => listener({ matches } as MediaQueryListEvent)) },
  }
  Object.defineProperty(window, 'matchMedia', { value: vi.fn(() => query), configurable: true })
  return query
}

describe('createWebPetPlugin', () => {
  it('mounts once and releases its root', async () => {
    const plugin = createWebPetPlugin()
    const adapters = {
      transcribe: async () => 'hello',
      chat: async () => undefined,
      synthesize: async () => new Blob(),
    }
    await plugin.mount({ target: document.body, adapters })
    await plugin.mount({ target: document.body, adapters })
    expect(document.querySelectorAll('[data-web-pet-root]')).toHaveLength(1)
    await plugin.unmount()
    expect(document.querySelector('[data-web-pet-root]')).toBeNull()
  })

  it('cancels natural blink scheduling when unmounted', async () => {
    vi.useFakeTimers()
    const plugin = createWebPetPlugin()
    await plugin.mount({ target: document.body })
    expect(vi.getTimerCount()).toBe(1)
    await plugin.unmount()
    expect(vi.getTimerCount()).toBe(0)
  })

  it('stops natural blink while hidden, then resumes only after show', async () => {
    vi.useFakeTimers()
    const setTimeoutSpy = vi.spyOn(window, 'setTimeout')
    const clearTimeoutSpy = vi.spyOn(window, 'clearTimeout')
    const plugin = createWebPetPlugin()
    await plugin.mount({ target: document.body })
    const naturalSchedules = () => setTimeoutSpy.mock.calls.filter(([, delay]) => Number(delay) >= 4_000 && Number(delay) <= 7_000)
    expect(naturalSchedules()).toHaveLength(1)

    plugin.hide()
    expect(clearTimeoutSpy).toHaveBeenCalled()
    await vi.advanceTimersByTimeAsync(8_000)
    expect(naturalSchedules()).toHaveLength(1)

    plugin.show()
    expect(naturalSchedules()).toHaveLength(2)
    await plugin.unmount()
    expect(clearTimeoutSpy).toHaveBeenCalledTimes(2)
  })

  it('ignores stale mixer completion after a newer action becomes active', () => {
    const mixer = new THREE.AnimationMixer(new THREE.Object3D())
    const blink = mixer.clipAction(new THREE.AnimationClip('Blink', .2, []))
    const listen = mixer.clipAction(new THREE.AnimationClip('Listen', 1, []))
    const sleep = mixer.clipAction(new THREE.AnimationClip('Sleep', 1, []))

    expect(shouldReturnToIdleAfterFinished(blink, listen)).toBe(false)
    expect(shouldReturnToIdleAfterFinished(listen, listen)).toBe(true)
    expect(shouldReturnToIdleAfterFinished(sleep, sleep)).toBe(false)
  })

  it('keeps natural blink stopped for reduced motion and reacts to preference changes', async () => {
    vi.useFakeTimers()
    const query = reducedMotionMediaQuery(true)
    const plugin = createWebPetPlugin()
    await plugin.mount({ target: document.body })
    expect(vi.getTimerCount()).toBe(0)
    expect(document.querySelector<HTMLButtonElement>('[data-action="Blink"]')?.disabled).toBe(false)

    query.setMatches(false)
    expect(vi.getTimerCount()).toBe(1)
    query.setMatches(true)
    expect(vi.getTimerCount()).toBe(0)

    await plugin.unmount()
    expect(query.removeEventListener).toHaveBeenCalledTimes(1)
    query.setMatches(false)
    expect(vi.getTimerCount()).toBe(0)
  })

  it('sends text with Enter and persists visibility', async () => {
    let sent = ''
    const plugin = createWebPetPlugin()
    await plugin.mount({
      target: document.body,
      adapters: {
        transcribe: async () => 'hello',
        chat: async (text, onDelta) => { sent = text; onDelta('Hi there') },
        synthesize: async () => new Blob(),
      },
    })
    fireEvent.click(document.querySelector<HTMLElement>('[data-pet-chat]')!)
    expect(document.querySelector<HTMLElement>('.webpet-controls')?.hidden).toBe(false)
    const input = document.querySelector<HTMLInputElement>('[data-pet-input]')!
    fireEvent.input(input, { target: { value: 'status' } })
    fireEvent.keyDown(input, { key: 'Enter' })
    await new Promise(resolve => setTimeout(resolve, 0))
    expect(sent).toBe('status')
    expect(document.querySelector('[data-pet-bubble]')?.textContent).toContain('Hi there')
    plugin.hide()
    expect(localStorage.getItem('webpet.orange-spirit.visible')).toBe('false')
  })

  it('uses the Orange Spirit definition and exposes animation controls', async () => {
    const plugin = createWebPetPlugin()
    await plugin.mount({ target: document.body })
    expect(document.querySelector('[data-pet-id="orange-spirit"]')).not.toBeNull()
    expect(document.querySelector('[aria-label="橙子精灵桌宠"]')).not.toBeNull()
    expect(document.querySelector('.webpet-panel > header')).toBeNull()
    expect(document.querySelector('[data-pet-min]')).toBeNull()
    expect(document.querySelector('[data-action="Blink"]')).not.toBeNull()
    expect(document.querySelector('[data-action="Mischief"]')).not.toBeNull()
    expect([...document.querySelectorAll<HTMLElement>('[data-action]')].map(button => button.dataset.action)).toEqual(['Blink', 'Bounce', 'Mischief'])
    expect(document.querySelectorAll('.webpet-actions button')).toHaveLength(6)
    expect(document.querySelector('[data-pet-hide]')?.parentElement?.classList.contains('webpet-actions')).toBe(true)
    expect(document.querySelector<HTMLElement>('.webpet-controls')?.hidden).toBe(true)
    expect(plugin.playAction('Wave')).toBe(false)
    plugin.setState('sleeping')
    expect(document.querySelector('[data-pet-status]')?.textContent).toBe('sleeping')
  })

  it('stops browser speech recognition on the second record click', async () => {
    let stopped = 0
    class FakeRecognition {
      lang = ''; interimResults = false; continuous = false
      onresult = null; onerror = null; onend = null
      start() {}
      stop() { stopped += 1 }
    }
    Object.defineProperty(window, 'webkitSpeechRecognition', { value: FakeRecognition, configurable: true })
    const plugin = createWebPetPlugin()
    await plugin.mount({ target: document.body })
    const record = document.querySelector<HTMLElement>('[data-pet-record]')!
    fireEvent.click(record); fireEvent.click(record)
    expect(stopped).toBe(1)
    delete (window as any).webkitSpeechRecognition
  })
})
