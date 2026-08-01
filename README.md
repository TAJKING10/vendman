# Vendman — hero video + machine image library

## 1. Video (`/video`)

All loops are **17.1 s, 24 fps, silent, seamlessly looping**. Sequence:
snack machine → bean-to-cup coffee → smoothie machine, with slow push-in,
a specular light sweep across each machine, drifting grid and particles.

| File | Use | Size |
|---|---|---|
| `vendman-hero-1920x1080.webm` | Desktop hero background (serve first) | 881 KB |
| `vendman-hero-1920x1080.mp4` | Desktop fallback — Safari / iOS | 1.7 MB |
| `vendman-hero-poster.jpg` | Poster frame, shows before video loads | 206 KB |
| `vendman-hero-mobile-1080x1350.webm` / `.mp4` | Portrait crop for phones | 856 KB / 1.4 MB |
| `vendman-hero-mobile-poster.jpg` | Mobile poster | 178 KB |
| `vendman-machine-transparent.webm` | **Alpha channel** machine loop, no background | 1.1 MB |

The left ~55% of the wide video is deliberately darkened so white hero copy
stays legible on top without an extra overlay.

**Browser note on the transparent WebM:** VP9 + alpha works in Chrome, Edge,
Firefox and Safari 16+. Older Safari ignores it and shows the `poster` image,
which is why the snippet points the poster at `snack-machine-hero.png`.

## 2. Integration

Open `vendman-hero-video.html` — it is a working page with two options:

* **Option A** — full-bleed `<video>` behind the hero, replaces your current
  background. Attributes that matter: `autoplay muted loop playsinline`.
  Without `muted` **and** `playsinline`, iOS refuses to autoplay.
* **Option B** — keeps your existing hero and swaps only
  `<img src="hero-machine.jpg">` for the transparent loop.

The inline `IntersectionObserver` script pauses the video when it scrolls out
of view, which keeps mobile battery and CPU down.

Serve the WebM before the MP4 in the `<source>` list — the browser takes the
first format it understands, so WebM-capable browsers get the smaller file.

## 3. Machine images (`/images`)

Every machine cut out of the catalogue PDF, background removed, cropped tight,
with transparency preserved. Three variants each:

* `name.png` — native resolution straight from the PDF (lossless)
* `name@2x.png` — 2× Lanczos upscale for retina layouts
* `name.webp` — 2× size, WebP, ~70% smaller than PNG — use this on the site

`_ALL-MACHINES-overview.png` is a labelled contact sheet of the whole set.
`manifest.json` lists every file with its pixel dimensions and spec caption.

### Resolution reality check

These are the **native resolutions embedded in the catalogue** — that is the
ceiling, no tool can recover detail that was never in the file:

| Asset | Native | Verdict |
|---|---|---|
| `smoothie-machine` | 1497×2222 | Excellent — print quality |
| `protein-shake-machine` | 1307×818 | Excellent |
| `snack-machine-hero` | 802×1064 | Very good |
| `coffee-bean-to-cup-hero` | 784×1120 | Very good |
| `snack-machine-36/48-selection` | ~205×420 | Thumbnail only |
| `coffee-01` … `coffee-06` | 121–256 px wide | Thumbnail only |

The six coffee models and the two spec'd snack machines were placed in the
catalogue at roughly the size they print, so they are small. They are fine as
spec-card thumbnails at ~200–300 px displayed width, but they will go soft if
you blow them up to full-width product shots.

**Ask the client for the original TCN product renders** for those eight —
TCN publishes high-res transparent PNGs for every model, and their supplier
will have them. That is a five-minute email and it is the only real fix.

Meanwhile `snack-machine-hero`, `coffee-bean-to-cup-hero`,
`protein-shake-machine` and `smoothie-machine` are all large enough to carry
the Machines and Solutions pages on their own.

## 4. Regenerating

`hero.py` renders the wide/mobile frames, `alpha.py` renders the transparent
pass, `build_imgs.py` re-extracts the image library. Change the `MACHINES`
list at the top of `hero.py` to reorder or swap what appears in the loop —
`SCENE` and `FADE` control timing.
