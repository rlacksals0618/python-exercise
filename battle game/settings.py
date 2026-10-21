"""게임 전체에서 쓰는 상수 모음. 수치 조정은 이 파일에서 한다."""
import os

# ── 경로 ──
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(BASE_DIR, "assets", "fonts")
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
EFFECT_FILES = {"fist": "fist_effect.png", "foot": "foot_effect.png", "slash": "slash_effect.png"}

# ── 화면 ──
SCREEN_W, SCREEN_H = 1280, 720
FPS = 60                # 로직은 항상 초당 60틱으로 돈다
CAPTION = "권 · 족 · 참"

# ── 무대 ──
GROUND_Y = 640
STAGE_LEFT, STAGE_RIGHT = 50, 1230
BODY_HALF_W = 22        # 캐릭터끼리 밀어낼 때 쓰는 몸통 반폭
START_X = {1: 440, 2: 840}

# ── 카메라: 게임 세계(위 좌표)를 2배로 확대해서 보여준다 ──
ZOOM = 2.0
GROUND_SCREEN = 650     # 화면에서 바닥선의 높이
VIEW_HALF = SCREEN_W / 2 / ZOOM
CAM_MIN_X, CAM_MAX_X = STAGE_LEFT + VIEW_HALF, STAGE_RIGHT - VIEW_HALF
MAX_SEPARATION = VIEW_HALF * 2 - 80   # 둘 다 화면 안에 보이도록 벌어질 수 있는 최대 거리

# ── 이동 물리 (단위: px/틱) ──
WALK_FWD = 4.0          # 앞으로 걷기
WALK_BACK = 3.0         # 뒤로 걷기는 조금 느리게
GROUND_ACCEL = 1.1      # 약 4틱 만에 최고 속도
GROUND_FRICTION = 1.0
HIT_FRICTION = 0.55     # 맞고 밀려날 때의 마찰
JUMP_VY = -17.5
JUMP_VX = 4.6
GRAVITY = 0.9
FALL_GRAVITY_MULT = 1.4 # 내려올 때 중력을 키워 둥둥 뜨는 느낌을 줄인다
PREJUMP_TICKS = 4
LAND_TICKS = 4
KNOCKDOWN_TICKS = 42
GETUP_TICKS = 18
BLEND_TICKS = 4         # 상태가 바뀔 때 포즈를 섞는 틱 수

# ── 전투 규칙 ──
ROUND_TIME = 99
ROUNDS_TO_WIN = 2
SUPER_MAX = 1000
BUTTON_BUFFER = 6       # 경직 중에 누른 공격키를 기억하는 틱 수
MOTION_WINDOW = 20      # ↓↘→ 같은 방향 입력을 찾는 범위(틱)
SUPER_WINDOW = 34
JUGGLE_LIMIT = 4        # 공중 콤보 최대 타수
CHIP_RATE = 0.15        # 필살기를 막았을 때 깎이는 체력 비율

# 기술 강도(1~5)별 연출: 히트스톱 틱, 화면 흔들림, 이펙트 크기(px)
HITSTOP = {1: 5, 2: 7, 3: 9, 4: 12, 5: 18}
SHAKE = {1: 0, 2: 2, 3: 4, 4: 7, 5: 12}
EFFECT_SIZE = {1: 150, 2: 190, 3: 240, 4: 300, 5: 520}   # 확대 전 기준 크기

# ── 색 ──
INK = (24, 22, 28)
PAPER = (238, 230, 212)
WHITE = (250, 248, 240)
GOLD = (236, 196, 92)
P_COLORS = {1: (80, 150, 255), 2: (240, 80, 80)}
EFFECT_COLORS = {"fist": (225, 45, 40), "foot": (60, 200, 90), "slash": (170, 85, 235)}
