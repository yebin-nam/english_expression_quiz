"""
'Learning English Raw' 폴더의 이미지(이미 "Learning English N.jpg" 형식으로
이름이 바뀐 것들) 중, '..\\Learning English' 폴더에 아직 대응하는 md 파일이
없는 것을 찾아서, 이미지 왼쪽(영어)/오른쪽(한글) 컬럼을 각각 OCR로 읽어
아래 형식의 표를 가진 md 파일을 새로 만듭니다. Example 칸은 항상 비워둡니다
(공부하면서 직접 채우는 용도).

    | Expression | Mean | Example |
    | --- | --- | --- |
    | ... | ... | |

이미 md 파일이 존재하는 이미지는 건드리지 않습니다.
OCR은 완벽하지 않으니, 생성된 md 파일은 한 번 훑어보고 오탈자를 고쳐주세요.

사용법:
    python generate_tables.py             실제로 md 파일 생성
    python generate_tables.py --dry-run   무엇을 만들지만 미리 확인 (파일 생성 없음)
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from itertools import zip_longest

import pytesseract
from PIL import Image

SCRIPT_DIR = Path(__file__).resolve().parent
RAW_DIR = SCRIPT_DIR.parent
MD_DIR = RAW_DIR.parent / "Learning English"
TESSDATA_DIR = Path(r"C:\Program Files\Tesseract-OCR\tessdata")

TESSERACT_EXE = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if Path(TESSERACT_EXE).exists():
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_EXE
os.environ["TESSDATA_PREFIX"] = str(TESSDATA_DIR)

IMAGE_EXTS = {".jpg", ".jpeg", ".png"}
NAMED_RE = re.compile(r"^Learning English \d+( [A-Za-z])?$", re.IGNORECASE)
TITLE_RE = re.compile(r"learn|engl|aelee", re.IGNORECASE)
HANGUL_RE = re.compile(r"[\uac00-\ud7a3]")
JUNK_PREFIX_RE = re.compile(r"^[^\w가-힣]+")


def ocr_column(image: Image.Image, lang: str) -> list[str]:
    text = pytesseract.image_to_string(image, lang=lang, config="--psm 6")
    return [line.strip() for line in text.splitlines() if line.strip()]


def extract_expressions(path: Path) -> tuple[list[str], list[str]] | None:
    im = Image.open(path)
    w, h = im.size

    left = im.crop((0, 0, int(w * 0.53), h))
    right = im.crop((int(w * 0.47), 0, w, h))
    right = right.resize((right.width * 2, right.height * 2), Image.LANCZOS)

    eng_lines = ocr_column(left, "eng")
    kor_lines = ocr_column(right, "kor")

    # 제목 줄(첫 줄), 서명 줄("...@...)") 제거
    if eng_lines and TITLE_RE.search(eng_lines[0]):
        eng_lines = eng_lines[1:]
    eng_lines = [l for l in eng_lines if "@" not in l]
    # 한글이 하나도 없는 줄(제목 오인식 등)은 제거, 앞에 붙은 잡음 문자는 정리
    kor_lines = [JUNK_PREFIX_RE.sub("", l) for l in kor_lines if HANGUL_RE.search(l)]

    return eng_lines, kor_lines


def build_table(expressions: list[str], meanings: list[str]) -> str:
    rows = ["| Expression | Mean | Example |", "| --- | --- | --- |"]

    for expr, mean in zip_longest(expressions, meanings, fillvalue=""):
        rows.append(f"| {expr} | {mean} | |")

    return "\n".join(rows) + "\n"


def main() -> None:
    dry_run = "--dry-run" in sys.argv

    images = [
        p
        for p in RAW_DIR.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS and NAMED_RE.match(p.stem)
    ]

    pending = [p for p in images if not (MD_DIR / f"{p.stem}.md").exists()]

    if not pending:
        print("새로 표를 만들 이미지가 없습니다.")
        return

    for path in sorted(pending):
        print(f"\n[처리] {path.name}")

        eng_lines, kor_lines = extract_expressions(path)

        if len(eng_lines) != len(kor_lines):
            print(
                f"  ⚠ OCR 줄 수 불일치: 영어 {len(eng_lines)}줄 / 한글 {len(kor_lines)}줄"
                " — md는 생성합니다. 수동 확인해주세요."
            )

        table = build_table(eng_lines, kor_lines)
        md_path = MD_DIR / f"{path.stem}.md"

        print(f"  -> {md_path.name} ({len(eng_lines)}개 표현)")
        if not dry_run:
            md_path.write_text(table, encoding="utf-8")

    if dry_run:
        print("\n(dry-run 모드: 실제로 파일은 생성되지 않았습니다)")
    else:
        print("\n생성된 md 파일은 OCR 오탈자가 있을 수 있으니 한 번 훑어봐주세요.")
if __name__ == "__main__":
    main()
