# Three-view character sheet

Use one landscape sheet with exactly three full-body views arranged left to right: front, true right profile and back. Require an orthographic eye-level camera, identical scale, identical floor baseline, equal spacing and generous margins.

Freeze these invariants in the prompt: body proportions, number and location of appendages, facial geometry, palette and surface material. The side view must show a true profile, and the back must not invent face elements. Exclude text labels, measurement lines, perspective, three-quarter poses, ground props, watermark and extra accessories.

Accept only when all views describe one buildable object. If one view redesigns a limb, leaf, ear or face, regenerate once with that single mismatch emphasized; do not silently average contradictory views during modeling.

Prompt skeleton:

```text
Use case: stylized-concept
Asset type: strict orthographic character turnaround for Blender modeling
Primary request: one original <pet>, exactly FRONT / RIGHT SIDE / BACK
Subject: <frozen geometry and material facts>
Composition: landscape, eye-level orthographic, identical scale and floor baseline
Constraints: same identity and proportions; no perspective, three-quarter view, text, watermark, props or redesign
```
