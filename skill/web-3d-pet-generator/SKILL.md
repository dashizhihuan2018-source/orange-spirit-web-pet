---
name: web-3d-pet-generator
description: Generate, refine, preview, or release an animated 3D web desktop pet from reference art or a short character brief, including strict three-view design locking, editable Blender source, web-optimized GLB, voice interaction, a framework-neutral web plugin, a local MCP control server, a reusable introduction-page template, animation and UI QA, and an optional final-only Git snapshot. Use when the user asks to create, correct, package, preview, or publish a mascot or creature as a website desktop pet.
---

# web-3d-pet-generator

Deliver a traceable image-to-Blender-to-web pipeline. Preserve the user's supplied design exactly; when the brief is open, create one restrained original design and freeze it after the three-view sheet. User feedback overrides earlier assumptions: correct only the named mismatch and do not redesign accepted parts.

For a new project, begin with [references/getting-started.md](references/getting-started.md) and copy [templates/web-pet-release.json](templates/web-pet-release.json) into the project root.

When a user requests an introduction page, screenshots, recording or a downloadable preview, read [references/preview-template.md](references/preview-template.md) and adapt the bundled `assets/preview/` example. Do not treat its orange character or palette as a universal design requirement.

## Default production contract

- Version working outputs without overwriting earlier pets. A user-requested final-only Git release is a separate clean snapshot, never the development tree.
- Budget: at most 70,000 triangles, eight materials and 6 MB per GLB unless the host specifies otherwise.
- Stable actions: `Idle`, `Blink`, `Listen`, `Think`, `Speak`, `Wave`, `Celebrate`, `Error`, `Sleep`. Cute extensions may include `Bounce`, `Spin`, `Shy` and `Mischief`; freeze the exact action contract before web integration.
- Speech is click-to-record. Do not enable a wakeword implicitly.
- Browser bundles contain no credentials, private model weights or internal endpoints.

## Workflow

1. Write a short production brief: target, name, style, scale, poly/material/GLB budgets, animation list, voice mode and deliverable path. If the user has already specified the workflow and asked not to reconfirm, proceed without an approval pause.
2. Generate one strict orthographic `FRONT / RIGHT SIDE / BACK` sheet with the built-in image generation tool. Require identical scale, baseline, identity, colors and limb positions; no perspective, text, watermark, props or redesign between views. Read [references/character-sheet.md](references/character-sheet.md) for the prompt and acceptance gate.
3. Copy the selected sheet into the project. Write `docs/reference-analysis.md` with measured ratios, palette, visible/inferred details and prohibited additions. Record a structural signature for accepted geometry, materials and bones so animation-only or UI-only revisions can prove the model did not drift.
4. Create the Blender validator before the asset and run it once to prove missing assets fail clearly.
5. Use Blender MCP first. If the bridge is offline, record the exact connection error and execute the same `bpy` script with the verified absolute Blender binary; do not replace the model with a static mockup.
6. Build one editable scene with `COL_` collections, `SM_` meshes, `MAT_` materials, `ARM_` rig, `CAM_` cameras and `LGT_` lights. Keep one root armature and a ground-center root pivot. Model silhouette and side depth before surface detail.
7. Preserve material facts. Procedural Blender-only bumps do not count as a web deliverable: bake or generate a normal map connected to the exported PBR material, or use budgeted micro-geometry. For fruit skins, use dense irregular discrete pores with restrained roughness, not broad waves, worm-like noise or a smooth plastic sphere. For leaves and other thin organic forms, validate outline, longitudinal arch, transverse cup, thickness, root overlap and front/back vein readability from side and back views.
8. Add the stable actions as named Blender Actions, then export with glTF `ACTIONS` mode. The web runtime must call these exact names.
9. Build animation from readable key poses, not only timeline playback. A blink compresses each eye to a visible thin shape rather than scaling it away; use pivot/position compensation if compression pulls the eye inward. A bounce needs anticipation, airborne separation, foot tuck, secondary follow-through, landing cushion, rebound and exact recovery. Mischief needs a clear asymmetric prepare, wink or tease, staggered secondary motion and exact recovery. Avoid scale keys on the character rig unless the design explicitly requires squash-and-stretch. Read [references/animation-runtime-ui.md](references/animation-runtime-ui.md).
10. Run three visual passes: (1) silhouette/scale/limb anchors, (2) face/side/back/secondary forms, (3) color/material/texture/action intersections. Save each pass and a gap log in the development workspace; apply only targeted fixes. Compare front/right/back plus decisive action frames and rerun the structural signature after animation-only changes.
11. Export `.blend`, `.glb`, front/right/back/three-quarter stills and an H.264 action showcase. Reimport or parse the GLB to verify clips, exact action set, materials, triangles, bounds and embedded textures.
12. Package a framework-neutral `createWebPetPlugin(definition)` API with mount/unmount, drag, show/hide, state-to-action mapping, `playAction`, `speak`, start/stop listening, reduced motion and preference persistence. Guard action completion with the action identity so a stale `finished` event cannot cancel a newer action. Schedule natural blinking only while the pet is visible and idle; pause it for reduced motion and reset timers on hide/show.
13. Keep a floating pet visually light: avoid full-width top/bottom chrome unless requested. Place essential controls outside the character canvas and foot silhouette, including the close button; hide secondary input until invoked. Verify button and model bounding boxes at the real target viewport.
14. Provide two voice paths: Web Speech Recognition plus SpeechSynthesis for a no-key demo, and optional host-owned `transcribe/chat/synthesize` adapters for private services. Disclose that browser speech recognition depends on browser/platform support.
15. Build a loopback-only MCP stdio server plus SSE bridge. Expose narrowly scoped action, speak, state, show, hide and status tools. Bind the bridge to `127.0.0.1`, validate Host/Origin and keep stdout reserved for JSON-RPC.
16. Write `web-pet-release.json` with the release version, exact action list and every required source/public/dist GLB copy. Use one explicit versioned filename consistently; do not retain an unversioned duplicate beside it. Run `scripts/validate_delivery.py`, model validation, unit tests, production build, MCP protocol smoke and a real-browser load with console inspection. Deliver a versioned folder with a SHA-256 manifest.
17. If an introduction page is in scope, copy the bundled preview, replace every example asset and character-specific field, and validate desktop/mobile layout, local media loading, video playback and link targets in a real browser.
18. If and only if the user explicitly requests a final-only Git publication, follow [references/final-only-git-release.md](references/final-only-git-release.md). Build a new clean snapshot containing the latest source, runtime assets, reference, final QA evidence and Skill; exclude superseded versions, iteration renders, plans, research, caches and dependencies. Preserve a local bundle before replacing remote history, then publish one root commit and verify private visibility, commit count, tracked paths and remote SHA.

## Completion gate

Do not call the pet complete from a successful render or export alone. Completion requires: three-view analysis, three comparison passes, Blender and GLB validation, exact required actions, decisive-pose checks, accepted-geometry drift checks, real web loading, MCP tool discovery/calls, no console errors, non-overlapping controls, voice controls present, and a verified delivery manifest. Microphone permission and audible output may remain user-environment checks when headless automation cannot exercise hardware. A force-pushed single-commit Git branch removes visible history but does not prove the hosting provider has immediately purged unreachable objects or caches; state that boundary plainly.
