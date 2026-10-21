"""웹 버전 만들기: pygbag으로 브라우저에서 돌아가는 파일을 web/ 폴더에 만든다.

실행: python build_web.py        (pip install pygbag fonttools 필요)
확인: python -m http.server -d web 8000  →  http://localhost:8000

게임에 필요한 파일만 임시 폴더에 모은 뒤 빌드한다.
글꼴은 게임에 나오는 글자만 남겨서(서브셋) 첫 로딩을 가볍게 한다.
"""
import shutil
import string
import subprocess
import sys
import tempfile
from pathlib import Path

import pygame
from fontTools import subset

HERE = Path(__file__).resolve().parent
OUT = HERE / "web"
APP_NAME = "battle_game"
TITLE = "권 · 족 · 참"
SKIP = {"build_web.py"}

# pygbag은 main.py 맨 위의 import만 보고 내려받을 패키지를 정하므로 pygame을 여기서 직접 불러야 한다
MAIN_PY = '''import asyncio
import pygame  # noqa: F401
from batgame import main

asyncio.run(main())
'''


def used_characters(sources):
    """소스에 나오는 모든 글자 + 영문·숫자·기호 + 화살표."""
    chars = set(string.printable) | set("↑↓←→↖↗↘↙·×✓◀▶")
    for path in sources:
        chars |= set(path.read_text(encoding="utf-8"))
    return "".join(sorted(c for c in chars if c.isprintable()))


def subset_font(src, dst, text):
    options = subset.Options()
    options.layout_features = ["*"]
    font = subset.load_font(str(src), options)
    sub = subset.Subsetter(options)
    sub.populate(text=text)
    sub.subset(font)
    subset.save_font(font, str(dst), options)


def main():
    stage = Path(tempfile.gettempdir()) / "kwon_jok_cham_web" / APP_NAME
    if stage.parent.exists():
        shutil.rmtree(stage.parent)
    (stage / "assets" / "fonts").mkdir(parents=True)

    sources = [p for p in HERE.glob("*.py") if p.name not in SKIP]
    for p in sources:
        shutil.copy2(p, stage / p.name)
    (stage / "main.py").write_text(MAIN_PY, encoding="utf-8")
    for name in ("fist_effect.png", "foot_effect.png", "slash_effect.png"):
        shutil.copy2(HERE / name, stage / name)

    text = used_characters(sources)
    for font in (HERE / "assets" / "fonts").glob("*.ttf"):
        dst = stage / "assets" / "fonts" / font.name
        subset_font(font, dst, text)
        print(f"글꼴 {font.name}: {font.stat().st_size // 1024} KB → {dst.stat().st_size // 1024} KB")
    for lic in (HERE / "assets" / "fonts").glob("OFL-*.txt"):   # 글꼴 라이선스도 함께 배포
        shutil.copy2(lic, stage / "assets" / "fonts" / lic.name)

    # 브라우저 탭 아이콘
    icon = pygame.image.load(str(HERE / "fist_effect.png"))
    pygame.image.save(pygame.transform.smoothscale(icon, (64, 64)), str(stage / "favicon.png"))

    subprocess.run([sys.executable, "-m", "pygbag", "--build", "--ume_block", "0", "--title", TITLE,
                    "--app_name", APP_NAME, "--icon", str(stage / "favicon.png"), str(stage)],
                   check=True)

    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(stage / "build" / "web", OUT)
    print(f"\n완료: {OUT}")
    for f in sorted(OUT.iterdir()):
        print(f"  {f.name}  {f.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
