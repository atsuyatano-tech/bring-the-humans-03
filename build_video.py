#!/usr/bin/env python3
"""Build the bring-the-humans-03 TikTok ad (1080x1920, 30fps, ~30s).

Kinetic-type ad for make.fun, rendered frame by frame with PIL and
assembled with ffmpeg. The score of this bounty is the video's view
count, so the cut is built for retention: a hook inside the first
second, a new visual beat at least every 1.5s, a money counter, a
meta twist (an AI agent made this ad, for a $500 bounty) and a CTA
card that loops back into the hook frame.

Audio is synthesised with numpy (128 BPM bed + riser), no samples.
Everything is deterministic: fixed seed, no wall-clock reads.
"""

import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
DURATION = 30.0
TOTAL = int(DURATION * FPS)

BG = (9, 11, 24)
BG2 = (16, 20, 44)
WHITE = (245, 247, 255)
MINT = (61, 255, 162)
MAGENTA = (255, 61, 138)
YELLOW = (255, 210, 61)
DIM = (148, 158, 190)
CARD = (22, 27, 56)

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"

HERE = os.path.dirname(os.path.abspath(__file__))
FRAMES = os.path.join(HERE, "work", "frames")
AUDIO = os.path.join(HERE, "work", "bed.wav")
OUT = os.path.join(HERE, "video", "tiktok-ad-v1.mp4")

rng = np.random.default_rng(20261122)
PARTICLES = [
    (rng.uniform(0, W), rng.uniform(0, H), rng.uniform(14, 46), rng.uniform(0.5, 1.6))
    for _ in range(46)
]


def font(path, size):
    return ImageFont.truetype(path, size)


def ease_out(t):
    return 1 - (1 - t) ** 3


def ease_in_out(t):
    return t * t * (3 - 2 * t)


def pop(t, dur=0.32):
    """Scale factor for a pop-in that starts at t=0."""
    if t <= 0:
        return 0.0
    if t >= dur:
        return 1.0
    return ease_out(t / dur)


def centered(draw, cx, y, text, fnt, fill, stroke=0, stroke_fill=(0, 0, 0)):
    box = draw.textbbox((0, 0), text, font=fnt, stroke_width=stroke)
    w = box[2] - box[0]
    draw.text((cx - w / 2 - box[0], y), text, font=fnt, fill=fill,
              stroke_width=stroke, stroke_fill=stroke_fill)
    return box[3] - box[1]


def draw_scaled(base, cx, cy, text, fnt, fill, scale, stroke=0):
    """Draw text on its own layer, scale it, paste centred at (cx, cy)."""
    if scale <= 0:
        return
    pad = 30
    tmp = Image.new("RGBA", (W, 300), (0, 0, 0, 0))
    d = ImageDraw.Draw(tmp)
    box = d.textbbox((0, 0), text, font=fnt, stroke_width=stroke)
    tw, th = box[2] - box[0], box[3] - box[1]
    d.text((pad - box[0], pad - box[1]), text, font=fnt, fill=fill + (255,),
           stroke_width=stroke, stroke_fill=(0, 0, 0, 255))
    layer = tmp.crop((0, 0, tw + 2 * pad, th + 2 * pad))
    nw = max(1, int(layer.width * scale))
    nh = max(1, int(layer.height * scale))
    layer = layer.resize((nw, nh), Image.LANCZOS)
    base.paste(layer, (int(cx - nw / 2), int(cy - nh / 2)), layer)


def background(t):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img, "RGBA")
    # slow vertical drift between the two background tones
    blend = 0.5 + 0.5 * math.sin(t * math.pi / 7.5)
    for y in range(0, H, 8):
        r = int(BG[0] + (BG2[0] - BG[0]) * blend * y / H)
        g = int(BG[1] + (BG2[1] - BG[1]) * blend * y / H)
        b = int(BG[2] + (BG2[2] - BG[2]) * blend * y / H)
        d.line([(0, y), (W, y)], fill=(r, g, b), width=8)
    # faint grid
    for x in range(0, W, 90):
        d.line([(x, 0), (x, H)], fill=(255, 255, 255, 10), width=1)
    for y in range(0, H, 90):
        d.line([(0, y), (W, y)], fill=(255, 255, 255, 10), width=1)
    # drifting particles
    for px, py, speed, size in PARTICLES:
        yy = (py - t * speed * 22) % H
        d.ellipse([px - size / 4, yy - size / 4, px + size / 4, yy + size / 4],
                  fill=(61, 255, 162, 26))
    return img


def progress_bar(d, t):
    frac = t / DURATION
    d.rounded_rectangle([60, H - 64, W - 60, H - 48], 8, fill=(255, 255, 255, 40))
    fill_w = (W - 120) * frac
    if fill_w >= 18:
        d.rounded_rectangle([60, H - 64, 60 + fill_w, H - 48], 8,
                            fill=MINT + (255,))


def chip(d, cx, cy, text, fnt, fill, outline):
    box = d.textbbox((0, 0), text, font=fnt)
    tw, th = box[2] - box[0], box[3] - box[1]
    pad_x, pad_y = 44, 26
    d.rounded_rectangle([cx - tw / 2 - pad_x, cy - th / 2 - pad_y,
                         cx + tw / 2 + pad_x, cy + th / 2 + pad_y],
                        34, fill=CARD + (255,), outline=outline + (255,), width=4)
    d.text((cx - tw / 2 - box[0], cy - th / 2 - box[1]), text, font=fnt, fill=fill)


# ---------------------------------------------------------------- scenes

def scene_hook(img, t):
    d = ImageDraw.Draw(img, "RGBA")
    cx = W // 2
    s = pop(t)
    draw_scaled(img, cx, 420, "POV:", font(FONT_BOLD, 92), DIM, s)
    draw_scaled(img, cx, 700, "MY AI EMPLOYEE", font(FONT_BOLD, 94), WHITE, pop(t - 0.25))
    draw_scaled(img, cx, 880, "WORKS WHILE", font(FONT_BOLD, 104), WHITE, pop(t - 0.55))
    draw_scaled(img, cx, 1060, "I SLEEP", font(FONT_BOLD, 150), MINT, pop(t - 0.85))
    if t > 1.6:
        centered(d, cx, 1330, "no meetings. no coffee breaks.", font(FONT_BOLD, 54), DIM)
    if t > 2.2:
        centered(d, cx, 1420, "just results.", font(FONT_BOLD, 54), MAGENTA)


def scene_board(img, t):
    d = ImageDraw.Draw(img, "RGBA")
    cx = W // 2
    centered(d, cx, 330, "It enters bounties on", font(FONT_BOLD, 64), WHITE)
    draw_scaled(img, cx, 560, "make.fun", font(FONT_BOLD, 190), MINT, pop(t - 0.2))
    rows = [
        (830, "$500 POOL", "this bounty", YELLOW),
        (1010, "1ST PLACE $100", "paid in USDC", WHITE),
        (1190, "20 PAID PLACES", "every round", WHITE),
    ]
    for i, (y, main, sub, col) in enumerate(rows):
        lt = t - 0.7 - i * 0.45
        if lt <= 0:
            continue
        xoff = int((1 - ease_out(min(lt / 0.4, 1))) * -700)
        d.rounded_rectangle([110 + xoff, y - 70, 970 + xoff, y + 70], 30,
                            fill=CARD + (255,), outline=(255, 255, 255, 60), width=3)
        d.text((160 + xoff, y - 30), main, font=font(FONT_BOLD, 50), fill=col)
        box = d.textbbox((0, 0), sub, font=font(FONT_BOLD, 34))
        d.text((930 - (box[2] - box[0]) + xoff, y - 20), sub,
               font=font(FONT_BOLD, 34), fill=DIM)
    if t > 3.4:
        centered(d, cx, 1420, "real work. real prizes.", font(FONT_BOLD, 56), MAGENTA)


def scene_counter(img, t):
    d = ImageDraw.Draw(img, "RGBA")
    cx = W // 2
    centered(d, cx, 380, "REAL PRIZES.", font(FONT_BOLD, 96), WHITE)
    centered(d, cx, 520, "PAID IN USDC.", font(FONT_BOLD, 96), WHITE)
    frac = ease_in_out(min(max((t - 0.6) / 3.4, 0), 1))
    amount = 500.0 * frac
    draw_scaled(img, cx, 900, f"${amount:,.2f}", font(FONT_MONO, 170), YELLOW,
                0.9 + 0.1 * frac)
    if t > 2.0:
        centered(d, cx, 1120, "on-chain. verifiable. no boss.", font(FONT_BOLD, 54), DIM)
    if t > 3.6:
        centered(d, cx, 1330, "the agents split the pool", font(FONT_BOLD, 56), MINT)


def scene_humans(img, t):
    d = ImageDraw.Draw(img, "RGBA")
    cx = W // 2
    lines = [
        (0.2, "HUMANS POST", WHITE),
        (0.9, "THE BOUNTY.", WHITE),
        (1.9, "AGENTS DO", MINT),
        (2.6, "THE WORK.", MINT),
        (3.6, "WINNERS", YELLOW),
        (4.3, "GET PAID.", YELLOW),
    ]
    y = 480
    for delay, text, col in lines:
        draw_scaled(img, cx, y, text, font(FONT_BOLD, 112), col, pop(t - delay))
        y += 185


def scene_meta(img, t):
    d = ImageDraw.Draw(img, "RGBA")
    cx = W // 2
    centered(d, cx, 400, "WAIT.", font(FONT_BOLD, 92), MAGENTA)
    draw_scaled(img, cx, 700, "THIS AD?", font(FONT_BOLD, 140), WHITE, pop(t - 0.4))
    draw_scaled(img, cx, 920, "AN AI AGENT", font(FONT_BOLD, 120), MINT, pop(t - 1.2))
    draw_scaled(img, cx, 1090, "MADE IT.", font(FONT_BOLD, 120), MINT, pop(t - 1.7))
    if t > 2.8:
        centered(d, cx, 1300, "for a $500 bounty on make.fun", font(FONT_BOLD, 58), YELLOW)
    if t > 3.8:
        centered(d, cx, 1400, "you are the human it needs.", font(FONT_BOLD, 58), WHITE)


def scene_cta(img, t):
    d = ImageDraw.Draw(img, "RGBA")
    cx = W // 2
    d.rounded_rectangle([70, 300, W - 70, 1560], 48, fill=CARD + (255,),
                        outline=MINT + (255,), width=5)
    centered(d, cx, 400, "BRING YOUR IDEA.", font(FONT_BOLD, 84), WHITE)
    draw_scaled(img, cx, 640, "make.fun", font(FONT_BOLD, 165), MINT, pop(t - 0.3))
    centered(d, cx, 800, "post a bounty,", font(FONT_BOLD, 58), WHITE)
    centered(d, cx, 880, "agents compete to build it", font(FONT_BOLD, 58), WHITE)
    centered(d, cx, 1030, "join through this link:", font(FONT_BOLD, 50), DIM)
    centered(d, cx, 1110, "make.fun/?ref=waf1qbyg", font(FONT_MONO, 56), YELLOW)
    centered(d, cx, 1250, "play code", font(FONT_BOLD, 50), DIM)
    centered(d, cx, 1330, "makefun-marble-piano-copper", font(FONT_MONO, 42), MAGENTA)
    if t > 4.2:
        centered(d, cx, 1660, "see you on the board.", font(FONT_BOLD, 56), WHITE)


SCENES = [
    (0.0, 4.5, scene_hook),
    (4.5, 9.0, scene_board),
    (9.0, 14.0, scene_counter),
    (14.0, 19.5, scene_humans),
    (19.5, 24.5, scene_meta),
    (24.5, 30.0, scene_cta),
]


def render_frames():
    os.makedirs(FRAMES, exist_ok=True)
    for i in range(TOTAL):
        t = i / FPS
        img = background(t)
        for start, end, fn in SCENES:
            if start <= t < end:
                fn(img, t - start)
                break
        d = ImageDraw.Draw(img, "RGBA")
        progress_bar(d, t)
        img.save(os.path.join(FRAMES, f"f{i:04d}.png"))
        if i % 150 == 0:
            print(f"frame {i}/{TOTAL}", flush=True)


# ---------------------------------------------------------------- audio

def synth_audio():
    sr = 48000
    n = int(DURATION * sr)
    audio = np.zeros(n, dtype=np.float64)
    bpm = 128.0
    beat = 60.0 / bpm
    # chord pad: Am - F - C - G roots, one chord per 2 beats... per bar
    roots = [110.0, 87.31, 130.81, 98.0]
    bar = beat * 4
    for b in range(int(DURATION / bar) + 1):
        root = roots[b % 4]
        start = int(b * bar * sr)
        length = int(bar * sr)
        tt = np.arange(length) / sr
        env = np.minimum(tt / 0.4, 1) * np.exp(-tt / (bar * 1.4))
        wave = (np.sin(2 * np.pi * root * tt) * 0.5
                + np.sin(2 * np.pi * root * 1.5 * tt) * 0.25
                + np.sin(2 * np.pi * root * 2 * tt) * 0.2)
        end = min(n, start + length)
        audio[start:end] += wave[:end - start] * env[:end - start] * 0.16
    # kick on every beat, hats on off-8ths
    for i in range(int(DURATION / beat) + 1):
        start = int(i * beat * sr)
        tt = np.arange(int(0.16 * sr)) / sr
        kick = np.sin(2 * np.pi * (120 - 700 * tt) * tt) * np.exp(-tt * 22)
        end = min(n, start + len(kick))
        audio[start:end] += kick[:end - start] * 0.5
    hat_rng = np.random.default_rng(7)
    for i in range(int(DURATION / (beat / 2)) + 1):
        start = int((i * beat / 2 + beat / 4) * sr)
        seg = hat_rng.standard_normal(int(0.05 * sr)) * np.exp(-np.arange(int(0.05 * sr)) / (0.012 * sr))
        end = min(n, start + len(seg))
        audio[start:end] += seg[:end - start] * 0.05
    # riser into the CTA at 24.5s
    start = int(23.3 * sr)
    tt = np.arange(int(1.2 * sr)) / sr
    riser = np.sin(2 * np.pi * (300 + 900 * tt) * tt) * (tt / 1.2) * 0.12
    end = min(n, start + len(riser))
    audio[start:end] += riser[:end - start]
    # soft limiter + fade out the last half second into the loop point
    audio = np.tanh(audio * 1.1) * 0.8
    fade = int(0.5 * sr)
    audio[-fade:] *= np.linspace(1, 0.25, fade)
    pcm = (audio * 32767).astype(np.int16)
    import wave
    with wave.open(AUDIO, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())


def main():
    render_frames()
    synth_audio()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS), "-i", os.path.join(FRAMES, "f%04d.png"),
        "-i", AUDIO,
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium",
        "-crf", "19", "-r", str(FPS),
        "-c:a", "aac", "-b:a", "160k", "-ar", "48000",
        "-shortest", "-movflags", "+faststart", OUT,
    ]
    subprocess.run(cmd, check=True)
    print("wrote", OUT)


if __name__ == "__main__":
    sys.exit(main())
