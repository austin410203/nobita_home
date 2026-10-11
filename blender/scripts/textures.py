# Procedural, tileable PBR textures (albedo + normal) generated with numpy, saved as JPG.
import bpy, os
import numpy as np

TEXDIR = os.path.join(os.path.dirname(LIB), "..", "textures")
TEXDIR = os.path.abspath(TEXDIR)
os.makedirs(TEXDIR, exist_ok=True)

def _freq(n):
    f = np.fft.fftfreq(n) * n
    return f[None, :], f[:, None]

def noise(n, sx, sy=None, seed=0):
    """Tileable gaussian-filtered noise, zero mean / unit std. sx, sy = cutoff in cycles per tile."""
    sy = sx if sy is None else sy
    r = np.random.default_rng(seed)
    F = np.fft.fft2(r.standard_normal((n, n)))
    fx, fy = _freq(n)
    F *= np.exp(-(fx / sx) ** 2 - (fy / sy) ** 2)
    o = np.real(np.fft.ifft2(F))
    return (o - o.mean()) / (o.std() + 1e-9)

def fbm(n, seed, octaves=((4, .5), (16, .3), (64, .15), (200, .05))):
    return sum(w * noise(n, s, seed=seed + i) for i, (s, w) in enumerate(octaves))

def lerp(a, b, t):
    a = np.asarray(a, np.float32); b = np.asarray(b, np.float32)
    return a + (b - a) * np.clip(t, 0, 1)[..., None]

def grid(n, nx, ny):
    y, x = np.mgrid[0:n, 0:n] / n
    return x, y

def normal_from_height(h, k):
    dx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * k
    dy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * k
    nrm = np.dstack((-dx, -dy, np.ones_like(h)))
    nrm /= np.linalg.norm(nrm, axis=2, keepdims=True)
    return nrm * 0.5 + 0.5

def save(name, rgb, data=False):
    n = rgb.shape[0]
    img = bpy.data.images.get("tex_" + name)
    if img: bpy.data.images.remove(img)
    img = bpy.data.images.new("tex_" + name, n, n, alpha=False)
    if data:
        img.colorspace_settings.name = "Non-Color"
    px = np.ones((n, n, 4), np.float32)
    px[..., :3] = np.clip(rgb, 0, 1)
    img.pixels.foreach_set(px.ravel())
    path = os.path.join(TEXDIR, name + ".jpg")
    img.filepath_raw = path
    img.file_format = "JPEG"
    try:
        img.save(filepath=path, quality=92)
    except TypeError:
        img.save()
    bpy.data.images.remove(img)

def out(name, col, h, k=4.0):
    save(name + "_col", col)
    save(name + "_nrm", normal_from_height(h, k), data=True)

def tiles(n, nx, ny, grout, offset=False, seed=0):
    """returns (mask of grout 0..1, per-tile random id field)"""
    x, y = grid(n, nx, ny)
    row = np.floor(y * ny)
    xs = x * nx + (0.5 * (row % 2) if offset else 0)
    col = np.floor(xs) % nx
    fx = xs - np.floor(xs); fy = y * ny - row
    gx = grout * nx / n; gy = grout * ny / n
    edge = np.minimum(np.minimum(fx, 1 - fx) / gx, np.minimum(fy, 1 - fy) / gy)
    mask = 1 - np.clip(edge, 0, 1)            # 1 in grout
    rnd = np.random.default_rng(seed).random((ny, nx + 1))
    tid = rnd[row.astype(int), col.astype(int)]
    bevel = np.clip(edge, 0, 1) ** 0.5         # rounded tile edges for height
    return mask, tid, bevel

N = 1024

# ---- wood flooring: 10 planks per 1.2 m tile, grain along U ----
def wood_planks():
    x, y = grid(N, 1, 1)
    planks = 10
    row = np.floor(y * planks).astype(int)
    r = np.random.default_rng(3)
    tint = r.uniform(-0.12, 0.12, planks)[row]
    joint = r.random(planks)[row]
    warp = noise(N, 3, 12, 5) * 0.8
    grain = np.sin(2 * np.pi * (y * 60 + warp)) * 0.5 + 0.5
    fib = noise(N, 2, 300, 6)
    t = 0.35 * grain + 0.15 * fib + tint + 0.4
    col = lerp((0.68, 0.45, 0.26), (0.42, 0.25, 0.13), t)
    fy = y * planks - np.floor(y * planks)
    seam = np.minimum(fy, 1 - fy) < 0.02
    fx = (x - joint) % 1.0
    jseam = np.minimum(fx, 1 - fx) < 0.0025
    s = seam | jseam
    col[s] *= 0.45
    h = 0.2 * fib + 0.1 * grain
    h[s] -= 1.0
    out("wood_floor", col, h, 3)

def wood_grain(name, light, dark, seed):
    x, y = grid(N, 1, 1)
    warp = noise(N, 2, 8, seed) * 1.2
    grain = np.sin(2 * np.pi * (y * 30 + warp)) * 0.5 + 0.5
    fib = noise(N, 2, 250, seed + 1)
    col = lerp(light, dark, 0.45 * grain ** 2 + 0.15 * fib + 0.25)
    out(name, col, 0.15 * fib + 0.05 * grain, 2)

def tatami():
    x, y = grid(N, 1, 1)
    strands = 220
    s = np.abs(np.sin(np.pi * y * strands))
    rowvar = np.random.default_rng(8).uniform(-0.12, 0.12, strands)[np.floor(y * strands).astype(int) % strands]
    warp = (np.abs(np.sin(np.pi * x * 45)) < 0.12)  # stitch threads
    n = noise(N, 6, seed=9)
    t = 0.45 + rowvar + 0.08 * n + 0.15 * (1 - s)
    col = lerp((0.74, 0.74, 0.50), (0.55, 0.60, 0.33), t)
    col[warp] *= 0.85
    h = s ** 0.5 - 0.3 * warp
    out("tatami", col, h, 3)

def plaster(name, c1, c2, seed, rough_amp=1.0):
    n = fbm(N, seed)
    fine = noise(N, 300, seed=seed + 7)
    col = lerp(c1, c2, 0.5 + 0.25 * n + 0.08 * fine)
    out(name, col, rough_amp * (0.6 * n + 0.4 * fine), 2.5)

def roof_tile():
    n = fbm(N, 20, ((3, .6), (12, .3), (80, .1)))
    speck = noise(N, 400, seed=21) > 2.2
    col = lerp((0.78, 0.26, 0.18), (0.50, 0.13, 0.09), 0.5 + 0.3 * n)
    col[speck] *= 0.8
    out("roof_tile", col, 0.3 * n, 1.5)

def block():
    mask, tid, bev = tiles(N, 2, 4, 12, offset=True, seed=30)
    n = fbm(N, 31)
    pits = noise(N, 300, seed=32)
    col = lerp((0.66, 0.67, 0.70), (0.52, 0.53, 0.57), 0.5 + 0.2 * n + 0.2 * (tid - 0.5))
    col = lerp(col, (0.76, 0.75, 0.72), mask)
    h = bev * 1.0 + 0.1 * pits
    out("block", col, h, 4)

def concrete():
    n = fbm(N, 40)
    pits = noise(N, 350, seed=41)
    col = lerp((0.66, 0.66, 0.64), (0.48, 0.48, 0.47), 0.5 + 0.25 * n)
    col[pits > 2.3] *= 0.7
    out("concrete", col, 0.3 * n + 0.1 * pits, 2)

def tile_floor(name, nx, grout, c1, c2, cg, seed):
    mask, tid, bev = tiles(N, nx, nx, grout, seed=seed)
    n = fbm(N, seed + 1)
    col = lerp(c1, c2, 0.4 + 0.2 * n + 0.3 * (tid - 0.5))
    col = lerp(col, cg, mask)
    out(name, col, bev + 0.05 * n, 5)

def granite(name, c1, c2, seed):
    n = fbm(N, seed)
    sp = noise(N, 450, seed=seed + 3)
    col = lerp(c1, c2, 0.5 + 0.2 * n + 0.25 * np.tanh(sp))
    col[sp > 2.0] = (0.2, 0.2, 0.2)
    out(name, col, 0.3 * n + 0.1 * sp, 2)

def asphalt():
    n = fbm(N, 50)
    sp = noise(N, 500, seed=51)
    col = lerp((0.22, 0.22, 0.23), (0.12, 0.12, 0.13), 0.5 + 0.2 * n + 0.3 * np.tanh(sp))
    col[sp > 1.8] = (0.45, 0.44, 0.42)
    out("asphalt", col, 0.4 * sp, 3)

def grass():
    n = fbm(N, 60)
    blades = noise(N, 400, 120, 61) + noise(N, 120, 400, 62)
    col = lerp((0.38, 0.58, 0.20), (0.16, 0.34, 0.10), 0.5 + 0.25 * n + 0.15 * blades)
    out("grass", col, 0.5 * blades, 2)

def fabric(name, c, seed, f=110):
    x, y = grid(N, 1, 1)
    a = np.sin(2 * np.pi * x * f); b = np.sin(2 * np.pi * y * f)
    weave = 0.5 + 0.5 * np.where(np.sin(np.pi * x * f) * np.sin(np.pi * y * f) > 0, a, b)
    n = noise(N, 8, seed=seed)
    c = np.asarray(c, np.float32)
    col = lerp(c * 1.08, c * 0.8, 0.5 + 0.3 * (weave - 0.5) + 0.1 * n)
    out(name, col, weave, 1.5)

def paper():
    n = fbm(N, 70)
    fib = noise(N, 30, 300, 71) + noise(N, 300, 30, 72)
    col = lerp((0.96, 0.95, 0.90), (0.86, 0.84, 0.78), 0.4 + 0.15 * n + 0.08 * fib)
    out("paper", col, 0.2 * fib, 1)

def bark():
    n = noise(N, 60, 4, 80) + 0.4 * noise(N, 200, 10, 81)
    col = lerp((0.45, 0.33, 0.22), (0.20, 0.13, 0.08), 0.5 + 0.3 * n)
    out("bark", col, n, 4)

def leaf():
    n = fbm(N, 90, ((10, .5), (40, .35), (150, .15)))
    col = lerp((0.42, 0.62, 0.24), (0.10, 0.28, 0.08), 0.5 + 0.35 * n)
    out("leaf", col, n, 4)

def paint(name, c, seed):
    x, y = grid(N, 1, 1)
    g = np.sin(2 * np.pi * (y * 25 + noise(N, 2, 8, seed) * 1.0)) * 0.5 + 0.5
    n = noise(N, 6, seed=seed + 1)
    c = np.asarray(c, np.float32)
    col = lerp(c * 1.05, c * 0.88, 0.5 + 0.2 * g + 0.15 * n)
    out(name, col, 0.15 * g, 1)

wood_planks()
wood_grain("wood_light", (0.80, 0.62, 0.42), (0.58, 0.40, 0.24), 100)
wood_grain("wood_dark", (0.50, 0.33, 0.20), (0.28, 0.17, 0.09), 110)
tatami()
plaster("plaster_ext", (0.95, 0.91, 0.80), (0.84, 0.79, 0.66), 120)
plaster("plaster_int", (0.94, 0.91, 0.85), (0.86, 0.82, 0.74), 130, 0.5)
plaster("ceiling", (0.97, 0.96, 0.93), (0.90, 0.89, 0.85), 140, 0.4)
roof_tile(); block(); concrete(); asphalt(); grass(); paper(); bark(); leaf()
tile_floor("tile_white", 3, 6, (0.90, 0.89, 0.85), (0.80, 0.79, 0.75), (0.65, 0.65, 0.62), 150)
tile_floor("tile_blue", 4, 5, (0.62, 0.78, 0.90), (0.48, 0.66, 0.82), (0.92, 0.92, 0.92), 160)
tile_floor("stone_tile", 2, 6, (0.66, 0.64, 0.60), (0.52, 0.50, 0.47), (0.40, 0.39, 0.37), 170)
granite("stone", (0.70, 0.68, 0.64), (0.50, 0.49, 0.46), 180)
fabric("fabric_green", (0.42, 0.60, 0.42), 190)
fabric("fabric_blue", (0.30, 0.48, 0.80), 191)
fabric("fabric_navy", (0.25, 0.32, 0.62), 192)
fabric("fabric_red", (0.85, 0.36, 0.32), 193)
fabric("fabric_white", (0.95, 0.95, 0.93), 194)
fabric("fabric_beige", (0.80, 0.74, 0.62), 195, f=60)
fabric("fabric_tatamiedge", (0.12, 0.22, 0.14), 196, f=80)
paint("paint_red", (0.80, 0.26, 0.23), 200)
paint("paint_teal", (0.30, 0.62, 0.66), 210)
print("textures ->", TEXDIR, len(os.listdir(TEXDIR)))
