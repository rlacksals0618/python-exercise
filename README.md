# Python Exercise

청년 피지컬 AI 과정에서 파이썬을 배우며 실습한 코드와, 직접 기획하고 만든 게임 두 개를 모은 저장소입니다.

| 폴더 | 내용 |
|---|---|
| [A-데이터 기초](#a-데이터-기초) | 간단한 파이썬 문법과 연산자 |
| [C-파이썬 기초](#c-파이썬-기초) | 각종 파이썬 명령어 실습 (문자열, 입력, 조건문, 리스트, 반복문, 함수) |
| [D-파이썬 심화](#d-파이썬-심화) | 파이썬 명령어 실습 (함수의 반환값과 인수, CSV 파일 읽기·쓰기) |
| [battle game](#battle-game--권--족--참) | 직접 구상하고 만든 2D 격투게임 |
| [mini project](#mini-project--바닷속-탈출) | 캐릭터를 움직여 높은 곳으로 올라가는 게임 |

### 실행 방법

파이썬 파일은 해당 폴더로 이동한 뒤 실행합니다. 폴더 이름에 띄어쓰기나 한글이 있으므로 경로를 따옴표로 감쌉니다.

```bash
cd "C-파이썬 기초"
python c03.py
```

VS Code에서는 파일을 열고 오른쪽 위의 ▶ 버튼을 눌러도 됩니다.

---

## A-데이터 기초

변수, 출력, 연산자 같은 가장 기본적인 파이썬 문법을 연습한 폴더입니다.

### [intro.py](A-데이터%20기초/intro.py)

변수에 값을 저장하고 `print()`로 출력합니다. 변수 이름을 출력하는 것과 따옴표로 감싼 문자열을 출력하는 것의 차이를 확인합니다.

```python
location = "입구"
temperature = 22.5

print(location)      # 입구        ← 변수에 저장된 값
print(temperature)   # 22.5
print("location")    # location    ← 따옴표 안의 글자 그대로
```

### [calculation.py](A-데이터%20기초/calculation.py)

재고 계산과 시험 점수 같은 예시로 파이썬의 연산자를 연습합니다. 줄마다 주석으로 계산 과정과 결과를 적어 두었습니다.

| 구분 | 명령어 | 예시 → 결과 |
|---|---|---|
| 사칙연산 | `+` `-` `*` `/` | `48 / 8` → `6.0` (나누기 결과는 항상 실수) |
| 정수 변환 | `int()` | `int(6.0)` → `6` |
| 몫과 나머지 | `//` `%` | `6 // 4` → `1`, `6 % 4` → `2` |
| 연산 순서 | `( )` | `2 + 3 * 4` → `14`, `(2 + 3) * 4` → `20` |
| 삼항 연산자 | `A if 조건 else B` | `"합격" if score >= 60 else "불합격"` → `합격` |
| 거듭제곱 | `**`, `pow()` | `3 ** 2` → `9`, `pow(2, 10)` → `1024` |
| 제곱근 | `math.sqrt()`, `** 0.5` | `math.sqrt(16)` → `4.0` |
| 반올림 | `round(값, 자릿수)` | `round(math.sqrt(2), 3)` → `1.414` |

`math.sqrt()`를 쓰려면 파일 맨 위에 `import math`가 필요합니다.

---

## C-파이썬 기초

문자열, 입력, 조건문, 리스트, 반복문, 함수 같은 파이썬 명령어를 하나씩 실습한 폴더입니다. 파일별 자세한 설명은 [C-파이썬 기초/README.md](C-파이썬%20기초/README.md)에 있습니다.

| 파일 | 주제 | 사용한 명령어 예시 |
|---|---|---|
| [c03.py](C-파이썬%20기초/c03.py) | 산술 연산 (온도 환산, 초 → 분·초) | `127 // 60` → `2`, `127 % 60` → `7` |
| [c04.py](C-파이썬%20기초/c04.py) | 변수와 자료형 | `name = "홍길동"`, `age = 25`, `temperature = 22.5`, `active = True` |
| [c05.py](C-파이썬%20기초/c05.py) | 문자열 길이, 인덱싱, 슬라이싱, 연결 | `len("S01")` → `3`, `sensor[0:2]` → `S0`, `"장치-" + sensor` |
| [c05_starter.py](C-파이썬%20기초/c05_starter.py) | f-string | `f"{name}님, {quantity}개 주문 금액은 {total}원입니다."` |
| [c06.py](C-파이썬%20기초/c06.py) | 입력과 형 변환 | `first = input("첫째 수: ")`, `int(first)` |
| [c07.py](C-파이썬%20기초/c07.py) | 문자열 메서드 | `"  START  ".strip()` → `START`, `.lower()` → `start` |
| [c08.py](C-파이썬%20기초/c08.py) | 비교 연산자 | `>` `>=` `<` `<=` `==` `!=` → `True` / `False` |
| [c09.py](C-파이썬%20기초/c09.py) | `if` / `else` (홀짝 판정) | `if number % 2 == 0:` |
| [c09_starter.py](C-파이썬%20기초/c09_starter.py) | `if` / `elif` / `else` (학점 판정) | `elif score >= 90:`, `score < 0 or score > 100` |
| [c09_work.py](C-파이썬%20기초/c09_work.py) | 조건문 응용 (초과 근무 급여) | `money = 1.5*pay*(hour-40) + pay*40` |
| [c10.py](C-파이썬%20기초/c10.py) | 리스트 수정과 추가 | `temperatures[1] = 25`, `temperatures.append(26)` |
| [c11.py](C-파이썬%20기초/c11.py) | `for` 반복문 + 조건문 | `for score in scores:` |
| [c11(2).py](<C-파이썬 기초/c11(2).py>) | 중첩 반복문 (구구단) | `for dan in range(1, 10):` 안에 `for multiple in range(1, 10):` |
| [c12.py](C-파이썬%20기초/c12.py) | 반복문으로 합계·개수 누적 | `total = total + number` |
| [c16.py](C-파이썬%20기초/c16.py) | 함수 정의와 반환값 | `def f_to_c(f):` … `return (f - 32) * 5 / 9` |
| [c16exercise.py](C-파이썬%20기초/c16exercise.py) | 함수 실습 (수량 × 가격) | `def total(a, b): return a * b` |
| [chwk.py](C-파이썬%20기초/chwk.py) | 과제: 크리스마스 트리 | `" " * vacant`, `print(..., end="")` |
| [chwk(2).py](<C-파이썬 기초/chwk(2).py>) | 과제: 트리 여러 개 나란히 | 중첩 `for`로 같은 층을 나무 개수만큼 반복 |

### 주요 명령어 예시

**문자열 다루기 (c05, c07)**

```python
sensor = "S01"
len(sensor)          # 3        글자 수
sensor[0]            # "S"      첫 글자 (번호는 0부터)
sensor[0:2]          # "S0"     0번부터 2번 앞까지
"  START  ".strip().lower()   # "start"   양끝 공백 제거 후 소문자로
```

**조건문 (c09_starter)**: 위에서부터 차례로 검사해서, 처음 참이 된 블록 하나만 실행합니다.

```python
if score < 0 or score > 100:
    print("점수 범위 오류")
elif score >= 90:
    print("A")
else:
    print("F")
```

**반복문과 누적 (c12)**: 합계 변수는 반복 밖에서 0으로 만들어 두고, 반복 안에서 더합니다.

```python
total = 0
for number in [4, 5, 7]:
    total = total + number   # 4 → 9 → 16
```

**함수 (c16)**: `def`로 계산 과정에 이름을 붙이고, `return`으로 결과를 돌려줍니다. `return`이 없으면 함수는 `None`을 돌려줍니다.

```python
def f_to_c(f):
    """화씨 숫자를 받아 섭씨 숫자를 돌려줍니다."""
    return (f - 32) * 5 / 9

print(f"{f_to_c(72):.1f}")   # 22.2   (:.1f는 소수점 첫째 자리까지)
```

---

## D-파이썬 심화

함수를 더 깊이 다루고, CSV 파일을 읽고 쓰는 방법을 실습한 폴더입니다.

### [d01.py](D-파이썬%20심화/d01.py): 함수의 반환값

주문 금액에 따라 배송비를 정하는 함수를 만들고, 그 반환값을 다른 함수의 계산에 다시 사용합니다.

- **매개변수**: 함수를 정의할 때 값을 받는 이름 (`amount`)
- **인수**: 함수를 호출할 때 실제로 넘기는 값 (`25000`)
- `return 0`은 숫자 0을 돌려주는 것으로, 아무것도 돌려주지 않는 `None`과 다릅니다.
- `return`을 만나면 함수가 그 자리에서 끝나므로, 아래 줄은 위에서 반환하지 않았을 때만 실행됩니다.

```python
def delivery_fee(amount):
    if amount >= 30000:
        return 0
    return 3000

def payment(amount):
    return amount + delivery_fee(amount)   # 반환값을 다른 계산에 사용

# 주문 25000 / 배송 3000 / 결제 28000
# 주문 30000 / 배송 0 / 결제 30000
```

### [d02.py](D-파이썬%20심화/d02.py): 기본값과 이름 지정 인수

하나의 계산 함수를 여러 주문에 다시 사용합니다.

- **기본값**: `delivery=0`처럼 써 두면, 호출할 때 생략해도 0이 들어갑니다.
- **이름 지정 인수**: `price=1500`처럼 이름을 붙이면 순서를 바꿔 넘겨도 됩니다.

```python
def calculate_total(price, quantity, delivery=0, discount=0):
    return price * quantity + delivery - discount

calculate_total(2000, 3)                                  # 6000 (배송비 생략)
calculate_total(2000, 3, delivery=1000)                   # 7000
calculate_total(quantity=2, price=1500, delivery=500)     # 3500 (순서를 바꿔도 됨)
```

### [d06.py](D-파이썬%20심화/d06.py): CSV 파일 읽기

센서 기록 CSV 파일을 읽어 센서별 온도를 출력합니다.

| 명령어 | 설명 |
|---|---|
| `Path(__file__).resolve().parent` | 지금 실행 중인 .py 파일이 들어 있는 폴더의 전체 경로. 어느 폴더에서 실행해도 같은 파일을 찾을 수 있음 |
| `base / "data" / "readings.csv"` | `Path`에서 `/`는 경로를 이어 붙이는 연산자 |
| `with ... open(...) as file:` | 블록이 끝나면 파일을 자동으로 닫음 |
| `encoding="utf-8-sig"`, `newline=""` | 한글이 깨지지 않게 하고, 줄바꿈 처리를 csv 모듈에 맡김 |
| `csv.DictReader(file)` | 첫 줄의 열 이름을 키로 해서 한 줄씩 딕셔너리로 읽음 |
| `None if raw == "" else float(raw)` | 빈칸이면 `None`, 아니면 실수로 변환 (CSV에서 읽은 값은 처음에 모두 문자열) |

```python
with input_path.open(encoding="utf-8-sig", newline="") as file:
    rows = list(csv.DictReader(file))

for row in rows:
    raw = row["temperature_c"]
    temperature = None if raw == "" else float(raw)
    print(f"{row['sensor_id']}: {temperature}")
```

> 실행하려면 같은 폴더에 `data/readings.csv` 파일이 있어야 합니다. 실습용 데이터 파일은 이 저장소에 포함되어 있지 않습니다.

### [d07.py](D-파이썬%20심화/d07.py): CSV 파일 쓰기

주문 목록을 CSV 파일로 저장한 뒤, 다시 읽어서 값이 제대로 남았는지 확인합니다.

| 명령어 | 설명 |
|---|---|
| `output_dir.mkdir(exist_ok=True)` | `work` 폴더를 만들고, 이미 있으면 그대로 사용 |
| `open("w", ...)` | 쓰기 모드. 같은 이름의 파일이 있으면 덮어씀 |
| `csv.DictWriter(file, fieldnames=[...])` | 딕셔너리를 CSV 한 줄로 바꿔 씀 |
| `writer.writeheader()` / `writer.writerows(rows)` | 열 이름 한 줄을 쓰고, 이어서 모든 행을 씀 |

```python
with output_path.open("w", encoding="utf-8-sig", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=["id", "item", "quantity", "note"])
    writer.writeheader()
    writer.writerows(rows)
```

값 안에 쉼표(`"볼트, 소형"`)나 큰따옴표(`'담당자 "김"'`)가 있어도 csv 모듈이 알아서 처리합니다. `None`은 빈칸으로, `0`은 `"0"`으로 저장됩니다. 실행하면 `D-파이썬 심화/work/D07_orders.csv` 파일이 생깁니다.

---

## battle game · 권 · 족 · 참

팔 공격(拳)·발 공격(足)·검 공격(斬)과 방향키 콤보로 겨루는 2D 격투게임입니다. 직접 구상하고 Python과 [pygame-ce](https://pyga.me/)로 만들었습니다.

**🎮 웹에서 바로 플레이: https://battle-game-triple-command.vercel.app**

PC 브라우저나 휴대폰(가로 화면)으로 열면 설치 없이 바로 플레이할 수 있습니다.

### 게임 내용

- **모드**: 한 키보드(또는 한 터치스크린)로 두 사람이 겨루는 PVP, 컴퓨터와 겨루는 PVE(쉬움·보통·어려움)
- **캐릭터 4명**: 검술의 무진·설아, 격투술의 강혁·하린. 체력·속도·공격력이 서로 다름
- **기술**: 캐릭터마다 3연타 콤보 2개, ↓↘→ 같은 방향키 필살기 5개, 필살 게이지가 가득 찼을 때 쓰는 초필살기 1개
- **스테이지 5개**: 황야·초원·뒷골목·격투기 링·흰 방
- **규칙**: 3판 2선승, 한 라운드 99초

### 제작 과정

1. **기획**: "다양한 커맨드를 사용할 수 있는 격투게임"을 목표로 정했습니다. 버튼 하나로 끝나는 공격이 아니라, 연속 입력 콤보와 ↓↘→ 같은 방향키 커맨드로 기술을 골라 쓰는 게임입니다.
2. **캐릭터·기술·스테이지 설계**: 무기를 쓰는 **검술**과 맨손으로 싸우는 **격투술** 두 가지 유형을 정하고, 유형마다 남녀 한 명씩 총 4명의 캐릭터를 만들었습니다. 같은 유형끼리는 같은 커맨드를 쓰고, 체력·속도·공격력과 의상으로 개성을 나눴습니다. 맞은 부위에 따라 拳·足·斬 붓글씨 이펙트가 나오도록 했습니다.
3. **테스트 플레이 후 수정**
   - 캐릭터가 화면에 너무 작게 나와서, 게임 화면을 2배로 확대해 보여주고 두 캐릭터를 따라가는 카메라를 만들었습니다.
   - 그래픽이 깨져 보이는 문제를 고쳤습니다.
   - 메뉴·화면 구성 같은 인터페이스와 자잘한 편의 기능을 다듬었습니다.
4. **웹 배포**: 설치 없이 플레이할 수 있도록 브라우저에서 돌아가는 웹 버전을 만들어 배포했습니다.
5. **모바일 지원**: 휴대폰에는 키보드가 없어 웹 버전을 조작할 수 없다는 것을 확인하고, 화면 속 가상 조이스틱과 공격 버튼, 터치로 고르는 메뉴를 만들어 휴대폰·태블릿에서도 플레이할 수 있게 했습니다.

### 파일 구성

게임은 역할별로 파일을 나눠 만들었습니다. 파일별 자세한 설명과 기술표는 [battle game/README.md](battle%20game/README.md)에 있습니다.

| 분류 | 파일 |
|---|---|
| 실행 | `batgame.py` (게임 실행 파일), `settings.py` (게임 전체 수치) |
| 입력 | `controls.py` (키보드·키 설정), `touch.py` (휴대폰 터치 조작) |
| 게임 로직 | `fighter.py` (캐릭터 움직임·피격), `moves.py` (기술 데이터), `characters.py` (캐릭터 4명), `skeleton.py` (관절·판정 상자), `ai.py` (컴퓨터 상대) |
| 그리기 | `costume.py` (캐릭터 그림), `stages.py` (배경), `effects.py` (타격 연출), `hud.py` (체력바·타이머), `camera.py`, `ui.py` |
| 화면 흐름 | `scenes.py` (타이틀 → 모드·캐릭터·스테이지 선택 → 전투 → 결과) |
| 웹 배포 | `build_web.py` (브라우저용 버전 만들기) |
| 이미지 | `fist_effect.png`·`foot_effect.png`·`slash_effect.png` (타격 이펙트), `*_side.png` (캐릭터 원화 4장) |

### 실행

```bash
pip install pygame-ce
cd "battle game"
python batgame.py
```

---

## mini project · 바닷속 탈출

깊은 바닷속에서 눈을 뜬 주인공이 발판을 밟고 올라가 수면 위 출구로 탈출하는 게임입니다. 캐릭터를 방향키로 움직이고 점프해서 높은 곳으로 올라갑니다.

**🎮 웹에서 바로 플레이: https://claude.ai/artifact/PLTQaUA6T2p1dpP4ZBr2FA**

### 게임 내용

- **난이도**: 이지(30층)·노말(50층)·하드(70층)와 끝이 없는 무한 모드
- **목숨 3개**: 화면 아래로 떨어지면 목숨을 1개 잃고, 가장 높이 올라갔던 발판에서 부활
- **특수 발판**: 좌우로 움직이는 발판, 미끄러운 발판, 걷는 속도가 느려지는 발판
- **돌발 상황**: 8~10층을 오를 때마다 "모래알이 덮쳐왔다!"며 화면 색이 반전되고, 3층을 더 오르면 원래대로 돌아옴

### 제작 과정

1. **기획**: 만들 프로그램을 한 문장으로 쓰고("탈출 스토리를 가진 게임"), 핵심 기능 3개(이동·점프, 발판 등반과 목숨, 층수·목숨 표시)와 돌발 상황(화면 색 반전)을 정했습니다. 화면 구성은 [ex image.png](<mini project/ex image.png>)에 직접 그려 스케치했습니다.
2. **첫 구현**: 파이썬 기본 GUI 라이브러리 tkinter로 만들었습니다. 이때 도착점(EXIT 문), 게임 오버와 재시작, "화면 아래로 떨어지면 추락" 같은 빠진 규칙을 정했습니다.
3. **기능 확장**: 난이도와 무한 모드, 스케치의 파란 낙서를 살린 바닷속 배경(물결선과 물방울), 미끄러운·느려지는 발판을 추가했습니다.
4. **테스트 플레이 후 수정**: 직접 해 보고 번쩍임 횟수 줄이기, 발판 옆 숫자 삭제, 글자 진하게 하기, 발판 간격 늘리기, 하드 목표를 100층에서 70층으로 낮추기를 했습니다. 간격을 늘릴 때는 모든 발판이 점프로 닿는지 시뮬레이션으로 확인했습니다.
5. **웹 배포**: tkinter는 브라우저에서 실행되지 않으므로, 같은 규칙을 JavaScript로 옮긴 웹 버전을 만들어 배포했습니다.

자세한 제작 과정과 `game.py` 코드 설명은 [mini project/README.md](mini%20project/README.md)에 있습니다.

### 파일 구성

| 파일 | 설명 |
|---|---|
| [game.py](mini%20project/game.py) | 게임 본체 (파이썬, tkinter). 추가 설치 없이 `python game.py`로 실행 |
| [web/index.html](mini%20project/web/index.html) | 브라우저용 웹 버전 |
| [ex image.png](<mini project/ex image.png>) | 게임 제작에 사용한 예시 이미지 (기획 단계의 화면 스케치) |
