# Build Your Own Pet

1. Copy this Skill into the active skills directory and invoke `web-3d-pet-generator` with a character brief or reference images.
2. Replace the example name, palette, dimensions and prohibited additions in the production brief. If no strict three-view exists, generate one and freeze it before modeling.
3. Keep the nine baseline action names stable: `Idle`, `Blink`, `Listen`, `Think`, `Speak`, `Wave`, `Celebrate`, `Error`, `Sleep`. Add character-specific actions only after naming them in the release contract.
4. Copy `templates/web-pet-release.json` to the project root. Replace the version, exact action set and GLB paths. Use the same explicit versioned filename in source, public and built locations; do not retain an unversioned duplicate in a final-only release.
5. Build the editable Blender source and export the GLB. Run three comparison passes and the model validator before integrating the web runtime.
6. Reuse the framework-neutral `createWebPetPlugin(definition)` contract. Change the pet definition and assets while preserving host adapters and saved preferences.
7. Run `python3 scripts/preview.py` to inspect the bundled example. Copy `assets/preview/` into the new project, replace all example media and character-specific content, then verify it in desktop and mobile browsers.
8. Run `scripts/validate_delivery.py <project-root>`, unit tests, MCP protocol smoke and real-browser tests. Do not publish until every configured GLB has the same hash and exact action set.

The example character is not part of the generic contract. A new pet should use its own reference analysis, palette, model name, MCP tool prefix and versioned asset paths.
