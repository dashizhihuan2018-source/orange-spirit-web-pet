import { describe, expect, it } from 'vitest'
import { canUseNaturalBlink, createNaturalBlinkScheduler } from './naturalBlink'

describe('createNaturalBlinkScheduler', () => {
  it('blocks natural blink while a one-shot action is active', () => {
    expect(canUseNaturalBlink({ state: 'idle', activeActionName: 'Idle', hasBlinkAction: true, reducedMotion: false })).toBe(true)
    expect(canUseNaturalBlink({ state: 'idle', activeActionName: 'Wave', hasBlinkAction: true, reducedMotion: false })).toBe(false)
    expect(canUseNaturalBlink({ state: 'idle', activeActionName: 'Bounce', hasBlinkAction: true, reducedMotion: false })).toBe(false)
    expect(canUseNaturalBlink({ state: 'idle', activeActionName: 'Spin', hasBlinkAction: true, reducedMotion: false })).toBe(false)
    expect(canUseNaturalBlink({ state: 'idle', activeActionName: 'Shy', hasBlinkAction: true, reducedMotion: false })).toBe(false)
    expect(canUseNaturalBlink({ state: 'idle', activeActionName: 'Mischief', hasBlinkAction: true, reducedMotion: false })).toBe(false)
    expect(canUseNaturalBlink({ state: 'idle', activeActionName: 'Idle', hasBlinkAction: true, reducedMotion: true })).toBe(false)
    expect(canUseNaturalBlink({ state: 'idle', activeActionName: 'Idle', hasBlinkAction: true, reducedMotion: false, visible: false })).toBe(false)
  })

  it('blinks only when allowed and reschedules after every tick', () => {
    const scheduled: Array<() => void> = []
    let mayBlink = false
    let blinks = 0
    const scheduler = createNaturalBlinkScheduler({
      schedule: callback => { scheduled.push(callback); return scheduled.length },
      cancel: () => undefined,
      delay: () => 4_500,
      canBlink: () => mayBlink,
      blink: () => { blinks += 1 },
    })

    scheduler.start()
    expect(scheduled).toHaveLength(1)
    scheduled[0]()
    expect(blinks).toBe(0)
    expect(scheduled).toHaveLength(2)

    mayBlink = true
    scheduled[1]()
    expect(blinks).toBe(1)
    expect(scheduled).toHaveLength(3)
  })

  it('cancels its pending one-shot registration on stop', () => {
    let cancelled: number | undefined
    const scheduler = createNaturalBlinkScheduler({
      schedule: () => 42,
      cancel: handle => { cancelled = handle },
      delay: () => 4_000,
      canBlink: () => true,
      blink: () => undefined,
    })

    scheduler.start()
    scheduler.stop()

    expect(cancelled).toBe(42)
  })
})
