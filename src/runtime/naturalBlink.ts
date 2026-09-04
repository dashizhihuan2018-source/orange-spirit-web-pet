import type { WebPetState } from '../contracts'

type NaturalBlinkSchedulerOptions = {
  schedule(callback: () => void, delayMs: number): number
  cancel(handle: number): void
  delay(): number
  canBlink(): boolean
  blink(): void
}

export function canUseNaturalBlink({ state, activeActionName, hasBlinkAction, reducedMotion, visible = true }: {
  state: WebPetState
  activeActionName?: string
  hasBlinkAction: boolean
  reducedMotion: boolean
  visible?: boolean
}) {
  return visible && state === 'idle' && activeActionName === 'Idle' && hasBlinkAction && !reducedMotion
}

export function createNaturalBlinkScheduler({ schedule, cancel, delay, canBlink, blink }: NaturalBlinkSchedulerOptions) {
  let running = false
  let pending: number | undefined

  const register = () => { pending = schedule(tick, delay()) }
  const tick = () => {
    pending = undefined
    if (!running) return
    if (canBlink()) blink()
    if (running) register()
  }

  return {
    start() {
      if (running) return
      running = true
      register()
    },
    stop() {
      running = false
      if (pending !== undefined) cancel(pending)
      pending = undefined
    },
  }
}
