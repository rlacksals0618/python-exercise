"""격투 캐릭터 한 명: 입력 → 상태 머신 → 물리 → 포즈·판정 상자 계산."""
import math
from collections import deque

import pygame

import costume
import skeleton
from controls import EMPTY_INPUT, InputBuffer, numpad
from moves import SPECIAL_COMMANDS
from settings import (BLEND_TICKS, BODY_HALF_W, BUTTON_BUFFER, CHIP_RATE, FALL_GRAVITY_MULT, GETUP_TICKS,
                      GRAVITY, GROUND_ACCEL, GROUND_FRICTION, GROUND_Y, HIT_FRICTION, JUGGLE_LIMIT, JUMP_VX,
                      JUMP_VY, KNOCKDOWN_TICKS, LAND_TICKS, PREJUMP_TICKS, STAGE_LEFT, STAGE_RIGHT, START_X,
                      SUPER_MAX, WALK_BACK, WALK_FWD)

# ── 상태 ──
IDLE, WALK, CROUCH, PREJUMP, AIR, LAND = "IDLE", "WALK", "CROUCH", "PREJUMP", "AIR", "LAND"
ATTACK, HITSTUN, BLOCKSTUN, JUGGLE = "ATTACK", "HITSTUN", "BLOCKSTUN", "JUGGLE"
KNOCKDOWN, GETUP, KO, WIN = "KNOCKDOWN", "GETUP", "KO", "WIN"
NEUTRAL = (IDLE, WALK, CROUCH)

# ── 상태별 포즈 보정 ──
GUARD = {"martial": dict(fa_u=60, fa_l=172, ba_u=45, ba_l=165, torso=-6, head=8),
         "sword": dict(fa_u=55, fa_l=125, blade=172, ba_u=30, ba_l=110, torso=-6, head=8)}
HURT = {"high": dict(torso=-24, head=-22, fa_u=-30, fa_l=20, ba_u=-45, ba_l=0, x=-6, blade=-40),
        "body": dict(torso=34, head=18, fa_u=10, fa_l=60, ba_u=0, ba_l=40, x=-4, blade=-20),
        "low": dict(torso=18, head=10, fl_u=5, fl_l=-20, bl_u=-30, bl_l=-40, fa_u=-20, fa_l=30, blade=-30)}
JUGGLED = dict(torso=-60, head=-25, fa_u=-100, fa_l=-130, ba_u=-70, ba_l=-110,
               fl_u=60, fl_l=20, bl_u=30, bl_l=-10, blade=-120)
LYING = dict(torso=-90, head=-8, fa_u=-100, fa_l=-110, ba_u=-80, ba_l=-90,
             fl_u=92, fl_l=95, bl_u=80, bl_l=88, x=0, blade=-95)
VICTORY = {"martial": dict(fa_u=165, fa_l=178, ba_u=20, ba_l=150, torso=-4, head=-10),
           "sword": dict(fa_u=150, fa_l=170, blade=182, ba_u=10, ba_l=40, torso=-2, head=-10)}


def alt_look(look):
    """같은 캐릭터 대전용 2P 색: 옷 색의 밝기를 뒤집어 한눈에 구분되게 한다."""
    def inv(c):
        return (int(255 - c[2] * 0.8), int(255 - c[1] * 0.8), int(255 - c[0] * 0.8))
    out = dict(look)
    for k in ("top", "pants", "sash", "band", "ribbon"):
        if k in look and look[k] != look["skin"]:
            out[k] = inv(look[k])
    if look.get("skirt"):
        out["skirt"] = dict(look["skirt"], color=inv(look["skirt"]["color"]))
    return out


def approach(cur, target, step):
    return min(cur + step, target) if cur < target else max(cur - step, target)


class Fighter:
    def __init__(self, pid, char, alt=False):
        self.pid = pid
        self.char = char
        self.style = char.style
        self.moves = char.moves
        self.body = char.body
        self.look = alt_look(char.look) if alt else char.look
        self.max_hp = char.hp
        self.super = 0
        self.wins = 0
        self.reset_round()

    def reset_round(self):
        self.pos = pygame.Vector2(START_X[self.pid], GROUND_Y)
        self.prev_pos = self.pos.copy()
        self.vel = pygame.Vector2()
        self.facing = 1 if self.pid == 1 else -1
        self.hp = self.max_hp
        self.state, self.state_frame = IDLE, 0
        self.move, self.move_frame = None, 0
        self.hit_slots = set()
        self.cancel_ok = False
        self.advancing = False
        self.stun = 0
        self.land_len = LAND_TICKS
        self.pending_lag = 0
        self.air_used = False
        self.air_locked = False
        self.buffer = InputBuffer()
        self.btn_buf = {}
        self.inp = EMPTY_INPUT
        self.juggle = 0
        self.combo_hits = 0
        self.combo_dmg = 0
        self.flash = 0
        self.freeze = 0
        self.events = []
        self.walk_phase = 0.0
        self.anim_t = 0
        self.hit_reaction = "high"
        self.guard_crouch = False
        self.at_wall = 0
        self.pose = self._base()
        self.prev_pose = dict(self.pose)
        self.blend_from, self.blend_len, self.blend_t = None, 0, 0
        self.trail = deque(maxlen=6)
        n = len(self.look.get("strands", []))
        self.strands, self.strand_prev = [None] * n, [None] * n
        self.hems = {}
        self.update_pose()

    # ── 상태 조회 ──
    @property
    def on_ground(self):
        return self.pos.y >= GROUND_Y and self.vel.y >= 0

    @property
    def in_combo(self):
        return self.state in (HITSTUN, JUGGLE)

    @property
    def threatening(self):
        """공격이 아직 나가는 중(선딜~지속)인가. AI가 막을지 판단할 때 쓴다."""
        return self.state == ATTACK and self.move_frame < self.move.startup + self.move.active

    @property
    def active(self):
        m = self.move
        return self.state == ATTACK and m.startup <= self.move_frame < m.startup + m.active

    @property
    def invulnerable(self):
        if self.state in (KNOCKDOWN, GETUP, KO, WIN):
            return True
        if self.state == JUGGLE and self.juggle >= JUGGLE_LIMIT:
            return True
        m = self.move
        return self.state == ATTACK and m.invuln is not None and m.invuln[0] <= self.move_frame < m.invuln[1]

    # ── 입력 ──
    def record_input(self, inp):
        """히트스톱 중에도 입력은 기록해서 버퍼가 동작하게 한다."""
        self.inp = inp
        self.buffer.push(numpad(inp.x * self.facing, inp.up, inp.down), inp.pressed)
        for b in inp.pressed:
            self.btn_buf[b] = BUTTON_BUFFER

    def _tick_buffers(self):
        for b in list(self.btn_buf):
            self.btn_buf[b] -= 1
            if self.btn_buf[b] <= 0:
                del self.btn_buf[b]

    def _change(self, state, blend=BLEND_TICKS):
        self.state = state
        self.state_frame = 0
        self.blend_from = dict(self.pose)
        self.blend_len, self.blend_t = blend, 0

    # ── 한 틱 진행 ──
    def hold(self):
        """히트스톱처럼 멈춰 있는 틱: 보간용 이전 값만 맞춘다."""
        self.prev_pos = self.pos.copy()
        self.prev_pose = self.pose

    def step(self):
        self.prev_pos = self.pos.copy()
        self.prev_pose = self.pose
        if self.freeze > 0:
            self.freeze -= 1
            return
        self.state_frame += 1
        self.anim_t += 1
        self.advancing = False
        handler = {IDLE: self._neutral, WALK: self._neutral, CROUCH: self._neutral, PREJUMP: self._prejump,
                   AIR: self._air, LAND: self._land, ATTACK: self._attack, HITSTUN: self._stunned,
                   BLOCKSTUN: self._stunned, JUGGLE: self._noop, KNOCKDOWN: self._knockdown,
                   GETUP: self._getup, KO: self._noop, WIN: self._noop}[self.state]
        handler()
        self._physics()
        self._tick_buffers()
        if self.flash > 0:
            self.flash -= 1
        # 포즈와 판정 상자는 밀어내기·방향 전환이 끝난 뒤 update_pose()에서 계산한다

    def _noop(self):
        pass

    def _neutral(self):
        inp = self.inp
        if self.try_attack():
            return
        if inp.up:
            self._change(PREJUMP, 2)
            return
        if inp.down:
            if self.state != CROUCH:
                self._change(CROUCH)
            self.vel.x = approach(self.vel.x, 0, GROUND_FRICTION)
            return
        x = inp.x
        if x:
            target = x * (WALK_FWD if x * self.facing > 0 else WALK_BACK) * self.char.speed
            if self.state != WALK:
                self._change(WALK)
        else:
            target = 0
            if self.state != IDLE:
                self._change(IDLE)
        self.vel.x = approach(self.vel.x, target, GROUND_ACCEL if x else GROUND_FRICTION)

    def _prejump(self):
        if self.state_frame >= PREJUMP_TICKS:
            self.vel.y = JUMP_VY
            self.vel.x = self.inp.x * JUMP_VX * self.char.speed
            self.pos.y -= 1
            self.air_used = False
            self.air_locked = False
            self._change(AIR, 3)
            self.events.append(("jump", None))

    def _air(self):
        if not self.air_locked:
            self.try_attack()

    def _land(self):
        if self.state_frame >= self.land_len:
            self._change(CROUCH if self.inp.down else IDLE)

    def _stunned(self):
        self.stun -= 1
        if self.stun <= 0:
            self._change(CROUCH if self.inp.down else IDLE)

    def _knockdown(self):
        if self.hp <= 0:
            self._change(KO, 6)
        elif self.state_frame >= KNOCKDOWN_TICKS:
            self._change(GETUP, 2)

    def _getup(self):
        if self.state_frame >= GETUP_TICKS:
            self._change(IDLE)

    def _attack(self):
        mv = self.move
        self.move_frame += 1
        f = self.move_frame
        if self.cancel_ok and f < mv.total - 1 and self.try_attack(cancel=True):
            return
        if mv.advance and mv.advance[0] <= f < mv.advance[1]:
            self.vel.x = mv.advance[2] * self.facing
            self.advancing = True
        if mv.impulse and f == mv.impulse[0]:
            self.vel.x = mv.impulse[1] * self.facing
            self.vel.y = mv.impulse[2]
            self.pos.y -= 1
        if f >= mv.total:
            if self.on_ground:
                self._change(CROUCH if self.inp.down else IDLE)
            else:
                self.air_used = True
                self.air_locked = mv.base != "air"
                self.pending_lag = mv.land_lag
                self._change(AIR, 6)

    # ── 공격 ──
    def try_attack(self, cancel=False):
        btn = next((b for b in ("punch", "kick") if self.btn_buf.get(b, 0) > 0), None)
        if btn is None:
            return False
        mv = self._resolve(btn, cancel)
        if mv is None:
            return False
        del self.btn_buf[btn]
        self.start_move(mv)
        return True

    def _resolve(self, btn, cancel):
        cur = self.move if cancel else None
        if not self.on_ground:
            if cancel or self.air_used or self.air_locked:
                return None
            return self.moves["jP" if btn == "punch" else "jK"]
        if (btn == "punch" and self.super >= SUPER_MAX and self.buffer.motion("236236") >= 0
                and (cur is None or cur.kind != "super")):
            return self.moves["super"]
        if cur is None or cur.kind in ("normal", "chain"):
            best = None
            for motion, b, key in SPECIAL_COMMANDS:
                if b == btn:
                    pos = self.buffer.motion(motion)
                    if pos >= 0 and (best is None or pos > best[0]):
                        best = (pos, key)
            if best:
                return self.moves[best[1]]
        if cancel:
            nxt = cur.chain.get(btn) if cur.kind in ("normal", "chain") else None
            return self.moves[nxt] if nxt else None
        b = "P" if btn == "punch" else "K"
        if self.inp.down:
            return self.moves["2" + b]
        if self.inp.x * self.facing > 0:
            return self.moves["6" + b]
        return self.moves["5" + b]

    def start_move(self, mv):
        self.move = mv
        self.move_frame = 0
        self.hit_slots = set()
        self.cancel_ok = False
        self.trail.clear()
        if self.on_ground:
            self.vel.x *= 0.3
        if mv.base == "air":
            self.air_used = True
        if mv.is_special:
            self.buffer.clear()
            self.events.append((mv.kind, mv))
        if mv.kind == "super":
            self.super -= SUPER_MAX
        self._change(ATTACK, 2)

    def hit_slot(self):
        """다단히트 기술에서 지금 몇 번째 타격 구간인지. 이미 맞힌 구간이면 None."""
        mv = self.move
        slot = (self.move_frame - mv.startup) // mv.interval if mv.interval else 0
        if slot in self.hit_slots or slot >= mv.hits:
            return None
        return slot

    # ── 피격 ──
    def is_guarding(self, attacker, mv):
        if self.state not in (IDLE, WALK, CROUCH, BLOCKSTUN) or not self.on_ground:
            return False
        toward = 1 if attacker.pos.x > self.pos.x else -1
        if self.inp.x != -toward:
            return False
        if mv.level == "low" and not self.inp.down:
            return False
        if mv.level == "overhead" and self.inp.down:
            return False
        return True

    def take_hit(self, attacker, mv):
        """맞거나 막는다. 'hit' 또는 'block'을 돌려준다."""
        d = 1 if self.pos.x >= attacker.pos.x else -1
        if abs(self.pos.x - attacker.pos.x) < 4:
            d = attacker.facing
        if self.is_guarding(attacker, mv):
            self.stun = mv.blockstun
            self.guard_crouch = self.inp.down
            self._change(BLOCKSTUN, 2)
            self.vel.x = mv.push * 0.9 * d
            if mv.is_special:
                self.hp = max(1, self.hp - int(mv.dmg * attacker.char.power * CHIP_RATE))
            self.super = min(SUPER_MAX, self.super + mv.dmg * 0.25)
            attacker.super = min(SUPER_MAX, attacker.super + mv.dmg * 0.2)
            return "block"

        if self.in_combo:
            self.combo_hits += 1
        else:
            self.combo_hits, self.combo_dmg = 1, 0
        scale = max(0.35, 1 - 0.1 * (self.combo_hits - 1))
        dmg = max(1, round(mv.dmg * attacker.char.power * scale))
        self.hp = max(0, self.hp - dmg)
        self.combo_dmg += dmg
        self.flash = 3
        if mv.level == "low":
            self.hit_reaction = "low"
        elif mv.strike in ("fl", "bl") and mv.level == "mid":
            self.hit_reaction = "body"
        else:
            self.hit_reaction = "high"

        if mv.launch or not self.on_ground or self.hp <= 0:
            lx, ly = mv.launch or (mv.push * 0.6, -6)
            if self.hp <= 0:
                lx, ly = max(lx, 5), min(ly, -9)
            self.vel.x, self.vel.y = lx * d, ly
            self.pos.y = min(self.pos.y, GROUND_Y - 1)
            self.juggle += 1
            self._change(JUGGLE, 3)
        else:
            self.stun = mv.hitstun
            self._change(HITSTUN, 2)
            self.vel.x = mv.push * d
        self.super = min(SUPER_MAX, self.super + dmg * 0.35)
        attacker.super = min(SUPER_MAX, attacker.super + dmg * 0.7)
        return "hit"

    def win(self):
        if self.state not in (KO,):
            self.move = None
            self._change(WIN, 10)

    # ── 물리 ──
    def _physics(self):
        airborne = self.pos.y < GROUND_Y or self.vel.y < 0
        if airborne:
            g = GRAVITY * (FALL_GRAVITY_MULT if self.vel.y > 0 else 1.0)
            if self.state == JUGGLE:
                g = GRAVITY * 0.8
            self.vel.y += g
        elif self.state in (HITSTUN, BLOCKSTUN, KNOCKDOWN, KO):
            self.vel.x = approach(self.vel.x, 0, HIT_FRICTION)
        elif self.state not in NEUTRAL and not self.advancing:
            self.vel.x = approach(self.vel.x, 0, GROUND_FRICTION)
        self.pos += self.vel
        landed = False
        if self.pos.y >= GROUND_Y:
            landed = airborne and self.vel.y >= 0
            self.pos.y = GROUND_Y
            self.vel.y = 0
        lo, hi = STAGE_LEFT + BODY_HALF_W, STAGE_RIGHT - BODY_HALF_W
        self.at_wall = 0
        if self.pos.x <= lo:
            self.pos.x, self.at_wall = lo, -1
        elif self.pos.x >= hi:
            self.pos.x, self.at_wall = hi, 1
        if self.at_wall and self.vel.x * self.at_wall > 0:
            self.vel.x = 0
        if landed:
            self._on_land()

    def _on_land(self):
        self.events.append(("land", None))
        if self.state == AIR:
            self.land_len = self.pending_lag or LAND_TICKS
            self.pending_lag = 0
            self.vel.x = 0
            self._change(LAND, 2)
        elif self.state == ATTACK:
            mv = self.move
            if mv.base == "air":
                self.land_len = LAND_TICKS
                self.vel.x = 0
                self._change(LAND, 2)
            elif mv.impulse and self.move_frame > mv.impulse[0]:
                self.land_len = mv.land_lag
                self.vel.x = 0
                self._change(LAND, 3)
        elif self.state == JUGGLE:
            self.juggle = 0
            self.vel.x *= 0.3
            self._change(KNOCKDOWN, 5)

    # ── 포즈 ──
    def _base(self, base="stand"):
        return skeleton.base_pose(self.style, base, self.char.stance)

    def _target_pose(self):
        st, f = self.state, self.state_frame
        stance = self._base()
        if st == ATTACK:
            return skeleton.move_pose(self.move, self.style, self.move_frame, self.char.stance, self.char.key)
        if st == IDLE:
            b = math.sin(self.anim_t * 0.08)
            stance["torso"] += b * 1.5
            stance["fa_l"] += b * 3
            stance["ba_l"] += b * 3
            stance["blade"] += b * 2
            return stance
        if st == WALK:
            self.walk_phase += self.vel.x * self.facing * 0.075
            s, c = math.sin(self.walk_phase), math.cos(self.walk_phase)
            stance["fl_u"] = 20 + 16 * s
            stance["fl_l"] = stance["fl_u"] - 6 - 22 * max(0.0, c)
            stance["bl_u"] = -14 - 16 * s
            stance["bl_l"] = stance["bl_u"] - 6 - 22 * max(0.0, -c)
            stance["torso"] += 2 + 1.5 * abs(s)
            # 걸음에 맞춰 팔도 살짝 흔든다(무기를 든 손은 조금만)
            swing = 3 if self.style == "sword" else 7
            stance["fa_u"] += swing * s
            stance["ba_u"] -= swing * s
            stance["head"] += 1.5 * c
            return stance
        if st == CROUCH:
            p = self._base("crouch")
            p["torso"] += math.sin(self.anim_t * 0.08) * 1.2
            return p
        if st == PREJUMP:
            return skeleton.lerp_pose(stance, self._base("crouch"), 0.6)
        if st == AIR:
            p = self._base("air")
            if self.vel.y > 4:  # 내려올 때는 다리를 펴서 착지 준비
                p.update(fl_u=40, fl_l=10, bl_u=10, bl_l=-20)
            return p
        if st == LAND:
            k = 0.6 * (1 - f / max(1, self.land_len))
            return skeleton.lerp_pose(stance, self._base("crouch"), max(0.0, k))
        if st == BLOCKSTUN:
            p = self._base("crouch" if self.guard_crouch else "stand")
            p.update(GUARD[self.style])
            p["x"] -= 4
            return p
        if st == HITSTUN:
            p = dict(stance)
            p.update(HURT[self.hit_reaction])
            back = min(1.0, self.stun / 8)  # 경직이 끝나갈수록 자세를 되찾는다
            return skeleton.lerp_pose(stance, p, back)
        if st == JUGGLE:
            p = dict(stance)
            p.update(JUGGLED)
            return p
        if st in (KNOCKDOWN, KO):
            p = dict(stance)
            p.update(LYING)
            return p
        if st == GETUP:
            lying = dict(stance)
            lying.update(LYING)
            return skeleton.lerp_pose(lying, self._base("crouch"),
                                      skeleton.smoothstep(min(1.0, f / GETUP_TICKS)))
        if st == WIN:
            p = dict(stance)
            p.update(VICTORY[self.style])
            return skeleton.lerp_pose(stance, p, skeleton.smoothstep(min(1.0, f / 24)))
        return stance

    @property
    def grounded_pose(self):
        return self.on_ground and self.state not in (JUGGLE, AIR)

    def update_pose(self):
        target = self._target_pose()
        if self.blend_from is not None and self.blend_t < self.blend_len:
            self.blend_t += 1
            target = skeleton.lerp_pose(self.blend_from, target,
                                        skeleton.smoothstep(self.blend_t / self.blend_len), wrap_spin=True)
        self.pose = target
        self.joints = skeleton.compute_joints(target, self.body, self.facing, self.pos.x, self.pos.y,
                                              self.grounded_pose)
        self.hurt = skeleton.hurtbox(self.joints, self.body)
        self.hit = None
        if self.state == ATTACK:
            mv = self.move
            if self.active:
                self.hit = skeleton.hitbox(self.joints, mv.strike, mv.reach)
                if mv.no_push:  # 상대를 꿰뚫고 지나가는 기술은 몸이 스치는 것도 맞는다
                    self.hit.append(self.hurt.copy())
            if mv.startup - 1 <= self.move_frame < mv.startup + mv.active + 2:
                self.trail.append(skeleton.strike_segment(self.joints, mv.strike))
            elif self.trail:
                self.trail.popleft()
        elif self.trail:
            self.trail.popleft()
        self._update_cloth()

    def _update_cloth(self):
        """가닥(머리카락·리본·띠 끝)은 베를레 줄 물리로, 옷자락 단은 용수철로 몸을 늦게 따라온다."""
        j = self.joints
        for i, spec in enumerate(self.look.get("strands", [])):
            root = costume.anchor(j, self.body, spec)
            n, seg = spec["n"], spec["seg"]
            pts, prev = self.strands[i], self.strand_prev[i]
            if pts is None:
                pts = [[root[0] - self.facing * seg * k * 0.7, root[1] + seg * k * 0.7] for k in range(n)]
                prev = [p[:] for p in pts]
                self.strands[i], self.strand_prev[i] = pts, prev
            bias, grav = spec.get("bias", 0.3), spec.get("grav", 0.6)
            for k in range(1, n):
                p, q = pts[k], prev[k]
                vx, vy = (p[0] - q[0]) * 0.88, (p[1] - q[1]) * 0.88
                q[0], q[1] = p[0], p[1]
                p[0] += vx - self.facing * bias   # 가만히 있을 때는 등 뒤로 살짝 흐른다
                p[1] += vy + grav
            pts[0][0], pts[0][1] = root
            for _ in range(3):
                for k in range(1, n):
                    a, b = pts[k - 1], pts[k]
                    dx, dy = b[0] - a[0], b[1] - a[1]
                    d = math.hypot(dx, dy) or 1
                    c = (d - seg) / d
                    b[0] -= dx * c
                    b[1] = min(GROUND_Y - 2, b[1] - dy * c)
        spec = self.look.get("skirt")
        if not spec:
            return
        for side in ("f", "b"):
            targets = costume.skirt_target(j, self.body, spec, side)
            hem = self.hems.get(side)
            if hem is None:
                hem = self.hems[side] = [[t[0], t[1], 0.0, 0.0] for t in targets]
            for p, t in zip(hem, targets):
                p[2] = (p[2] + (t[0] - p[0]) * 0.32) * 0.6
                p[3] = (p[3] + (t[1] - p[1]) * 0.32) * 0.6
                p[0] += p[2]
                p[1] += p[3]
                # 너무 멀리 뒤처지면 천이 찢어져 보이므로 끌어당긴다
                dx, dy = p[0] - t[0], p[1] - t[1]
                d = math.hypot(dx, dy)
                if d > 26:
                    p[0], p[1] = t[0] + dx * 26 / d, t[1] + dy * 26 / d
                p[1] = min(p[1], GROUND_Y - 1)

    # ── 그리기 ──
    def draw(self, surf, alpha, view, ox=0, oy=0):
        """view(카메라)로 확대·이동해서 그린다. ox, oy는 화면에서 덧붙일 흔들림."""
        pos = self.prev_pos.lerp(self.pos, alpha)
        pose = skeleton.lerp_pose(self.prev_pose, self.pose, alpha, wrap_spin=True)
        sx, sy = view.to_screen(pos)
        j = skeleton.compute_joints(pose, self.body, self.facing, sx + ox, sy + oy, self.grounded_pose, view.zoom)
        # 물리로 움직이는 가닥·옷자락은 틱 단위 세계 좌표라서, 보간된 몸 위치만큼 옮긴 뒤 화면으로 바꾼다
        dx, dy = pos.x - self.pos.x, pos.y - self.pos.y

        def T(p):
            x, y = view.to_screen((p[0] + dx, p[1] + dy))
            return (x + ox, y + oy)
        strands = []
        for spec, pts in zip(self.look.get("strands", []), self.strands):
            strands.append(None if pts is None else [costume.anchor(j, self.body, spec)] + [T(p) for p in pts[1:]])
        hems = {s: tuple(T(p) for p in h) for s, h in self.hems.items()}
        costume.draw_figure(surf, j, self.look, self.body, dict(strands=strands, hems=hems), flash=self.flash > 0)
        return j
