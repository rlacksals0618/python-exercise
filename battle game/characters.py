"""캐릭터 4명: 검(남, 중국풍), 검(여, 일본풍), 격투(남, 일본풍), 격투(여, 중국풍).

같은 유형(검/격투)은 기술 목록을 공유하고, 체격·속도·공격력·체력·의상이 다르다.
look의 strands는 몸을 따라 흔들리는 가닥(머리카락·리본·띠 끝)이고,
skirt는 다리를 따라 출렁이는 옷자락(도포·하카마·상의 자락)이다.
"""
from moves import MOVESETS

BODY_MALE = dict(torso=58, neck=8, head=13, ua=30, fa=28, th=42, sh=44, foot=15,
                 w_ua=13, w_fa=11, w_th=17, w_sh=13, sh_w=30, chest_w=30, waist_w=23, hip_w=25)
BODY_FEMALE = dict(torso=54, neck=8, head=12.5, ua=28, fa=26, th=41, sh=43, foot=14,
                   w_ua=11, w_fa=9, w_th=15, w_sh=11, sh_w=24, chest_w=25, waist_w=17, hip_w=25)


def hair_strand(at, n, seg, w, color="hair", **kw):
    return dict(anchor="head", at=at, n=n, seg=seg, w=w, color=color, **kw)


class Character:
    def __init__(self, key, name, style, gender, body, look, hp, speed, power, blurb, stance=None):
        self.key, self.name, self.style, self.gender = key, name, style, gender
        self.body = dict(body)
        if style == "sword":
            self.body["blade"] = 84 if gender == "male" else 76
        self.look = look
        self.hp, self.speed, self.power = hp, speed, power
        self.blurb = blurb
        self.stance = stance or {}   # 기본 자세에서 이 캐릭터만 다르게 둘 관절 각도
        self.moves = MOVESETS[style]

    @property
    def style_name(self):
        return "검술" if self.style == "sword" else "격투술"

    @property
    def effect(self):
        return "slash" if self.style == "sword" else "fist"


CHARACTERS = [
    # 무진: 중국풍 무협 도포, 상투와 금관, 등까지 내려오는 긴 머리, 술 달린 직검
    Character("mujin", "무진", "sword", "male", BODY_MALE, dict(
        skin=(226, 184, 150), hair=(30, 26, 34), eye=(60, 40, 34), fierce=True, hair_style="topknot",
        top=(46, 66, 116), inner=(238, 234, 224), trim=(216, 178, 84), sleeve="wide", collar="hanfu",
        sash=(170, 38, 40), sash_w=8, trim_sash=True, bulk=1.08,
        skirt=dict(color=(46, 66, 116), length=1.6, flare=19, trim=True),
        pants=(38, 34, 44), feet="boot", boot=(30, 28, 34),
        weapon="jian", hilt=(70, 40, 32),
        strands=[hair_strand((-0.8, -0.1), 7, 8.5, (15, 6), bias=0.25),
                 dict(anchor="pommel", n=4, seg=6, w=(3, 3), color=(170, 38, 40), layer="front", tuft=7, bias=0),
                 dict(anchor="belt_front", at=(0.9, 4), n=4, seg=6, w=(3, 3), color=(170, 38, 40), layer="front",
                      tuft=6, bias=0)]),
        hp=1050, speed=1.0, power=1.08, blurb="묵직한 일격의 검객",
        stance=dict(fa_u=30, fa_l=120, blade=168, ba_u=72, ba_l=86)),
    # 설아: 일본풍 흰 고소데 + 보라 하카마, 붉은 다스키, 높게 묶은 말총머리, 카타나
    Character("seola", "설아", "sword", "female", BODY_FEMALE, dict(
        skin=(242, 210, 184), hair=(30, 24, 36), eye=(84, 52, 96), hair_style="ponytail", ribbon=(112, 70, 152),
        top=(244, 242, 246), inner=(232, 230, 238), tasuki=(196, 44, 52), trim=(240, 238, 244), sleeve="tied",
        collar="kimono", sash=(112, 70, 152), sash_w=8,
        skirt=dict(color=(112, 70, 152), length=1.92, flare=21, pleats=True),
        pants=(112, 70, 152), feet="zori", weapon="katana", saya=(36, 30, 40),
        strands=[hair_strand((-0.6, -0.95), 8, 8, (13, 4), bias=0.35),
                 hair_strand((-0.8, -1.1), 4, 6, (5, 2), color="ribbon", bias=0.3),
                 dict(anchor="belt_front", at=(1.0, 4), n=3, seg=7, w=(4, 3), color=(240, 238, 244), layer="front",
                      bias=0)]),
        hp=950, speed=1.12, power=0.95, blurb="빠르고 날렵한 검객",
        stance=dict(fa_u=34, fa_l=118, blade=172, ba_u=40, ba_l=112)),
    # 강혁: 일본풍 도복과 검은 띠, 붉은 머리띠(하치마키), 맨발
    Character("ganghyuk", "강혁", "martial", "male", BODY_MALE, dict(
        skin=(214, 166, 126), hair=(26, 22, 26), eye=(50, 34, 28), fierce=True, hair_style="spiky",
        band=(204, 38, 40), top=(244, 242, 234), sleeve="gi", collar="gi", sash=(30, 28, 32), sash_w=8,
        pants=(244, 242, 234), leg_w=1.3, feet="bare", bulk=1.12,
        strands=[hair_strand((-1.0, -0.4), 6, 8, (6, 4), color="band", bias=0.35),
                 hair_strand((-1.0, -0.3), 5, 8, (5, 3), color="band", bias=0.2),
                 dict(anchor="belt_front", at=(1.0, 4), n=3, seg=8, w=(7, 6), color=(30, 28, 32), layer="front",
                      bias=0),
                 dict(anchor="belt_front", at=(0.7, 4), n=3, seg=8, w=(7, 6), color=(30, 28, 32), layer="front",
                      bias=0)]),
        hp=1080, speed=0.97, power=1.1, blurb="강철 주먹의 격투가"),
    # 하린: 중국풍 무술복(차이나 칼라·매듭단추), 양쪽 쪽머리, 검은 바지와 천신발
    Character("harin", "하린", "martial", "female", BODY_FEMALE, dict(
        skin=(242, 208, 180), hair=(62, 36, 30), eye=(70, 44, 32), hair_style="buns", ribbon=(204, 52, 52),
        top=(30, 132, 116), trim=(230, 190, 84), cuff=(244, 242, 236), sleeve="cuffed", collar="mandarin",
        sash=(230, 190, 84), sash_w=6,
        skirt=dict(color=(30, 132, 116), length=0.42, flare=15, trim=True),
        pants=(34, 34, 46), leg_w=1.1, feet="shoe",
        strands=[hair_strand((-0.6, -0.75), 4, 7, (4, 2), color="ribbon", bias=0.3),
                 hair_strand((-0.3, -0.9), 4, 7, (4, 2), color="ribbon", bias=0.25),
                 dict(anchor="belt_back", at=(1.0, 4), n=3, seg=7, w=(5, 4), color=(230, 190, 84), layer="front",
                      bias=0)]),
        hp=940, speed=1.14, power=0.94, blurb="바람 같은 발차기의 격투가",
        stance=dict(ba_u=80, ba_l=88, fa_u=-15, fa_l=75)),
]
