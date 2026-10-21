"""기술 데이터: 프레임 데이터(선딜·지속·후딜)와 동작 키프레임.

포즈 각도 규칙(오른쪽을 볼 때 기준, 단위 도):
    0 = 똑바로 아래, 90 = 앞으로 수평, 180 = 똑바로 위, -90 = 뒤로 수평
    torso: 몸통 기울기(+는 앞으로 숙임), spin: 몸을 도는 각도(180이면 등을 보임)
    fa/ba = 앞팔/뒷팔, fl/bl = 앞다리/뒷다리, _u = 윗마디, _l = 아랫마디
    blade = 칼날 방향, x/y = 엉덩이 위치 보정(px)
강한 기술일수록 선딜(startup)과 후딜(recovery)이 길다.
"""

POSE_KEYS = ("x", "y", "torso", "head", "fa_u", "fa_l", "ba_u", "ba_l",
             "fl_u", "fl_l", "bl_u", "bl_l", "spin", "blade")

STANCE = {
    "martial": dict(x=0, y=0, torso=6, head=0, fa_u=35, fa_l=150, ba_u=15, ba_l=160,
                    fl_u=26, fl_l=2, bl_u=-20, bl_l=-26, spin=0, blade=0),
    "sword": dict(x=0, y=0, torso=4, head=0, fa_u=38, fa_l=88, ba_u=12, ba_l=70,
                  fl_u=24, fl_l=0, bl_u=-22, bl_l=-26, spin=0, blade=100),
}
CROUCH = dict(torso=32, fl_u=85, fl_l=-25, bl_u=30, bl_l=-75)
CROUCH_SWORD = dict(CROUCH, fa_u=55, fa_l=80, blade=75)
AIR = dict(torso=8, fl_u=70, fl_l=-15, bl_u=30, bl_l=-70)

# 공격 부위 → 이펙트 종류 (팔 = 拳, 발 = 足, 검 = 斬)
STRIKE_EFFECT = {"fa": "fist", "ba": "fist", "fl": "foot", "bl": "foot", "blade": "slash"}


class Move:
    def __init__(self, key, name, startup, active, recovery, dmg, strike, keys, *,
                 hitstun=16, blockstun=None, push=4.0, level="mid", reach=26, tier=1,
                 base="stand", knockdown=False, launch=None, hits=1, interval=0,
                 advance=None, impulse=None, invuln=None, land_lag=0, chain=None,
                 kind="normal", no_push=False, command="", desc=""):
        self.key, self.name = key, name
        self.startup, self.active, self.recovery = startup, active, recovery
        self.total = startup + active + recovery
        self.dmg, self.strike, self.keys = dmg, strike, keys
        self.hitstun = hitstun
        self.blockstun = blockstun if blockstun is not None else max(6, hitstun - 5)
        self.push, self.level, self.reach, self.tier = push, level, reach, tier
        self.base = base                  # "stand" / "crouch" / "air"
        self.knockdown = knockdown
        self.launch = launch              # 맞은 쪽을 띄우는 속도 (vx, vy)
        self.hits, self.interval = hits, interval
        self.advance = advance            # (시작틱, 끝틱, 속도): 그 동안 앞으로 이동
        self.impulse = impulse            # (틱, vx, vy): 그 틱에 몸을 띄움
        self.invuln = invuln              # (시작틱, 끝틱): 무적
        self.land_lag = land_lag
        self.chain = chain or {}          # 맞혔을 때 이어지는 기술 {"punch": 기술키}
        self.kind = kind                  # normal / chain / special / super
        self.no_push = no_push
        self.command = command            # 기술표 표시용 (예: "236P")
        self.desc = desc
        self.effect = STRIKE_EFFECT[strike]

    @property
    def is_special(self):
        return self.kind in ("special", "super")


def K(frame, **pose):
    return (frame, pose)


def _martial():
    m = {}
    # ── 기본기 ──
    m["5P"] = Move("5P", "잽", 4, 2, 8, 40, "fa", [
        K(0), K(2, fa_u=55, fa_l=125, torso=9),
        K(4, fa_u=88, fa_l=90, torso=14, x=5), K(6, fa_u=88, fa_l=90, torso=14, x=5), K(14)],
        hitstun=18, push=2.0, level="high", reach=26, chain={"punch": "hook"}, command="P",
        desc="가장 빠른 견제기")
    m["5K"] = Move("5K", "앞차기", 7, 3, 13, 55, "fl", [
        K(0), K(4, fl_u=75, fl_l=-25, torso=-4, bl_u=-8, bl_l=-12),
        K(7, fl_u=88, fl_l=94, torso=-12, x=3, bl_u=-10, bl_l=-14),
        K(10, fl_u=88, fl_l=94, torso=-12, x=3, bl_u=-10, bl_l=-14), K(23)],
        hitstun=20, push=3.0, reach=26, chain={"kick": "mkick"}, command="K")
    m["2P"] = Move("2P", "앉아 지르기", 5, 2, 10, 40, "fa", [
        K(0), K(3, fa_u=60, fa_l=100), K(5, fa_u=92, fa_l=88, torso=36, x=4),
        K(7, fa_u=92, fa_l=88, torso=36, x=4), K(17)],
        hitstun=17, push=2.5, base="crouch", command="2P")
    m["2K"] = Move("2K", "다리 쓸기", 9, 4, 22, 70, "fl", [
        K(0), K(5, fl_u=60, fl_l=20, bl_u=20, bl_l=-90, torso=35, fa_u=60, fa_l=30, ba_u=-30, ba_l=0),
        K(9, fl_u=84, fl_l=88, bl_u=20, bl_l=-90, torso=30, x=6, fa_u=50, fa_l=20, ba_u=-40, ba_l=-10),
        K(13, fl_u=86, fl_l=90, bl_u=20, bl_l=-90, torso=30, x=6, fa_u=50, fa_l=20, ba_u=-40, ba_l=-10),
        K(35)],
        level="low", reach=22, tier=2, base="crouch", knockdown=True, launch=(2.5, -6),
        command="2K", desc="하단. 맞으면 넘어진다")
    m["6P"] = Move("6P", "정권 지르기", 12, 4, 20, 105, "ba", [
        K(0), K(8, torso=-6, ba_u=-45, ba_l=20, x=-6, fa_u=45, fa_l=140),
        K(12, torso=24, ba_u=92, ba_l=90, x=14, fa_u=-10, fa_l=40, fl_u=42, fl_l=8, bl_u=-38, bl_l=-34),
        K(16, torso=24, ba_u=92, ba_l=90, x=14, fa_u=-10, fa_l=40, fl_u=42, fl_l=8, bl_u=-38, bl_l=-34),
        K(36)],
        hitstun=22, push=7.0, reach=30, tier=3, advance=(6, 14, 3.0), command="6P",
        desc="한 걸음 들어가며 치는 강펀치")
    m["6K"] = Move("6K", "상단 돌려차기", 13, 3, 22, 100, "bl", [
        K(0), K(7, bl_u=60, bl_l=-25, torso=-15, spin=20),
        K(13, bl_u=112, bl_l=102, torso=-34, spin=30, fl_u=6, fl_l=0, fa_u=55, fa_l=125, ba_u=-45, ba_l=-15),
        K(16, bl_u=112, bl_l=102, torso=-34, spin=30, fl_u=6, fl_l=0, fa_u=55, fa_l=125, ba_u=-45, ba_l=-15),
        K(38)],
        hitstun=22, push=6.0, level="high", reach=30, tier=3, command="6K", desc="앉으면 피할 수 있다")
    m["jP"] = Move("jP", "공중 내려치기", 6, 9, 8, 65, "fa", [
        K(0), K(4, fa_u=165, fa_l=175, torso=0), K(6, fa_u=105, fa_l=55, torso=22),
        K(15, fa_u=95, fa_l=40, torso=26), K(23)],
        hitstun=18, push=3.0, level="overhead", reach=28, tier=2, base="air", command="점프 중 P")
    m["jK"] = Move("jK", "날아차기", 7, 8, 8, 75, "fl", [
        K(0), K(4, fl_u=40, fl_l=-60, bl_u=50, bl_l=-80),
        K(7, fl_u=65, fl_l=60, bl_u=30, bl_l=-100, torso=-10),
        K(15, fl_u=65, fl_l=60, bl_u=30, bl_l=-100, torso=-10), K(23)],
        hitstun=18, push=4.0, level="overhead", reach=26, tier=2, base="air", command="점프 중 K")

    # ── 연결기(콤보 2·3타) ──
    m["hook"] = Move("hook", "훅", 6, 3, 12, 55, "ba", [
        K(0), K(3, ba_u=-30, ba_l=60, torso=0, fa_u=30, fa_l=160),
        K(6, ba_u=88, ba_l=120, torso=20, x=8, fa_u=20, fa_l=150),
        K(9, ba_u=88, ba_l=120, torso=20, x=8, fa_u=20, fa_l=150), K(21)],
        hitstun=21, push=1.5, reach=28, tier=2, kind="chain", chain={"punch": "upper"})
    m["upper"] = Move("upper", "올려치기", 9, 3, 22, 80, "fa", [
        K(0), K(5, torso=28, fa_u=15, fa_l=70, ba_u=20, ba_l=150, fl_u=55, fl_l=-15, bl_u=-5, bl_l=-45),
        K(9, torso=0, fa_u=105, fa_l=140, x=12, fl_u=18, fl_l=4, bl_u=-22, bl_l=-14),
        K(12, torso=-10, fa_u=150, fa_l=172, x=10, fl_u=18, fl_l=4, bl_u=-22, bl_l=-14), K(34)],
        reach=32, tier=3, kind="chain", knockdown=True, launch=(2.0, -11.5), advance=(3, 9, 2.5))
    m["mkick"] = Move("mkick", "중단 돌려차기", 9, 3, 16, 70, "bl", [
        K(0), K(5, bl_u=45, bl_l=-35, torso=-8, fa_u=20, fa_l=140, ba_u=-20, ba_l=30),
        K(9, bl_u=98, bl_l=100, torso=-22, x=6, fl_u=4, fl_l=-2, fa_u=10, fa_l=130, ba_u=-40, ba_l=-20),
        K(12, bl_u=98, bl_l=100, torso=-22, x=6, fl_u=4, fl_l=-2, fa_u=10, fa_l=130, ba_u=-40, ba_l=-20),
        K(28)],
        hitstun=22, push=3.0, reach=28, tier=2, kind="chain", chain={"kick": "spinback"})
    m["spinback"] = Move("spinback", "뒤후려차기", 13, 4, 22, 100, "bl", [
        K(0), K(6, spin=110, torso=10, bl_u=-10, bl_l=-50, fl_u=15, fl_l=0),
        K(13, spin=180, torso=28, bl_u=-98, bl_l=-96, fl_u=8, fl_l=0, x=-4, fa_u=-20, fa_l=40, ba_u=30, ba_l=140),
        K(17, spin=180, torso=28, bl_u=-98, bl_l=-96, fl_u=8, fl_l=0, x=-4, fa_u=-20, fa_l=40, ba_u=30, ba_l=140),
        K(30, spin=300, torso=5), K(39, spin=360)],
        reach=30, tier=3, kind="chain", knockdown=True, launch=(5.0, -7))

    # ── 필살기 ──
    m["236P"] = Move("236P", "붕권", 15, 4, 26, 150, "fa", [
        K(0), K(9, torso=-12, fa_u=-35, fa_l=30, ba_u=-25, ba_l=40, x=-10, fl_u=40, fl_l=-10, bl_u=-10, bl_l=-40),
        K(15, torso=32, fa_u=94, fa_l=92, ba_u=-70, ba_l=-50, x=22, fl_u=62, fl_l=14, bl_u=-55, bl_l=-55),
        K(19, torso=32, fa_u=94, fa_l=92, ba_u=-70, ba_l=-50, x=22, fl_u=62, fl_l=14, bl_u=-55, bl_l=-55),
        K(45)],
        reach=34, tier=4, knockdown=True, launch=(6.0, -6), advance=(9, 18, 7.0), kind="special",
        command="236P", desc="크게 파고드는 일격")
    m["623P"] = Move("623P", "승룡권", 7, 10, 24, 140, "fa", [
        K(0, torso=25, fa_u=20, fa_l=70, fl_u=60, fl_l=-20, bl_u=0, bl_l=-50),
        K(6, torso=4, fa_u=95, fa_l=125, ba_u=-20, ba_l=30, x=16, fl_u=70, fl_l=-40, bl_u=-10, bl_l=-8),
        K(10, torso=-5, fa_u=145, fa_l=165, ba_u=-20, ba_l=30, x=14, fl_u=70, fl_l=-40, bl_u=-10, bl_l=-8),
        K(17, torso=-5, fa_u=165, fa_l=176, ba_u=-20, ba_l=30, x=14, fl_u=70, fl_l=-40, bl_u=-10, bl_l=-8),
        K(41, **AIR)],
        reach=40, tier=4, knockdown=True, launch=(2.0, -14), impulse=(6, 2.5, -15), invuln=(0, 8),
        advance=(1, 6, 3.0),
        land_lag=14, kind="special", command="623P", desc="무적 대공기. 빗나가면 위험")
    m["236K"] = Move("236K", "선풍각", 12, 18, 18, 45, "fl", [
        K(0), K(8, fl_u=60, fl_l=-30, torso=-5, spin=-30),
        K(12, fl_u=92, fl_l=92, bl_u=-4, bl_l=-4, torso=-10, spin=0, fa_u=-70, fa_l=-80, ba_u=100, ba_l=110),
        K(30, fl_u=92, fl_l=92, bl_u=-4, bl_l=-4, torso=-10, spin=1080, fa_u=-70, fa_l=-80, ba_u=100, ba_l=110),
        K(48, spin=1080)],
        hitstun=16, push=2.5, reach=28, tier=3, hits=3, interval=6, advance=(10, 30, 3.5),
        kind="special", command="236K", desc="회전하며 전진하는 3연타")
    m["214K"] = Move("214K", "낙뢰각", 18, 4, 20, 130, "fl", [
        K(0), K(12, fl_u=172, fl_l=178, torso=-25, fa_u=-60, fa_l=-40, ba_u=70, ba_l=100, bl_u=-6, bl_l=-8),
        K(18, fl_u=128, fl_l=112, torso=0, x=8, fa_u=40, fa_l=150, ba_u=10, ba_l=160),
        K(22, fl_u=70, fl_l=40, torso=20, x=12), K(26, fl_u=45, fl_l=15, torso=22, x=12), K(42)],
        hitstun=28, push=5.0, level="overhead", reach=32, tier=4, advance=(4, 18, 2.0),
        kind="special", command="214K", desc="서서 막아야 하는 내려찍기")
    m["214P"] = Move("214P", "장타", 11, 3, 18, 90, "fa", [
        K(0), K(7, torso=-8, fa_u=-20, fa_l=60, ba_u=-25, ba_l=70, x=-5, fl_u=35, fl_l=-10, bl_u=-30, bl_l=-30),
        K(11, torso=20, fa_u=90, fa_l=92, ba_u=84, ba_l=86, x=16, fl_u=50, fl_l=12, bl_u=-40, bl_l=-38),
        K(14, torso=20, fa_u=90, fa_l=92, ba_u=84, ba_l=86, x=16, fl_u=50, fl_l=12, bl_u=-40, bl_l=-38),
        K(32)],
        hitstun=22, push=15.0, reach=32, tier=3, kind="special", command="214P", desc="크게 밀어내는 양손 장타")
    m["super"] = Move("super", "천붕권", 20, 6, 40, 300, "fa", [
        K(0), K(12, torso=-15, fa_u=-60, fa_l=-10, ba_u=-60, ba_l=-20, x=-12, fl_u=50, fl_l=-20, bl_u=0, bl_l=-50),
        K(20, torso=35, fa_u=95, fa_l=92, ba_u=90, ba_l=95, x=26, fl_u=65, fl_l=15, bl_u=-60, bl_l=-60),
        K(26, torso=35, fa_u=95, fa_l=92, ba_u=90, ba_l=95, x=26, fl_u=65, fl_l=15, bl_u=-60, bl_l=-60),
        K(66)],
        hitstun=40, reach=44, tier=5, knockdown=True, launch=(9.0, -10), advance=(12, 26, 9.0),
        invuln=(0, 20), kind="super", command="236236P", desc="필살 게이지 MAX 필요")
    return m


def _sword():
    m = {}
    m["5P"] = Move("5P", "가로베기", 5, 3, 10, 48, "blade", [
        K(0), K(3, fa_u=5, fa_l=150, blade=170, torso=0),
        K(5, fa_u=85, fa_l=92, blade=96, torso=14, x=5), K(8, fa_u=88, fa_l=95, blade=110, torso=14, x=5),
        K(18)],
        hitstun=18, push=2.5, reach=18, chain={"punch": "rev"}, command="P", desc="검의 긴 사거리 견제")
    m["5K"] = Move("5K", "앞차기", 7, 3, 13, 55, "fl", [
        K(0), K(4, fl_u=75, fl_l=-25, torso=-4, bl_u=-8, bl_l=-12),
        K(7, fl_u=88, fl_l=94, torso=-12, x=3, bl_u=-10, bl_l=-14),
        K(10, fl_u=88, fl_l=94, torso=-12, x=3, bl_u=-10, bl_l=-14), K(23)],
        hitstun=20, push=3.0, reach=26, chain={"kick": "6K"}, command="K")
    m["2P"] = Move("2P", "하단 베기", 6, 3, 12, 45, "blade", [
        K(0), K(3, fa_u=20, fa_l=120, blade=150),
        K(6, fa_u=80, fa_l=70, blade=70, torso=36, x=4), K(9, fa_u=82, fa_l=60, blade=55, torso=36, x=4),
        K(21)],
        hitstun=17, push=2.5, level="low", reach=16, base="crouch", command="2P", desc="하단")
    m["2K"] = Move("2K", "다리 쓸기", 9, 4, 22, 70, "fl", [
        K(0), K(5, fl_u=60, fl_l=20, bl_u=20, bl_l=-90, torso=35, fa_u=60, fa_l=30, blade=-60),
        K(9, fl_u=84, fl_l=88, bl_u=20, bl_l=-90, torso=30, x=6, fa_u=50, fa_l=20, blade=-70),
        K(13, fl_u=86, fl_l=90, bl_u=20, bl_l=-90, torso=30, x=6, fa_u=50, fa_l=20, blade=-70), K(35)],
        level="low", reach=22, tier=2, base="crouch", knockdown=True, launch=(2.5, -6),
        command="2K", desc="하단. 맞으면 넘어진다")
    m["6P"] = Move("6P", "찌르기", 10, 4, 18, 90, "blade", [
        K(0), K(7, fa_u=20, fa_l=115, blade=92, x=-8, torso=-2),
        K(10, fa_u=90, fa_l=90, blade=90, torso=26, x=18, fl_u=44, fl_l=8, bl_u=-38, bl_l=-34),
        K(14, fa_u=90, fa_l=90, blade=90, torso=26, x=18, fl_u=44, fl_l=8, bl_u=-38, bl_l=-34), K(32)],
        hitstun=20, push=6.0, reach=16, tier=3, advance=(5, 12, 3.5), command="6P", desc="가장 긴 사거리")
    m["6K"] = Move("6K", "옆차기", 11, 3, 20, 85, "fl", [
        K(0), K(6, fl_u=105, fl_l=-10, torso=-20, bl_u=-10, bl_l=-12),
        K(11, fl_u=96, fl_l=94, torso=-38, x=6, bl_u=-14, bl_l=-16),
        K(14, fl_u=96, fl_l=94, torso=-38, x=6, bl_u=-14, bl_l=-16), K(34)],
        hitstun=22, push=3.0, reach=28, tier=3, chain={"punch": "down"}, command="6K")
    m["jP"] = Move("jP", "공중 베기", 6, 6, 10, 65, "blade", [
        K(0), K(3, fa_u=165, fa_l=170, blade=195), K(6, fa_u=100, fa_l=80, blade=110, torso=20),
        K(12, fa_u=70, fa_l=50, blade=50, torso=24), K(22)],
        hitstun=18, push=3.0, level="overhead", reach=20, tier=2, base="air", command="점프 중 P")
    m["jK"] = Move("jK", "날아차기", 7, 8, 8, 75, "fl", [
        K(0), K(4, fl_u=40, fl_l=-60, bl_u=50, bl_l=-80),
        K(7, fl_u=65, fl_l=60, bl_u=30, bl_l=-100, torso=-10),
        K(15, fl_u=65, fl_l=60, bl_u=30, bl_l=-100, torso=-10), K(23)],
        hitstun=18, push=4.0, level="overhead", reach=26, tier=2, base="air", command="점프 중 K")

    m["rev"] = Move("rev", "역베기", 7, 3, 13, 62, "blade", [
        K(0, fa_u=60, fa_l=50, blade=-30, torso=16), K(4, fa_u=35, fa_l=15, blade=-70, torso=18, x=4),
        K(7, fa_u=100, fa_l=110, blade=100, torso=4, x=6), K(10, fa_u=125, fa_l=145, blade=160, torso=-6, x=6),
        K(23)],
        hitstun=21, push=2.0, reach=20, tier=2, kind="chain", chain={"punch": "down"})
    m["down"] = Move("down", "내려베기", 11, 4, 22, 105, "blade", [
        K(0), K(7, fa_u=172, fa_l=178, ba_u=165, ba_l=172, blade=205, torso=-14, x=-4),
        K(11, fa_u=120, fa_l=120, ba_u=115, ba_l=120, blade=120, torso=20, x=8),
        K(15, fa_u=85, fa_l=70, ba_u=80, ba_l=70, blade=55, torso=30, x=12), K(37)],
        reach=22, tier=3, kind="chain", knockdown=True, launch=(4.0, -6))

    m["236P"] = Move("236P", "질풍참", 14, 6, 24, 140, "blade", [
        K(0), K(9, torso=35, fa_u=-40, fa_l=-20, blade=-120, x=-6, fl_u=55, fl_l=-15, bl_u=-10, bl_l=-55),
        K(14, torso=30, fa_u=92, fa_l=95, blade=92, x=24, fl_u=66, fl_l=16, bl_u=-60, bl_l=-60),
        K(20, torso=30, fa_u=92, fa_l=95, blade=100, x=24, fl_u=66, fl_l=16, bl_u=-60, bl_l=-60), K(44)],
        reach=22, tier=4, knockdown=True, launch=(6.0, -6), advance=(9, 20, 9.0), kind="special",
        command="236P", desc="순식간에 거리를 좁히는 돌진 베기")
    m["623P"] = Move("623P", "승천참", 8, 10, 24, 135, "blade", [
        K(0, torso=26, fa_u=30, fa_l=20, blade=-30, fl_u=60, fl_l=-20, bl_u=0, bl_l=-50),
        K(6, torso=12, fa_u=70, fa_l=80, blade=70, x=8, fl_u=65, fl_l=-30, bl_u=-5, bl_l=-20),
        K(8, torso=4, fa_u=100, fa_l=110, blade=100, x=12, fl_u=70, fl_l=-40, bl_u=-10, bl_l=-8),
        K(12, torso=-5, fa_u=140, fa_l=160, blade=150, x=12, fl_u=70, fl_l=-40, bl_u=-10, bl_l=-8),
        K(18, torso=-10, fa_u=160, fa_l=172, blade=178, x=12, fl_u=70, fl_l=-40, bl_u=-10, bl_l=-8),
        K(42, **AIR)],
        reach=24, tier=4, knockdown=True, launch=(2.0, -14), impulse=(9, 2.5, -15), invuln=(0, 9),
        land_lag=14, kind="special", command="623P", desc="무적 대공 베기. 빗나가면 위험")
    m["214P"] = Move("214P", "회전참", 10, 12, 18, 60, "blade", [
        K(0), K(6, torso=10, fa_u=-30, fa_l=-10, blade=-80, spin=-40),
        K(10, fa_u=90, fa_l=92, blade=92, torso=12, spin=0),
        K(22, fa_u=90, fa_l=92, blade=92, torso=12, spin=720), K(40, spin=720)],
        hitstun=18, push=3.5, reach=20, tier=3, hits=2, interval=6, advance=(10, 22, 2.5),
        kind="special", command="214P", desc="두 바퀴 돌며 2연속 베기")
    m["236K"] = Move("236K", "비연각", 9, 14, 6, 100, "fl", [
        K(0), K(6, fl_u=40, fl_l=-40, bl_u=-10, bl_l=-50, torso=20, blade=-100),
        K(9, fl_u=80, fl_l=78, bl_u=30, bl_l=-110, torso=-15, fa_u=-40, fa_l=-60, blade=-110, x=4),
        K(23, fl_u=80, fl_l=78, bl_u=30, bl_l=-110, torso=-15, fa_u=-40, fa_l=-60, blade=-110, x=4),
        K(29, **AIR)],
        hitstun=22, push=5.0, level="overhead", reach=28, tier=3, impulse=(8, 7.0, -11), land_lag=10,
        kind="special", command="236K", desc="날아올라 차는 중단")
    m["214K"] = Move("214K", "반월각", 16, 4, 20, 115, "bl", [
        K(0), K(8, bl_u=-50, bl_l=-60, torso=15, fl_u=30, fl_l=0),
        K(13, bl_u=60, bl_l=40, torso=-10), K(16, bl_u=150, bl_l=150, torso=-35, spin=15),
        K(20, bl_u=110, bl_l=95, torso=-30), K(40)],
        hitstun=26, push=6.0, reach=32, tier=4, kind="special", command="214K", desc="반달을 그리는 큰 발차기")
    m["super"] = Move("super", "일섬", 18, 5, 40, 300, "blade", [
        K(0), K(12, torso=38, fa_u=-20, fa_l=-30, ba_u=10, ba_l=60, blade=-110, x=-8,
                fl_u=65, fl_l=-20, bl_u=-10, bl_l=-60),
        K(18, torso=30, fa_u=95, fa_l=100, ba_u=-50, ba_l=-40, blade=100, x=30, fl_u=70, fl_l=20, bl_u=-62, bl_l=-62),
        K(23, torso=30, fa_u=95, fa_l=100, ba_u=-50, ba_l=-40, blade=100, x=30, fl_u=70, fl_l=20, bl_u=-62, bl_l=-62),
        K(63)],
        hitstun=40, reach=52, tier=5, knockdown=True, launch=(5.0, -9), advance=(18, 24, 22.0),
        invuln=(0, 24), no_push=True, kind="super", command="236236P", desc="필살 게이지 MAX 필요. 상대를 꿰뚫는 일격")
    return m


MOVESETS = {"martial": _martial(), "sword": _sword()}

# 필살기 판정 순서: 방향 명령, 버튼, 기술키
SPECIAL_COMMANDS = [("623", "punch", "623P"), ("236", "punch", "236P"), ("214", "punch", "214P"),
                    ("236", "kick", "236K"), ("214", "kick", "214K")]

# 기술표에 보여줄 콤보 목록 (이름, 입력, 시작 기술키)
COMBOS = {
    "martial": [("삼연권", "P → P → P", "5P"), ("삼연각", "K → K → K", "5K")],
    "sword": [("삼단베기", "P → P → P", "5P"), ("각검연격", "K → K → P", "5K")],
}
