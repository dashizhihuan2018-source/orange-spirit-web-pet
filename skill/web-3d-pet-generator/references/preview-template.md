# Bundled Preview Template

The Skill includes a self-contained static example at `assets/preview/`. It demonstrates the expected introduction page with a design sheet, mobile screenshot, rendered hero, demo recording, repeatable workflow and links back to the Skill.

Run it from the Skill directory:

```bash
python3 scripts/preview.py
```

For automated checks or when opening the browser separately:

```bash
python3 scripts/preview.py --port 5194 --no-open
```

To adapt it for a new pet, copy the entire `assets/preview/` directory into the project and replace:

- `media/three-view.png` with the approved orthographic sheet.
- `media/hero.png` with the final three-quarter render.
- `media/mobile.png` with a real 390 × 844 browser screenshot.
- `media/video-poster.png` and `media/demo.mp4` with the final action showcase.
- The character name, dimensions, action count, descriptive copy and repository link in `index.html`.
- The palette tokens at the beginning of `styles.css` so the page derives from the character rather than retaining the orange example.

Keep every asset local. Do not add CDN dependencies, credentials, internal URLs or unlicensed fonts. Verify the adapted preview at desktop and mobile widths, play the video, test every link and confirm there are no console errors or failed requests.
