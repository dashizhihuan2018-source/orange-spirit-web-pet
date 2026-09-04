# Animation, Runtime and Floating UI Gates

## Animation pose gates

- `Blink`: keep the eyelid/eye shape visible at closure. A useful stylized target is 25–30% of open height. Confirm both eyes remain in their sockets and do not collapse toward the rig pivot.
- `Bounce`: inspect anticipation, apex, landing and recovery stills. The root must leave the ground at the apex; feet tuck instead of stretching; arms, stem and leaves follow with small delay; landing compresses and rebounds once; the last pose matches the first.
- `Mischief`: use a directional lean, asymmetric face or wink, staggered hands/leaves and a deliberate recovery. It must read differently from `Wave`, `Celebrate` and `Bounce` in a single still.
- One-shot actions must have explicit final keys for every animated control. Compare the final transform matrix with `Idle` and reject drift.
- Avoid bone scale keys by default. If squash-and-stretch is required, isolate it to approved controls and validate skin volume and export behavior.

## Runtime state machine gates

- When registering an animation mixer `finished` handler, capture or compare the finished action identity. Ignore completion events from actions that are no longer current.
- One-shot actions return to the previous persistent state or `Idle`; they never loop silently.
- Natural blink starts only while visible `Idle` is active. It does not interrupt speech, listening, explicit actions or hidden state.
- Respect `prefers-reduced-motion` for scheduled motion. Manual controls may remain available when that matches the host product contract.
- Hide/unmount cancels pending timers and listeners. Show/remount creates exactly one scheduler and one listener set.

## Floating UI gates

- Treat the rendered character bounds and control-row bounds as separate regions. The controls must not cover feet, shadow, hands or the drag target at supported viewports.
- Keep close alongside the other essential controls when the user wants a compact floating pet. Do not park it over the head or body.
- Remove decorative top and bottom bars unless the product explicitly calls for a panel. Reveal chat input on demand and place it clear of the pet.
- Test actual `getBoundingClientRect()` values in a real browser, not only CSS snapshots. Check at least the target desktop size and the smallest supported viewport.
