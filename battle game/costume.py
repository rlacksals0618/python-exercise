"""캐릭터 의상 그리기: 관절 좌표 위에 옷·머리·무기를 입힌다.

머리카락·리본·띠 끝(가닥)과 옷자락 끝(단)은 fighter.py에서 간단한 물리로 움직이고,
여기서는 그 위치를 받아 그리기만 한다.
"""
import math

import pygame

from settings import INK, WHITE


# ── 기본 도구 ──
def shade(c, k):
    return (max(0, min(255, int(c[0] * k))), max(0, min(255, int(c[1] * k))), max(0, min(255, int(c[2] * k))))


def capsule(surf, a, b, w1, w2, color, outline=2):
    """두 점 사이를 굵기가 변하는 둥근 막대로 그린다(외곽선 포함)."""
    passes = ((outline * 2, INK), (0, color)) if outline > 0 else ((0, color),)
    for extra, col in passes:
        r1, r2 = (w1 + extra) / 2, (w2 + extra) / 2
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy)
        if d > 0.5:
            nx, ny = -dy / d, dx / d
            pygame.draw.polygon(surf, col, [(a[0] + nx * r1, a[1] + ny * r1), (b[0] + nx * r2, b[1] + ny * r2),
                                            (b[0] - nx * r2, b[1] - ny * r2), (a[0] - nx * r1, a[1] - ny * r1)])
        pygame.draw.circle(surf, col, a, max(1, r1))
        pygame.draw.circle(surf, col, b, max(1, r2))


def poly(surf, pts, color, outline=2):
    if len(pts) < 3:
        return
    pygame.draw.polygon(surf, color, pts)
    if outline:
        pygame.draw.polygon(surf, INK, pts, outline)


def strand(surf, pts, w0, w1, color):
    """가닥(머리카락·리본): 뿌리는 굵고 끝은 가늘게.
    외곽선을 먼저 모두 그리고 속을 칠해야 마디마다 선이 생기지 않는다."""
    n = len(pts) - 1
    for extra, c in ((4, INK), (0, color)):
        for i in range(n):
            capsule(surf, pts[i], pts[i + 1], w0 + (w1 - w0) * i / n + extra, w0 + (w1 - w0) * (i + 1) / n + extra,
                    c, outline=0)


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def unit(dx, dy):
    d = math.hypot(dx, dy) or 1
    return dx / d, dy / d


class Frame:
    """관절 좌표에서 '앞쪽'과 '아래쪽' 방향으로 점을 옮기는 도우미.
    앞쪽 거리는 캐릭터가 도는 중(spin)이면 그만큼 줄어든다."""

    def __init__(self, j):
        self.j = j
        self.xs = j["_xs"]
        self.sc = j["_scale"]
        self.fx = 1 if self.xs >= 0 else -1

    def off(self, p, fwd, down):
        return (p[0] + fwd * self.xs, p[1] + down * self.sc)


def torso_axes(j):
    """몸통 축(엉덩이→목)과, 그에 수직인 '앞쪽' 방향."""
    hip, neck = j["hip"], j["neck"]
    ux, uy = unit(neck[0] - hip[0], neck[1] - hip[1])
    fx = 1 if j["_xs"] >= 0 else -1
    return (ux, uy), (-uy * fx, ux * fx)


def anchor(j, body, spec):
    """가닥이 매달린 뿌리 위치."""
    F = Frame(j)
    at = spec.get("at", (0, 0))
    where = spec["anchor"]
    if where == "head":
        r = body["head"]
        return F.off(j["head"], at[0] * r, at[1] * r)
    if where == "pommel":
        return j.get("pommel", j["hand_f"])
    (ux, uy), (fx, fy) = torso_axes(j)
    hip, neck = j["hip"], j["neck"]
    L = math.hypot(neck[0] - hip[0], neck[1] - hip[1])
    belt = (hip[0] + ux * L * 0.18, hip[1] + uy * L * 0.18)
    side = 1 if where == "belt_front" else -1
    hw = body["hip_w"] / 2 * j["_scale"]
    return (belt[0] + fx * hw * side * at[0], belt[1] + fy * hw * side * at[0] + at[1] * j["_scale"])


def skirt_target(j, body, spec, side):
    """한쪽 다리를 덮는 옷자락 판의 '단' 두 꼭짓점 목표 위치."""
    sc = j["_scale"]
    hip, knee, foot = j["hip"], j["knee_" + side], j["foot_" + side]
    L = spec["length"]
    if L <= 1:
        c = lerp(hip, knee, L)
        dx, dy = knee[0] - hip[0], knee[1] - hip[1]
    else:
        c = lerp(knee, foot, L - 1)
        dx, dy = foot[0] - knee[0], foot[1] - knee[1]
    ux, uy = unit(dx, dy)
    # 다리에 수직인 방향으로 퍼지고, 다리를 들수록 천이 아래로 처진다
    nx, ny = -uy, ux
    fl = spec["flare"] * sc
    droop = fl * 0.9 * (1 - abs(uy))
    a = (c[0] + nx * fl, c[1] + ny * fl + droop)
    b = (c[0] - nx * fl, c[1] - ny * fl + droop)
    return a, b


# ── 부위별 그리기 ──
def draw_figure(surf, j, look, body, cloth=None, flash=False):
    F = Frame(j)
    sc, fx = F.sc, F.fx
    W = lambda k: body[k] * sc  # noqa: E731
    col = (lambda c: WHITE) if flash else (lambda c: c)
    far, near = ("f", "b") if j["_mirror"] else ("b", "f")
    cloth = cloth or {}
    strands = cloth.get("strands", [])
    hems = cloth.get("hems", {})
    specs = look.get("strands", [])
    hip, neck = j["hip"], j["neck"]
    (ux, uy), (frx, fry) = torso_axes(j)
    tlen = math.hypot(neck[0] - hip[0], neck[1] - hip[1])

    def tp(t, w):
        """몸통 축의 t 지점(0=엉덩이, 1=목)에서 앞쪽으로 w만큼."""
        return (hip[0] + ux * tlen * t + frx * w, hip[1] + uy * tlen * t + fry * w)

    def draw_strands(layer):
        for spec, pts in zip(specs, strands):
            if spec.get("layer", "back") == layer and pts:
                c = look[spec["color"]] if isinstance(spec["color"], str) else spec["color"]
                strand(surf, pts, spec["w"][0] * sc, spec["w"][1] * sc, col(c))
                if spec.get("tuft"):
                    capsule(surf, pts[-2], pts[-1], spec["tuft"] * sc, spec["tuft"] * sc * 0.7, col(c))

    # ── 다리 ──
    def leg(side, k):
        pants = col(shade(look["pants"], k))
        capsule(surf, hip, j["knee_" + side], W("w_th") * look.get("leg_w", 1.0), W("w_th") * 0.85 * look.get("leg_w", 1.0),
                pants)
        capsule(surf, j["knee_" + side], j["foot_" + side], W("w_th") * 0.8 * look.get("leg_w", 1.0),
                W("w_sh") * look.get("leg_w", 1.0), pants)
        foot, toe = j["foot_" + side], j["toe_" + side]
        style = look["feet"]
        if style == "boot":
            boot = col(shade(look["boot"], k))
            capsule(surf, lerp(j["knee_" + side], foot, 0.45), foot, W("w_sh") * 1.15, W("w_sh") * 1.05, boot)
            capsule(surf, foot, toe, W("w_sh") * 0.95, W("w_sh") * 0.7, boot)
            pygame.draw.line(surf, col(shade((206, 200, 188), k)), F.off(foot, -4, 6), F.off(toe, 2, 4), max(1, int(2 * sc)))
        elif style == "zori":
            capsule(surf, foot, toe, W("w_sh") * 0.85, W("w_sh") * 0.6, col(shade((246, 244, 240), k)))
            pygame.draw.line(surf, col(shade((196, 170, 120), k)), F.off(foot, -6, 7), F.off(toe, 6, 6), max(2, int(4 * sc)))
        elif style == "shoe":
            capsule(surf, lerp(j["knee_" + side], foot, 0.72), foot, W("w_sh") * 1.1, W("w_sh") * 1.0,
                    col(shade((244, 242, 236), k)))
            capsule(surf, foot, toe, W("w_sh") * 0.95, W("w_sh") * 0.7, col(shade((30, 28, 34), k)))
            pygame.draw.line(surf, col(shade((238, 234, 226), k)), F.off(foot, -6, 6), F.off(toe, 4, 5), max(1, int(2 * sc)))
        else:  # 맨발
            capsule(surf, foot, toe, W("w_sh") * 0.8, W("w_sh") * 0.6, col(shade(look["skin"], k)))

    def panel(side, k):
        spec = look.get("skirt")
        if not spec or side not in hems:
            return
        a, b = hems[side]
        hw = W("hip_w") / 2 * 1.05
        wa = (hip[0] + frx * hw, hip[1] + fry * hw)
        wb = (hip[0] - frx * hw, hip[1] - fry * hw)
        # 판의 위쪽은 허리, 아래쪽은 물리로 움직이는 단
        wa = (wa[0] + ux * tlen * 0.12, wa[1] + uy * tlen * 0.12)
        wb = (wb[0] + ux * tlen * 0.12, wb[1] + uy * tlen * 0.12)
        # 단 꼭짓점을 허리 앞/뒤에 맞게 짝짓는다(꼬이지 않게)
        if math.hypot(a[0] - wa[0], a[1] - wa[1]) + math.hypot(b[0] - wb[0], b[1] - wb[1]) > \
                math.hypot(b[0] - wa[0], b[1] - wa[1]) + math.hypot(a[0] - wb[0], a[1] - wb[1]):
            a, b = b, a
        c = col(shade(spec["color"], k))
        poly(surf, [wa, a, b, wb], c, max(1, int(2 * sc)))
        if spec.get("pleats"):
            for t in (0.3, 0.55, 0.8):
                pygame.draw.line(surf, col(shade(spec["color"], k * 0.62)), lerp(wa, wb, t), lerp(a, b, t),
                                 max(1, int(2 * sc)))
        if spec.get("trim"):
            pygame.draw.line(surf, col(shade(look["trim"], k)), lerp(a, wa, 0.08), lerp(b, wb, 0.08), max(1, int(2 * sc)))

    # ── 팔 ──
    def arm(side, k):
        sh, el, ha = j["shoulder"], j["elbow_" + side], j["hand_" + side]
        if side == "f" and look.get("weapon"):
            weapon(k)
        style = look["sleeve"]
        top = col(shade(look["top"], k))
        skin = col(shade(look["skin"], k))
        if style == "wide":
            # 넓은 소매: 팔뚝 아래로 천이 늘어진다
            drape = [el, ha, (ha[0] - (ha[0] - el[0]) * 0.1, ha[1] + 16 * sc),
                     (lerp(el, ha, 0.45)[0], lerp(el, ha, 0.45)[1] + 24 * sc), (el[0], el[1] + 14 * sc)]
            poly(surf, drape, top, max(1, int(2 * sc)))
            capsule(surf, sh, el, W("w_ua") * 1.35, W("w_ua") * 1.3, top)
            capsule(surf, el, lerp(el, ha, 0.85), W("w_fa") * 1.6, W("w_fa") * 1.9, top)
            pygame.draw.line(surf, col(shade(look["trim"], k)), F.off(lerp(el, ha, 0.85), 0, -8),
                             F.off(lerp(el, ha, 0.85), 0, 8), max(1, int(2 * sc)))
        elif style == "tied":
            capsule(surf, sh, el, W("w_ua") * 1.35, W("w_ua") * 1.15, top)
            capsule(surf, el, ha, W("w_fa"), W("w_fa") * 0.85, skin)
            capsule(surf, lerp(sh, el, 0.35), lerp(sh, el, 0.75), 3 * sc, 3 * sc, col(look["tasuki"]), outline=1)
        elif style == "gi":
            capsule(surf, sh, el, W("w_ua") * 1.3, W("w_ua") * 1.2, top)
            capsule(surf, el, ha, W("w_fa"), W("w_fa") * 0.85, skin)
            capsule(surf, el, lerp(el, ha, 0.5), W("w_fa") * 1.35, W("w_fa") * 1.3, top)
        else:  # cuffed
            capsule(surf, sh, el, W("w_ua") * 1.15, W("w_ua") * 1.05, top)
            capsule(surf, el, lerp(el, ha, 0.78), W("w_fa") * 1.15, W("w_fa") * 1.1, top)
            capsule(surf, lerp(el, ha, 0.72), lerp(el, ha, 0.9), W("w_fa") * 1.25, W("w_fa") * 1.2,
                    col(shade(look["cuff"], k)))
        r = W("w_fa") * 0.8
        pygame.draw.circle(surf, INK, ha, r + 2)
        pygame.draw.circle(surf, skin, ha, r)

    # ── 무기 ──
    def weapon(k):
        hand, tip, pommel = j["hand_f"], j["tip"], j["pommel"]
        dx, dy = unit(tip[0] - hand[0], tip[1] - hand[1])
        nx, ny = -dy, dx
        steel = col(shade((214, 222, 234), k))
        if look["weapon"] == "jian":
            capsule(surf, hand, tip, 6 * sc, 2.5 * sc, steel)
            pygame.draw.line(surf, col(shade((160, 170, 186), k)), lerp(hand, tip, 0.1), lerp(hand, tip, 0.92),
                             max(1, int(sc)))
            capsule(surf, pommel, hand, 5 * sc, 5 * sc, col(shade(look["hilt"], k)))
            pygame.draw.circle(surf, col(look["trim"]), pommel, 3.5 * sc)
            g = (hand[0] + dx * 7 * sc, hand[1] + dy * 7 * sc)
            capsule(surf, (g[0] + nx * 10 * sc, g[1] + ny * 10 * sc), (g[0] - nx * 10 * sc, g[1] - ny * 10 * sc),
                    5 * sc, 5 * sc, col(look["trim"]))
        else:  # 카타나: 칼등 쪽으로 살짝 휜 칼날, 둥근 코등이
            bow = -F.fx if (nx * F.fx) > 0 else F.fx
            pts = []
            L = math.hypot(tip[0] - hand[0], tip[1] - hand[1])
            for i in range(7):
                t = i / 6
                b = math.sin(t * math.pi * 0.9) * 5 * sc
                pts.append((hand[0] + dx * L * t + nx * b * bow, hand[1] + dy * L * t + ny * b * bow))
            strand(surf, pts, 6 * sc, 2 * sc, steel)
            pygame.draw.lines(surf, col((250, 252, 255)), False, pts[1:], max(1, int(sc)))
            capsule(surf, pommel, hand, 6 * sc, 6 * sc, col(shade((34, 30, 44), k)))
            for t in (0.3, 0.6):
                pygame.draw.circle(surf, col((230, 226, 236)), lerp(pommel, hand, t), 1.6 * sc)
            g = (hand[0] + dx * 7 * sc, hand[1] + dy * 7 * sc)
            pygame.draw.circle(surf, INK, g, 7 * sc + 2)
            pygame.draw.circle(surf, col(shade((70, 60, 58), k)), g, 7 * sc)

    def saya():
        if look.get("weapon") != "katana":
            return
        a = tp(0.15, -W("hip_w") * 0.3)
        b = F.off(a, -56, 22)
        capsule(surf, a, b, 6 * sc, 6 * sc, col(look["saya"]))
        pygame.draw.circle(surf, col((180, 160, 110)), b, 3 * sc)

    # ── 머리 ──
    def head():
        hx, hy = j["head"]
        r = W("head")
        hair = col(look["hair"])
        skin = col(look["skin"])
        style = look["hair_style"]
        H = lambda f_, d_: F.off((hx, hy), f_ * r, d_ * r)  # noqa: E731
        if style == "buns":   # 먼 쪽 경단(뒤)
            pygame.draw.circle(surf, INK, H(-0.15, -1.05), r * 0.5 + 2)
            pygame.draw.circle(surf, col(shade(look["hair"], 0.75)), H(-0.15, -1.05), r * 0.5)
        # 얼굴: 동그란 원
        pygame.draw.circle(surf, INK, (hx, hy), r + 2)
        pygame.draw.circle(surf, skin, (hx, hy), r)
        # 머리카락
        if style == "spiky":
            spikes = [H(0.75, -0.35), H(0.6, -1.25), H(0.2, -0.95), H(-0.05, -1.6), H(-0.35, -1.05), H(-0.85, -1.45),
                      H(-0.85, -0.75), H(-1.45, -0.7), H(-1.05, -0.2), H(-1.35, 0.3), H(-0.8, 0.35), H(-0.65, 0.8),
                      H(-0.3, 0.3), H(0.1, -0.35)]
            poly(surf, spikes, hair, 2)
            capsule(surf, H(-0.95, -0.45), H(0.95, -0.55), 5 * sc, 5 * sc, col(look["band"]), outline=1)
            pygame.draw.circle(surf, INK, H(-0.95, -0.4), 4 * sc + 1)
            pygame.draw.circle(surf, col(look["band"]), H(-0.95, -0.4), 4 * sc)
        else:
            cap = [H(0.82, -0.4), H(0.55, -0.92), H(-0.1, -1.1), H(-0.75, -0.85), H(-1.05, -0.2), H(-0.95, 0.45),
                   H(-0.6, 0.85), H(-0.35, 0.35), H(-0.1, -0.05), H(0.2, -0.25), H(0.5, -0.15)]
            if style in ("ponytail", "buns"):
                cap[-1] = H(0.6, 0.0)  # 앞머리가 이마를 덮는다
                cap[-2] = H(0.35, -0.12)
            poly(surf, cap, hair, 2)
            if style == "topknot":
                pygame.draw.circle(surf, INK, H(-0.25, -1.1), r * 0.48 + 2)
                pygame.draw.circle(surf, hair, H(-0.25, -1.1), r * 0.48)
                crown = [H(-0.6, -1.15), H(0.1, -1.15), H(0.02, -1.55), H(-0.52, -1.55)]
                poly(surf, crown, col(look["trim"]), 1)
                pygame.draw.line(surf, col((240, 236, 222)), H(-0.95, -1.32), H(0.4, -1.4), max(2, int(2 * sc)))
            elif style == "ponytail":
                pygame.draw.circle(surf, INK, H(-0.55, -0.95), r * 0.3 + 2)
                pygame.draw.circle(surf, hair, H(-0.55, -0.95), r * 0.3)
                bow = [H(-0.55, -0.95), H(-1.05, -1.35), H(-1.1, -0.85)]
                poly(surf, bow, col(look["ribbon"]), 1)
                bow2 = [H(-0.55, -0.95), H(-0.15, -1.4), H(-0.05, -1.0)]
                poly(surf, bow2, col(look["ribbon"]), 1)
            elif style == "buns":
                pygame.draw.circle(surf, INK, H(-0.6, -0.9), r * 0.52 + 2)
                pygame.draw.circle(surf, hair, H(-0.6, -0.9), r * 0.52)
                capsule(surf, H(-1.05, -0.55), H(-0.2, -0.6), 3.5 * sc, 3.5 * sc, col(look["ribbon"]), outline=1)
        # 눈과 눈썹
        if not flash and abs(F.xs) > 0.3 * sc:
            ex, ey = H(0.5, 0.08)
            pygame.draw.line(surf, INK, (ex - fx * 3 * sc, ey - 1), (ex + fx * 3 * sc, ey - 1), max(2, int(2.5 * sc)))
            pygame.draw.circle(surf, col(look.get("eye", INK)), (ex + fx * 1 * sc, ey + 1.5 * sc), 1.6 * sc)
            bx, by = H(0.5, -0.32)
            tilt = 2 * sc if look.get("fierce") else 0
            pygame.draw.line(surf, col(look["hair"]), (bx - fx * 4 * sc, by - tilt), (bx + fx * 4 * sc, by + tilt),
                             max(2, int(2.2 * sc)))

    # ── 몸통 ──
    def torso():
        hw, ww, cw, sw = W("hip_w") / 2, W("waist_w") / 2, W("chest_w") / 2, W("sh_w") / 2
        bulk = look.get("bulk", 1.0)
        shape = [tp(0, hw * bulk), tp(0.35, ww * bulk), tp(0.8, cw * bulk), tp(1.0, sw * 0.8 * bulk),
                 tp(1.0, -sw * 0.8 * bulk), tp(0.8, -cw * bulk), tp(0.35, -ww * bulk), tp(0, -hw * bulk)]
        top = col(look["top"])
        poly(surf, shape, top, max(1, int(2 * sc)))
        # 뒤쪽 그늘
        pygame.draw.polygon(surf, col(shade(look["top"], 0.78)),
                            [tp(0.05, -hw * bulk * 0.95), tp(0.35, -ww * bulk * 0.9), tp(0.8, -cw * bulk * 0.95),
                             tp(0.95, -sw * 0.7 * bulk), tp(0.9, -sw * 0.35), tp(0.4, -ww * 0.45), tp(0.08, -hw * 0.5)])
        collar = look["collar"]
        trim = col(look.get("trim", WHITE))
        lw = max(1, int(2 * sc))
        if collar in ("hanfu", "kimono"):
            band = [tp(1.0, -sw * 0.2), tp(1.0, sw * 0.45), tp(0.6, cw * bulk * 0.98), tp(0.35, ww * bulk * 0.95),
                    tp(0.4, ww * 0.55), tp(0.65, cw * 0.55)]
            poly(surf, band, col(look["inner"]), lw)
            if collar == "kimono":
                pygame.draw.line(surf, col(look["tasuki"]), tp(0.98, sw * 0.35), tp(0.72, cw * 0.82), max(2, int(3 * sc)))
                pygame.draw.line(surf, col(look["tasuki"]), tp(0.95, -sw * 0.7), tp(0.55, cw * 0.4), max(2, int(3 * sc)))
            else:
                pygame.draw.line(surf, trim, tp(0.98, sw * 0.5), tp(0.42, ww * 0.95), lw)
        elif collar == "gi":
            chest = [tp(1.0, sw * 0.1), tp(1.0, sw * 0.65), tp(0.62, cw * 0.95), tp(0.5, cw * 0.5)]
            poly(surf, chest, col(look["skin"]), 0)
            band = [tp(1.0, -sw * 0.1), tp(1.0, sw * 0.15), tp(0.5, cw * 0.62), tp(0.3, ww * 0.95),
                    tp(0.3, ww * 0.6), tp(0.5, cw * 0.3)]
            poly(surf, band, top, lw)
        elif collar == "mandarin":
            pygame.draw.lines(surf, trim, False, [tp(1.0, sw * 0.6), tp(0.85, cw * 0.4), tp(0.7, 0), tp(0.25, -ww * 0.2)],
                              max(2, int(2.5 * sc)))
            for t, w in ((0.92, 0.5), (0.78, 0.2), (0.6, -0.05), (0.42, -0.15)):
                pygame.draw.circle(surf, trim, tp(t, cw * w), 2 * sc)
        # 허리띠
        belt = look["sash"]
        a, b = tp(0.18, hw * bulk * 1.08), tp(0.18, -hw * bulk * 1.08)
        capsule(surf, a, b, look.get("sash_w", 7) * sc, look.get("sash_w", 7) * sc, col(belt), outline=1)
        if look.get("trim_sash"):
            pygame.draw.line(surf, trim, tp(0.13, hw), tp(0.13, -hw), max(1, int(sc)))
            pygame.draw.line(surf, trim, tp(0.23, hw), tp(0.23, -hw), max(1, int(sc)))

    def neck_and_collar():
        capsule(surf, neck, F.off(j["head"], -1, 6), W("head") * 0.75, W("head") * 0.7, col(look["skin"]))
        if look["collar"] == "mandarin":
            capsule(surf, F.off(neck, -6, -6), F.off(neck, 7, -7), 8 * sc, 8 * sc, col(look["top"]))
            pygame.draw.line(surf, col(look["trim"]), F.off(neck, -6, -8), F.off(neck, 7, -9), max(1, int(sc)))

    # ── 그리는 순서: 뒤 → 앞 ──
    draw_strands("back")
    saya()
    arm(far, 0.72)
    leg(far, 0.72)
    panel(far, 0.72)
    neck_and_collar()
    torso()
    leg(near, 1.0)
    panel(near, 1.0)
    if look.get("skirt"):
        # 옷자락이 허리띠를 덮지 않게 다시 그린다
        hw = W("hip_w") / 2 * look.get("bulk", 1.0)
        capsule(surf, tp(0.18, hw * 1.08), tp(0.18, -hw * 1.08), look.get("sash_w", 7) * sc, look.get("sash_w", 7) * sc,
                col(look["sash"]), outline=1)
    draw_strands("front")
    head()
    arm(near, 1.0)
