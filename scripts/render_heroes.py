#!/usr/bin/env python3
"""Render black-studio hero stills from REAL data — no generated art.

Sources (all via the running NeuroForge API):
  - NeuroMorpho SWC reconstructions (one cell per population, the richest tree in a sample)
  - fsaverage5 pial surface (the whole-brain hero)

Output:
  frontend/public/hero/<key>.jpg      2400×1000, black studio, rim glow
  frontend/lib/heroes.json            manifest with the provenance of every still

Usage:  backend/.venv/bin/python scripts/render_heroes.py [--api http://localhost:8000]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import requests
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "frontend" / "public" / "hero"
MANIFEST = ROOT / "frontend" / "lib" / "heroes.json"

W, H = 2400, 1000
SS = 2  # supersample

# population key → sample query. The richest reconstruction (most points) of the
# first 8 results is rendered, so the still is a real cell, chosen for silhouette.
POPULATIONS: list[tuple[str, str, dict]] = [
    ("pyramidal", "/api/neurons/sample", {"region": "neocortex", "cell_type": "pyramidal", "size": 8}),
    ("purkinje", "/api/neurons/sample", {"region": "cerebellum", "cell_type": "Purkinje", "size": 8}),
    ("ca3", "/api/neurons/ca3/sample", {"size": 8}),
    ("granule", "/api/neurons/sample", {"region": "dentate gyrus", "cell_type": "granule", "size": 8}),
    ("dopaminergic", "/api/neurons/sample", {"region": "substantia nigra", "cell_type": "dopaminergic", "size": 8}),
    ("v1", "/api/neurons/v1/sample", {"size": 8}),
]


def studio_background(cx: float, cy: float) -> Image.Image:
    """Pure black with a faint radial lift around the subject and a soft floor."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - cx) / (0.75 * W)) ** 2 + ((yy - cy) / (0.75 * H)) ** 2)
    lift = np.clip(1.0 - r, 0, 1) ** 2 * 14.0  # up to +14 grey levels
    floor = np.clip((yy - 0.62 * H) / (0.5 * H), 0, 1) ** 1.6 * 10.0
    base = np.full((H, W, 3), 10.0, dtype=np.float32)  # #0A0A0B-ish
    base[..., 2] += 1.0
    img = base + (lift + floor)[..., None]
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB")


def vignette(img: Image.Image, strength: float = 0.55) -> Image.Image:
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    m = 1.0 - strength * np.clip(r - 0.55, 0, 1) ** 1.5
    a = np.asarray(img).astype(np.float32) * m[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")


def screen(base: Image.Image, layer: Image.Image) -> Image.Image:
    b = np.asarray(base).astype(np.float32) / 255.0
    l = np.asarray(layer.convert("RGB")).astype(np.float32) / 255.0
    return Image.fromarray(((1 - (1 - b) * (1 - l)) * 255).astype(np.uint8), "RGB")


def pca_project(xyz: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Project onto the plane of greatest spread; return (uv, depth) centered."""
    c = xyz - xyz.mean(axis=0)
    _, _, vt = np.linalg.svd(c, full_matrices=False)
    p = c @ vt.T  # PC1, PC2, PC3
    return p[:, :2], p[:, 2]


def render_neuron(neuron: dict, key: str) -> dict:
    pts = neuron["points"]
    by_id = {p["id"]: p for p in pts}
    xyz = np.array([[p["x"], p["y"], p["z"]] for p in pts], dtype=np.float64)
    uv, depth = pca_project(xyz)
    soma_idx = [i for i, p in enumerate(pts) if p["type"] == 1]
    # orient: soma toward the lower part of the frame, tree upward/outward
    if soma_idx and uv[soma_idx, 1].mean() < 0:
        uv[:, 1] *= -1
    # fit the SOMA + DENDRITES into a box on the left ~60% of the strip (the
    # axon may run off-frame, dimly) — the dendritic tree is the subject.
    types = np.array([p["type"] for p in pts])
    subject = np.isin(types, (1, 3, 4)) if np.isin(types, (3, 4)).sum() > 20 else np.ones(len(pts), bool)
    box_w, box_h = 0.60 * W, 0.86 * H
    lo, hi = uv[subject].min(axis=0), uv[subject].max(axis=0)
    span = hi - lo
    scale = min(box_w / max(span[0], 1e-6), box_h / max(span[1], 1e-6))
    center = (hi + lo) / 2
    ox, oy = 0.36 * W, 0.50 * H
    px = (uv[:, 0] - center[0]) * scale + ox
    py = -(uv[:, 1] - center[1]) * scale + oy
    d = (depth - depth.min()) / max(depth.max() - depth.min(), 1e-6)  # 0 back .. 1 front
    radius = np.array([p["radius"] for p in pts], dtype=np.float64)
    # line weight: real radius × scale, but never hair-thin — a 2400px still needs ≥2.2px
    r_px = np.clip(radius * scale * 1.5, 2.2, 40)
    id_to_idx = {p["id"]: i for i, p in enumerate(pts)}

    # draw supersampled: segments back-to-front
    canvas = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    segs = []
    for i, p in enumerate(pts):
        j = id_to_idx.get(p["parent_id"])
        if j is None:
            continue
        segs.append((0.5 * (d[i] + d[j]), i, j))
    segs.sort()
    for dd, i, j in segs:
        t = pts[i]["type"]
        alpha = int(255 * (0.35 + 0.65 * dd))
        if t == 2:  # axon: cool, thin, quiet
            col = (150, 172, 196, int(alpha * 0.35))
            wdt = max(1.2, 0.55 * (r_px[i] + r_px[j]) / 2)
        elif t == 1:  # soma
            col = (255, 250, 242, alpha)
            wdt = (r_px[i] + r_px[j]) / 2 * 1.4
        else:  # dendrites: warm white
            col = (255, 244, 228, alpha)
            wdt = (r_px[i] + r_px[j]) / 2 * 1.15
        w_ss = max(1, int(round(wdt * SS)))
        draw.line([(px[i] * SS, py[i] * SS), (px[j] * SS, py[j] * SS)], fill=col, width=w_ss)
        # round joints so thick branches read as tubes, not mitred sticks
        if w_ss >= 5:
            rr = w_ss / 2
            for k in (i, j):
                draw.ellipse(
                    [px[k] * SS - rr, py[k] * SS - rr, px[k] * SS + rr, py[k] * SS + rr], fill=col
                )
    # soma disc
    if soma_idx:
        sx, sy = px[soma_idx].mean(), py[soma_idx].mean()
        sr = max(float(r_px[soma_idx].max()) * 1.6, 6.0)
        draw.ellipse([(sx - sr) * SS, (sy - sr) * SS, (sx + sr) * SS, (sy + sr) * SS], fill=(255, 252, 246, 255))
    else:
        sx, sy = px.mean(), py.mean()

    lines = canvas.resize((W, H), Image.LANCZOS)
    bg = studio_background(sx, sy)
    # glow passes: wide white bloom + tight red rim on the soma
    bloom = lines.filter(ImageFilter.GaussianBlur(22))
    bloom_rgb = Image.new("RGB", (W, H), (0, 0, 0))
    bloom_rgb.paste(Image.new("RGB", (W, H), (140, 135, 130)), mask=bloom.split()[3])
    out = screen(bg, bloom_rgb)
    red = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rd = ImageDraw.Draw(red)
    rr = max(float(r_px[soma_idx].max()) * 4.5, 40.0) if soma_idx else 60.0
    rd.ellipse([sx - rr, sy - rr, sx + rr, sy + rr], fill=(225, 5, 0, 110))
    red = red.filter(ImageFilter.GaussianBlur(38))
    red_rgb = Image.new("RGB", (W, H), (0, 0, 0))
    red_rgb.paste(Image.new("RGB", (W, H), (225, 5, 0)), mask=red.split()[3])
    out = screen(out, red_rgb)
    out.paste(lines, (0, 0), lines)
    out = vignette(out)
    path = OUT_DIR / f"{key}.jpg"
    out.save(path, "JPEG", quality=88, optimize=True, progressive=True)
    return {
        "key": key,
        "file": f"/hero/{key}.jpg",
        "kind": "neuron",
        "neuron_id": neuron["neuron_id"],
        "neuron_name": neuron["neuron_name"],
        "archive": neuron["archive"],
        "species": neuron["species"],
        "brain_region": neuron["brain_region"],
        "cell_type": neuron["cell_type"],
        "point_count": neuron["point_count"],
        "doi": (neuron.get("reference_doi") or [None])[0],
        "source_url": neuron["source_url"],
        "caption": f"{neuron['neuron_name']} · {neuron['species']} · {' / '.join(neuron['brain_region'][:2])} · {neuron['archive']} archive · neuromorpho.org",
    }


def render_brain(mesh: dict) -> dict:
    """Lateral view of the left hemisphere, flat-shaded with a rim light, painter's order."""
    hemi = mesh["left"]
    v = np.array(hemi["vertices_flat"], dtype=np.float64).reshape(-1, 3)
    f = np.array(hemi["faces_flat"], dtype=np.int64).reshape(-1, 3)
    # MNI: x right, y anterior, z superior. Lateral view of the LEFT hemisphere = look from -x.
    # screen u = -y (anterior to the left), screen v = z, depth = -x (more lateral = closer)
    u, w, depth = -v[:, 1], v[:, 2], -v[:, 0]
    box_w, box_h = 0.60 * W, 0.84 * H
    span = np.array([u.max() - u.min(), w.max() - w.min()])
    scale = min(box_w / span[0], box_h / span[1])
    cu, cw = (u.max() + u.min()) / 2, (w.max() + w.min()) / 2
    px = (u - cu) * scale + 0.36 * W
    py = -(w - cw) * scale + 0.50 * H
    tri = v[f]
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-9
    # make normals face the viewer (-x)
    view = np.array([-1.0, 0.0, 0.0])
    flip = (n @ view) < 0
    n[flip] *= -1
    key_light = np.array([-0.55, 0.35, 0.75])
    key_light /= np.linalg.norm(key_light)
    rim_light = np.array([0.2, -0.9, 0.35])
    rim_light /= np.linalg.norm(rim_light)
    diff = np.clip(n @ key_light, 0, 1)
    rim = np.clip(n @ rim_light, 0, 1) ** 4
    facing = np.clip(n @ view, 0, 1)
    shade = 14 + 70 * diff ** 1.4 + 95 * rim + 8 * facing
    order = np.argsort(depth[f].mean(axis=1))  # far → near
    canvas = Image.new("RGB", (W * SS, H * SS), (0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    for i in order:
        a, b, c = f[i]
        g = int(np.clip(shade[i], 0, 255))
        col = (g, g, int(min(255, g * 1.03)))
        draw.polygon(
            [(px[a] * SS, py[a] * SS), (px[b] * SS, py[b] * SS), (px[c] * SS, py[c] * SS)],
            fill=col,
            outline=col,
        )
    # fsaverage5 is a coarse mesh (10k vertices/hemisphere): soften the facets a
    # touch so the shading reads as a surface, not a polygon count.
    shell = canvas.resize((W, H), Image.LANCZOS).filter(ImageFilter.GaussianBlur(2.2))
    bg = studio_background(0.36 * W, 0.5 * H)
    mask = Image.fromarray((np.asarray(shell).max(axis=2) > 6).astype(np.uint8) * 255, "L")
    out = bg.copy()
    out.paste(shell, (0, 0), mask)
    bloom = Image.new("RGB", (W, H), (0, 0, 0))
    bloom.paste(Image.new("RGB", (W, H), (60, 58, 56)), mask=mask.filter(ImageFilter.GaussianBlur(40)))
    out = screen(out, bloom)
    out = vignette(out, 0.5)
    path = OUT_DIR / "brain.jpg"
    out.save(path, "JPEG", quality=88, optimize=True, progressive=True)
    return {
        "key": "brain",
        "file": "/hero/brain.jpg",
        "kind": "brain",
        "vertex_count": hemi["vertex_count"],
        "face_count": hemi["face_count"],
        "caption": f"fsaverage5 pial surface · left hemisphere · {hemi['vertex_count']:,} vertices · lateral view · flat-shaded from the real mesh",
        "citation": mesh["citation"],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", default="http://localhost:8000")
    args = ap.parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest: list[dict] = []

    for key, path, params in POPULATIONS:
        r = requests.get(args.api + path, params=params, timeout=120)
        r.raise_for_status()
        results = r.json()["results"]
        if not results:
            print(f"skip {key}: no results", file=sys.stderr)
            continue
        best, best_n = None, -1
        for s in results:
            n = requests.get(f"{args.api}/api/neurons/{s['neuron_id']}", timeout=300)
            if n.status_code != 200:
                continue
            nj = n.json()
            if nj["point_count"] > best_n:
                best, best_n = nj, nj["point_count"]
        if best is None:
            print(f"skip {key}: could not fetch any SWC", file=sys.stderr)
            continue
        entry = render_neuron(best, key)
        manifest.append(entry)
        print(f"rendered {key:12s} ← {entry['neuron_name']} ({best_n} pts, {entry['archive']})")

    m = requests.get(args.api + "/api/brain/mesh", timeout=300)
    m.raise_for_status()
    manifest.append(render_brain(m.json()))
    print("rendered brain      ← fsaverage5 left hemisphere")

    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"manifest → {MANIFEST} ({len(manifest)} stills)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
