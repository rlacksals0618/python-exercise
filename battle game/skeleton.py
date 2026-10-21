"""포즈(관절 각도) → 관절 좌표 계산, 맞는 범위·때리는 범위 상자.

스프라이트 대신 관절 각도로 몸을 움직이므로 키프레임 사이를 자연스럽게 보간할 수 있다.
옷과 머리는 costume.py가 이 관절 좌표 위에 그린다.
"""
import math

import pygame

from moves import AIR, CROUCH, CROUCH_SWORD, POSE_KEYS, STANCE


# ── 포즈 계산 ──
def smoothstep(t):
    return t * t * (3 - 2 * t)


def lerp_pose(a, b, t, wrap_spin=False):
    out = {k: a[k] + (b[k] - a[k]) * t for k in POSE_KEYS}
    if wrap_spin:
        # 상태가 바뀔 때 360도와 0도처럼 같은 방향이면 다시 돌지 않게 가까운 쪽으로 섞는다
        d = (b["spin"] - a["spin"] + 180) % 360 - 180
        out["spin"] = a["spin"] + d * t
    return out


def base_pose(style, base="stand", extra=None):
    """유형별 기본 자세. extra는 캐릭터마다 다른 손·칼 위치(서 있을 때만 적용)."""
    pose = dict(STANCE[style])
    if extra:
        pose.update(extra)
    if base == "crouch":
        pose.update(CROUCH_SWORD if style == "sword" else CROUCH)
    elif base == "air":
        pose.update(AIR)
    return pose


_full_keys = {}


def move_pose(move, style, frame, extra=None, who=None):
    """기술의 키프레임을 frame 시점으로 보간한 포즈."""
    keys = _full_keys.get((id(move), who))
    if keys is None:
        base = base_pose(style, move.base, extra)
        keys = [(f, {**base, **ov}) for f, ov in move.keys]
        _full_keys[(id(move), who)] = keys
    if frame <= keys[0][0]:
        return dict(keys[0][1])
    for (f0, p0), (f1, p1) in zip(keys, keys[1:]):
        if frame < f1:
            return lerp_pose(p0, p1, smoothstep((frame - f0) / (f1 - f0)))
    return dict(keys[-1][1])


def _v(angle, length):
    r = math.radians(angle)
    return math.sin(r) * length, math.cos(r) * length


def _add(p, d):
    return (p[0] + d[0], p[1] + d[1])


def compute_joints(pose, body, facing, ox, oy, grounded=True, scale=1.0):
    """관절의 화면 좌표를 계산한다. (ox, oy)는 발 중앙 기준점."""
    B = body
    hip = (pose["x"], -(B["th"] + B["sh"]) * 0.97 - pose["y"])
    tr = math.radians(pose["torso"])
    ax, ay = math.sin(tr), -math.cos(tr)          # 엉덩이 → 목 방향
    neck = (hip[0] + ax * B["torso"], hip[1] + ay * B["torso"])
    hr = math.radians(pose["torso"] + pose["head"])
    hd = B["neck"] + B["head"]
    head = (neck[0] + math.sin(hr) * hd, neck[1] - math.cos(hr) * hd)
    shoulder = (neck[0] - ax * 5, neck[1] - ay * 5)

    j = {"hip": hip, "neck": neck, "head": head, "shoulder": shoulder}
    for side in ("f", "b"):
        j["elbow_" + side] = e = _add(shoulder, _v(pose[side + "a_u"], B["ua"]))
        j["hand_" + side] = _add(e, _v(pose[side + "a_l"], B["fa"]))
        j["knee_" + side] = k = _add(hip, _v(pose[side + "l_u"], B["th"]))
        j["foot_" + side] = f = _add(k, _v(pose[side + "l_l"], B["sh"]))
        j["toe_" + side] = _add(f, _v(pose[side + "l_l"] + 90, B["foot"]))
    if B.get("blade"):
        j["tip"] = _add(j["hand_f"], _v(pose["blade"], B["blade"]))
        j["pommel"] = _add(j["hand_f"], _v(pose["blade"], -16))

    if grounded:
        # 가장 낮은 곳이 바닥에 닿게 몸 전체를 올리거나 내린다
        low = max(j["foot_f"][1] + 4, j["foot_b"][1] + 4, j["toe_f"][1] + 4, j["toe_b"][1] + 4,
                  j["knee_f"][1] + 6, j["knee_b"][1] + 6, j["hand_f"][1] + 6, j["hand_b"][1] + 6,
                  head[1] + B["head"], hip[1] + 10, neck[1] + 10)
        shift = -low
    else:
        shift = 0.0

    spin = math.cos(math.radians(pose["spin"]))
    xs = facing * spin * scale
    px = pose["x"]
    out = {}
    for name, (x, y) in j.items():
        out[name] = (ox + facing * scale * px + (x - px) * xs, oy + (y + shift) * scale)
    out["_xs"] = xs
    out["_mirror"] = spin < 0
    out["_scale"] = scale
    return out


def hurtbox(j, body):
    pts = [j[n] for n in ("neck", "hip", "knee_f", "knee_b", "foot_f", "foot_b", "shoulder")]
    r = body["head"] * j["_scale"]
    hx, hy = j["head"]
    xs = [p[0] for p in pts] + [hx - r, hx + r]
    ys = [p[1] for p in pts] + [hy - r]
    left, right = min(xs), max(xs)
    if right - left < 40:
        c = (left + right) / 2
        left, right = c - 20, c + 20
    else:
        pad = (right - left) * 0.1
        left, right = left + pad, right - pad
    return pygame.Rect(round(left), round(min(ys)), round(right - left), round(max(ys) - min(ys)))


STRIKE_SEG = {"fa": ("elbow_f", "hand_f", 0.4), "ba": ("elbow_b", "hand_b", 0.4),
              "fl": ("knee_f", "toe_f", 0.35), "bl": ("knee_b", "toe_b", 0.35),
              "blade": ("elbow_f", "tip", 0.3)}


def strike_segment(j, strike, start=None):
    """공격 부위 선분. start는 선분의 어디서부터 쓸지(0 = 팔꿈치·무릎·손잡이부터)."""
    a_name, b_name, default = STRIKE_SEG[strike]
    start = default if start is None else start
    a, b = j[a_name], j[b_name]
    s = (a[0] + (b[0] - a[0]) * start, a[1] + (b[1] - a[1]) * start)
    return s, b


def hitbox(j, strike, reach):
    """공격 판정: 팔꿈치(무릎)부터 끝까지 선분을 따라 작은 상자 여러 개.
    붙어 있을 때도 맞고, 대각선으로 휘두를 때 판정이 지나치게 커지지 않는다."""
    a, b = strike_segment(j, strike, 0.0)
    n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) // 22))
    boxes = []
    for i in range(n + 1):
        t = i / n
        x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
        boxes.append(pygame.Rect(round(x - reach / 2), round(y - reach / 2), round(reach), round(reach)))
    return boxes
