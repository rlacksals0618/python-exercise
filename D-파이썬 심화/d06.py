import csv
from pathlib import Path
# __file__은 지금 실행하는 .py의 위치입니다. 터미널의 현재 폴더와 다릅니다.

base = Path(__file__).resolve().parent # base에는 이 파일이 들어 있는 폴더의 전체 경로가 저장됨
input_path = base / "data" / "readings.csv"  # /는 경로를 이어 붙입니다.

with input_path.open(encoding="utf-8-sig", newline="") as file: # with를 벗어나면 파일을 닫습니다. newline=""은 CSV 줄바꿈 처리에 사용합니다.
    rows = list(csv.DictReader(file))  # 첫 줄의 열 이름이 딕셔너리의 키가 됩니다.
print(f"기록 수: {len(rows)}")

for row in rows:
    raw = row["temperature_c"]
    # CSV에서 읽은 수량·온도도 처음에는 문자열입니다.
    temperature = None if raw == "" else float(raw)
    # 위 표현은 '조건이면 앞 값, 아니면 뒤 값'인 짧은 조건 표현입니다.
    print(f"{row['sensor_id']}: {temperature}")
print(f"첫 번호 종류: {type(rows[0]['sensor_id']).__name__}")
# 원본 data 파일에는 쓰지 않습니다. .open에 w를 넣지 마세요.
# 다른 폴더에서 실행해도 __file__ 기준 data 경로는 같습니다.
# 직접 작성: 미측정 개수를 계산해 마지막에 출력하세요.