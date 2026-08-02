import os, math, random
from PIL import Image, ImageDraw, ImageFilter, ImageChops

# ---------------------------------------------------------------- config
FPS      = 24
SCENE    = 4.5           # seconds each machine is on screen
FADE     = 1.2           # crossfade duration
IMGDIR   = "/home/claude/out/images"

MACHINES = [
    ("snack-machine-hero.png",               1.00),
    ("coffee-bean-to-cup-hero-feathered.png", 1.02),
    ("smoothie-machine.png",                 1.00),
]

NAVY_TOP  = (5, 14, 26)
NAVY_MID  = (10, 32, 54)
TEAL      = (34, 211, 238)


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(len(a)))


def ease(t):
    """smootherstep"""
    t = max(0.0, min(1.0, t))
    return t * t * t * (t * (t * 6 - 15) + 10)


# ---------------------------------------------------------------- layers
def make_background(W, H):
    """Deep navy radial-ish gradient base."""
    base = Image.new("RGB", (W, H), NAVY_TOP)
    d = ImageDraw.Draw(base)
    for y in range(H):
        t = y / (H - 1)
        # darker at very top and bottom, lifted in the middle
        k = math.sin(math.pi * t) ** 1.3
        d.line([(0, y), (W, y)], fill=lerp(NAVY_TOP, NAVY_MID, k * 0.85))

    # warm/teal pool behind where the machine stands (right of centre)
    glow = Image.new("L", (W, H), 0)
    gd = ImageDraw.Draw(glow)
    cx, cy, r = int(W * 0.66), int(H * 0.60), int(H * 0.62)
    for i in range(46):
        f = i / 45
        gd.ellipse([cx - r * (1 - f) * 1.35, cy - r * (1 - f),
                    cx + r * (1 - f) * 1.35, cy + r * (1 - f)],
                   fill=int(150 * f * f))
    glow = glow.filter(ImageFilter.GaussianBlur(W // 22))
    tint = Image.new("RGB", (W, H), (16, 74, 96))
    base = Image.composite(ImageChops.add(base, tint), base, glow)
    return base


def make_grid(W, H, cell):
    """Tileable blueprint grid, rendered 2 cells oversize so it can drift."""
    g = Image.new("RGBA", (W + cell * 2, H + cell * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(g)
    col = (54, 128, 158, 40)
    for x in range(0, g.width, cell):
        d.line([(x, 0), (x, g.height)], fill=col, width=1)
    for y in range(0, g.height, cell):
        d.line([(0, y), (g.width, y)], fill=col, width=1)
    return g


def make_vignette(W, H, text_side=True):
    """Darkens edges; optionally lays a heavier gradient on the left for copy."""
    sw, sh = 96, 54
    small = Image.new("L", (sw, sh), 0)
    px = small.load()
    for yy in range(sh):
        for xx in range(sw):
            dx = (xx / (sw - 1) - 0.5) * 2.0
            dy = (yy / (sh - 1) - 0.5) * 2.0
            r = min(1.0, math.hypot(dx * 0.86, dy) / 1.16)
            px[xx, yy] = int(200 * (r ** 2.4))
    v = small.resize((W, H), Image.BICUBIC).filter(
        ImageFilter.GaussianBlur(W // 60))

    if text_side:
        left = Image.new("L", (W, H), 0)
        ld = ImageDraw.Draw(left)
        for x in range(W):
            t = max(0.0, 1 - x / (W * 0.55))
            ld.line([(x, 0), (x, H)], fill=int(165 * (t ** 1.5)))
        v = ImageChops.lighter(v, left)

    black = Image.new("RGBA", (W, H), (2, 8, 16, 255))
    black.putalpha(v)
    return black


def make_particles(W, H, n=70, seed=7):
    rnd = random.Random(seed)
    return [(rnd.uniform(0, W), rnd.uniform(0, H),
             rnd.uniform(0.9, 2.6), rnd.uniform(6, 22),
             rnd.uniform(0, math.tau)) for _ in range(n)]


def draw_particles(layer, pts, t, W, H):
    d = ImageDraw.Draw(layer)
    for (x, y, r, speed, ph) in pts:
        yy = (y - t * speed) % (H + 40) - 20
        xx = x + math.sin(t * 0.35 + ph) * 14
        a = int(70 + 55 * (0.5 + 0.5 * math.sin(t * 1.1 + ph)))
        d.ellipse([xx - r, yy - r, xx + r, yy + r], fill=(120, 220, 240, a))


def sweep_overlay(size, progress):
    """Diagonal specular highlight that travels across the machine."""
    w, h = size
    s = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(s)
    band = w * 0.30
    cx = -band + progress * (w + band * 2)
    for i in range(int(band)):
        f = i / band
        a = int(255 * math.sin(math.pi * f) ** 2)
        x = cx + i
        d.line([(x + h * 0.25, 0), (x - h * 0.25, h)], fill=a, width=3)
    return s.filter(ImageFilter.GaussianBlur(int(w * 0.02) + 1))


# ---------------------------------------------------------------- render
def render(W, H, outdir, machine_cx, machine_bottom, machine_h, text_side):
    os.makedirs(outdir, exist_ok=True)

    total_scene = SCENE + FADE
    duration = total_scene * len(MACHINES)
    nframes = int(round(duration * FPS))

    bg_base = make_background(W, H)
    cell = max(46, W // 34)
    grid = make_grid(W, H, cell)
    vign = make_vignette(W, H, text_side)
    pts = make_particles(W, H, n=int(W * H / 30000))

    # pre-scale each machine to its maximum on-screen size (Ken-Burns peak)
    MAXZOOM = 1.10
    prepped = []
    for fname, scale in MACHINES:
        im = Image.open(os.path.join(IMGDIR, fname)).convert("RGBA")
        target_h = int(machine_h * scale * MAXZOOM)
        target_w = int(im.width * target_h / im.height)
        prepped.append(im.resize((target_w, target_h), Image.LANCZOS))

    for f in range(nframes):
        t = f / FPS
        frame = bg_base.copy()

        # drifting grid
        ox = int((t * 9) % cell)
        oy = int((t * 6) % cell)
        frame.paste(grid, (-cell + ox, -cell + oy), grid)

        # particles
        pl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw_particles(pl, pts, t, W, H)
        pl = pl.filter(ImageFilter.GaussianBlur(1.2))
        frame = Image.alpha_composite(frame.convert("RGBA"), pl)

        # ---- which machines are visible, and at what opacity
        layers = []
        for idx in range(len(MACHINES)):
            start = idx * total_scene
            local = (t - start) % duration
            if local > duration / 2:
                local -= duration            # allows wrap-around for the loop
            if local < -FADE or local > total_scene:
                continue
            if local < 0:                    # tail of previous cycle fading in
                op = ease((local + FADE) / FADE)
            elif local < FADE:
                op = ease(local / FADE)
            elif local < SCENE:
                op = 1.0
            else:
                op = 1.0 - ease((local - SCENE) / FADE)
            if op <= 0.004:
                continue
            prog = max(0.0, min(1.0, (local + FADE) / (total_scene + FADE)))
            layers.append((idx, op, prog))

        for idx, op, prog in layers:
            src = prepped[idx]
            z = 1.0 + (MAXZOOM - 1.0) * prog          # slow push-in
            w = max(2, int(src.width * z / MAXZOOM))
            h = max(2, int(src.height * z / MAXZOOM))
            m = src.resize((w, h), Image.BILINEAR)

            # specular sweep once per scene
            sw = (prog - 0.18) / 0.42
            if 0.0 < sw < 1.0:
                shine = sweep_overlay((w, h), sw)
                shine = ImageChops.multiply(shine, m.getchannel("A"))
                hl = Image.new("RGBA", (w, h), (190, 245, 255, 0))
                hl.putalpha(shine.point(lambda v: int(v * 0.42)))
                m = Image.alpha_composite(m, hl)

            drift = math.sin(t * 0.55 + idx) * (H * 0.008)
            x = int(machine_cx - w / 2)
            y = int(machine_bottom - h + drift)

            # contact shadow / floor glow
            sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            sd = ImageDraw.Draw(sh)
            sd.ellipse([x + w * 0.05, machine_bottom - h * 0.045,
                        x + w * 0.95, machine_bottom + h * 0.055],
                       fill=(0, 0, 0, int(150 * op)))
            sh = sh.filter(ImageFilter.GaussianBlur(W // 60))
            frame = Image.alpha_composite(frame, sh)

            if op < 1.0:
                a = m.getchannel("A").point(lambda v: int(v * op))
                m = m.copy()
                m.putalpha(a)

            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            lay.paste(m, (x, y), m)
            frame = Image.alpha_composite(frame, lay)

        # vignette + copy-safe gradient
        frame = Image.alpha_composite(frame, vign)
        frame.convert("RGB").save(f"{outdir}/f{f:05d}.jpg", quality=95)

    return nframes


if __name__ == "__main__":
    import sys
    mode = sys.argv[1]
    if mode == "wide":
        n = render(1920, 1080, "/home/claude/frames_wide",
                   machine_cx=1268, machine_bottom=1012, machine_h=880,
                   text_side=True)
    else:
        n = render(1080, 1350, "/home/claude/frames_mob",
                   machine_cx=540, machine_bottom=1270, machine_h=1010,
                   text_side=False)
    print("frames:", n)
