# Robotics Widgets

Interactive HTML widgets for the Ultimate Robotics Handbook. Each widget is a single self-contained `index.html` with no build step.

## Layout

```
widgets/
  index.html           # gallery page
  kalman-1d/index.html
  path-grid/index.html
  arm-2dof/index.html
  quat-converter/index.html
  pid-cartpole/index.html
  icp-stepper/index.html
  rrt-star/index.html
  dh-3dof/index.html
  ekf-2d/index.html
  ros2-qos/index.html
```

## Local preview

```bash
cd widgets
python3 -m http.server 8000
# open http://localhost:8000
```

## Deploy to Netlify

The widgets are static — any static host works.

### Option A: Drag-and-drop (one-off)

1. Go to https://app.netlify.com/drop
2. Drag the `widgets/` folder onto the page
3. Netlify gives you a URL like `https://random-name.netlify.app`
4. Rename the site to `panav` in the site settings → final URL is `https://panav.netlify.app`

### Option B: Git-backed (recommended)

1. Push this repo to GitHub
2. In Netlify: **Add new site → Import from Git → pick the repo**
3. Build settings:
   - **Base directory:** `widgets`
   - **Build command:** *(leave empty)*
   - **Publish directory:** `widgets`
4. Deploy. Every push to `master` will redeploy.

Once deployed, the widgets live at:

```
https://panav.netlify.app/                 # gallery
https://panav.netlify.app/kalman-1d/       # individual widget
https://panav.netlify.app/path-grid/
...
```

If you'd rather keep them under `/widgets/`, set publish directory to the repo root instead — the URLs become `https://panav.netlify.app/widgets/kalman-1d/`.

## Embedding in GitBook

GitBook understands `{% embed %}` for arbitrary URLs:

```
{% embed url="https://panav.netlify.app/widgets/kalman-1d/" %}
```

Or use a raw HTML block with an iframe if you need to control the height:

```html
<iframe src="https://panav.netlify.app/widgets/kalman-1d/"
        width="100%" height="520" frameborder="0"
        loading="lazy"></iframe>
```

Each widget is sized to fit comfortably at `width=100% height≈500px`.

## Adding a new widget

1. Create `widgets/<widget-name>/index.html`
2. Follow the shared conventions:
   - Single file, embedded `<style>` and `<script>`
   - Pin CDN versions (p5 1.9.0, three 0.160.0, mathjs 12.4.0)
   - Dark theme (`#1f1f1f` bg, `#eee` text, `#4a9eff` accent)
   - Add the footer: `Part of the Ultimate Robotics Handbook by Panav · panav.netlify.app`
   - Viewport meta tag + responsive CSS
3. Add a card to `widgets/index.html`
4. Commit and push — Netlify redeploys automatically

## Conventions

- **No build step.** If you find yourself reaching for webpack, stop — pick a different file format.
- **No external assets.** Inline SVG, CSS gradients, or CDN-hosted libraries only.
- **Math is right.** Check the algorithm against a reference before publishing. Better to ship five correct widgets than ten that drift.
- **Mobile-first.** Test in DevTools at 360px wide; sliders and canvases must adapt.
