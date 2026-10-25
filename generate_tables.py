"""
'Learning English Raw' 폴더의 이미지(이미 "Learning English N.jpg" 형식으로
이름이 바뀐 것들) 중, '..\\Learning English' 폴더에 아직 대응하는 md 파일이
없는 것을 찾아서, 이미지 왼쪽(영어)/오른쪽(한글) 컬럼을 각각 OCR로 읽어
아래 형식의 표를 가진 md 파일을 새로 만듭니다. Example 칸은 항상 비워둡니다
(공부하면서 직접 채우는 용도).

    | Expression | Mean | Example |
    | --- | --- | --- |
    | ... | ... | |

기본 실행은 기존 md를 보존합니다. --force는 기존 파일을 .md.bak로 백업한 뒤 재생성합니다.
주의: --force로 재생성한 표의 Example은 비워집니다. 직접 쓴 내용은 백업에서 옮겨주세요.
첨부 양식 기준 상단 13%, 하단 10%는 제목/서명으로 제외합니다.
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

import pytesseract
from PIL import Image


def normalize_expression(text: str) -> str:
    """Normalize typography and unambiguous OCR pronoun forms, not every l."""
    text = text.translate(str.maketrans({c: "'" for c in "‘’ʼ＇`´"}))
    text = re.sub(r"(?<![A-Za-z])[liI](?='(?:m|d|ll|ve)\b)", "I", text)
    text = re.sub(r"(?<![A-Za-z])[li](?=\s|[.!?,;:]|$)", "I", text)
    return re.sub(r"\s+", " ", text).strip()


SCRIPT_DIR = Path(__file__).resolve().parent
RAW_DIR = SCRIPT_DIR.parent
MD_DIR = RAW_DIR.parent / "Learning English"
TESSDATA_DIR = Path(r"C:\Program Files\Tesseract-OCR\tessdata")

TESSERACT_EXE = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if Path(TESSERACT_EXE).exists():
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_EXE
if TESSDATA_DIR.exists():
    os.environ["TESSDATA_PREFIX"] = str(TESSDATA_DIR)

IMAGE_EXTS = {".jpg", ".jpeg", ".png"}
NAMED_RE = re.compile(r"^Learning English \d+( [A-Za-z])?$", re.IGNORECASE)
TITLE_RE = re.compile(r"learn|engl|aelee", re.IGNORECASE)
HANGUL_RE = re.compile(r"[\uac00-\ud7a3]")
JUNK_PREFIX_RE = re.compile(r"^[^\w가-힣]+")


def ocr_column(image: Image.Image, lang: str) -> list[dict]:
    """Keep line positions so a missing OCR line cannot shift all later pairs."""
    data = pytesseract.image_to_data(image, lang=lang, config="--psm 6",
                                     output_type=pytesseract.Output.DICT)
    groups = {}
    for i, word in enumerate(data["text"]):
        if not word.strip():
            continue
        key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
        row = groups.setdefault(key, {"words": [], "top": data["top"][i], "bottom": 0})
        row["words"].append(word.strip())
        row["top"] = min(row["top"], data["top"][i])
        row["bottom"] = max(row["bottom"], data["top"][i] + data["height"][i])
    return sorted([{"text": " ".join(r["words"]), "y": (r["top"] + r["bottom"]) / 2,
                    "height": r["bottom"] - r["top"]} for r in groups.values()],
                  key=lambda r: r["y"])


def pair_rows(left: list[dict], right: list[dict]) -> tuple[list[str], list[str]]:
    expressions, meanings = [], []
    used = set()
    for row in left:
        expr = normalize_expression(row["text"])
        if re.search(r"learning\s+english|aelee|aelly877|@", expr, re.I):
            continue
        candidates = [(abs(row["y"] - other["y"]), j, other)
                      for j, other in enumerate(right) if j not in used
                      and abs(row["y"] - other["y"]) <=
                      max(row["height"], other["height"]) * 0.75]
        if not candidates:
            print(f"  [확인] 대응하는 뜻이 없어 제외: {expr}")
            continue
        _, j, other = min(candidates, key=lambda c: c[0])
        used.add(j)
        meaning = other["text"].strip()
        if "@" in meaning:
            continue
        expressions.append(expr)
        meanings.append(meaning)
    for j, row in enumerate(right):
        if j not in used:
            print(f"  [확인] 대응하는 표현이 없어 제외: {row['text']}")
    return expressions, meanings


def extract_expressions(path: Path) -> tuple[list[str], list[str]]:
    with Image.open(path) as source:
        im = source.convert("RGB")
    w, h = im.size
    # This worksheet template: heading at top, signature below the lesson.
    # Equal vertical crops/scales keep left/right coordinates comparable.
    top, bottom = int(h * 0.13), int(h * 0.90)
    left = im.crop((0, top, int(w * 0.50), bottom))
    right = im.crop((int(w * 0.50), top, w, bottom))
    left = left.resize((left.width * 2, left.height * 2), Image.Resampling.LANCZOS)
    right = right.resize((right.width * 2, right.height * 2), Image.Resampling.LANCZOS)
    return pair_rows(ocr_column(left, "eng"), ocr_column(right, "kor+eng"))


def build_table(expressions: list[str], meanings: list[str]) -> str:
    rows = ["| Expression | Mean | Example |", "| --- | --- | --- |"]

    if len(expressions) != len(meanings):
        raise ValueError("표현과 뜻의 줄 수가 다릅니다. 위치 매칭 결과를 확인하세요.")
    for expr, mean in zip(expressions, meanings):
        expr = normalize_expression(expr).replace("|", "&#124;")
        mean = mean.replace("|", "&#124;")
        rows.append(f"| {expr} | {mean} | |")

    return "\n".join(rows) + "\n"


def main() -> None:
    dry_run = "--dry-run" in sys.argv

    images = [
        p
        for p in RAW_DIR.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS and NAMED_RE.match(p.stem)
    ]

    force = "--force" in sys.argv
    pending = [p for p in images if force or not (MD_DIR / f"{p.stem}.md").exists()]

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
            MD_DIR.mkdir(parents=True, exist_ok=True)
            if md_path.exists():
                # Preserve hand-written examples before explicitly regenerating.
                import shutil
                backup = md_path.with_suffix(".md.bak")
                index = 1
                while backup.exists():
                    backup = md_path.with_suffix(f".md.bak.{index}")
                    index += 1
                shutil.copy2(md_path, backup)
                print(f"  기존 노트 백업: {backup.name}")
            md_path.write_text(table, encoding="utf-8")

    if dry_run:
        print("\n(dry-run 모드: 실제로 파일은 생성되지 않았습니다)")
    else:
        print("\n생성된 md 파일은 OCR 오탈자가 있을 수 있으니 한 번 훑어봐주세요.")
if __name__ == "__main__":
    main()
