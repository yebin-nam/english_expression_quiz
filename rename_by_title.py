"""
'Learning English Raw' 폴더의 이미지 중, 아직 제목으로 이름이 바뀌지 않은 파일
(예: IMG_1234.JPG, IMG_1234_Original.jpg 등)을 찾아서, 이미지 안에 적힌
"Aelee's Learning English N" 또는 "... N A" 제목을 OCR로 읽어
"Learning English N.jpg" / "Learning English N A.jpg" 형식으로 이름을 바꿉니다.

이미 "Learning English N.jpg" 형식인 파일은 건드리지 않습니다.

사용법:
    python rename_by_title.py            실제로 이름 변경
    python rename_by_title.py --dry-run   무엇을 바꿀지만 미리 확인 (파일 변경 없음)
"""
from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

import pytesseract
from PIL import Image

TESSERACT_EXE = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if Path(TESSERACT_EXE).exists():
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_EXE

RAW_DIR = Path(__file__).resolve().parent.parent
IMAGE_EXTS = {".jpg", ".jpeg", ".png"}

# 이미 올바른 이름인 파일 패턴: "Learning English 12.jpg", "Learning English 10 A.jpg"
ALREADY_NAMED_RE = re.compile(r"^Learning English \d+( [A-Za-z])?$", re.IGNORECASE)

# OCR 텍스트에서 "Learning English 13" / "Learning English 20A" 추출
TITLE_RE = re.compile(
    r"Learning[ \t]+English[ \t]+(\d+)(?:[ \t]*([A-Za-z]))?(?!\w)", re.IGNORECASE
)


def md5(path: Path) -> str:
    h = hashlib.md5()
    h.update(path.read_bytes())
    return h.hexdigest()


def target_name(text: str) -> str | None:
    m = TITLE_RE.search(text)
    if not m:
        return None
    number, letter = m.group(1), m.group(2)
    if letter:
        return f"Learning English {number} {letter.upper()}"
    return f"Learning English {number}"


def main() -> None:
    dry_run = "--dry-run" in sys.argv

    candidates = [
        p
        for p in RAW_DIR.iterdir()
        if p.is_file()
        and p.suffix.lower() in IMAGE_EXTS
        and not ALREADY_NAMED_RE.match(p.stem)
    ]

    if not candidates:
        print("새로 이름 붙일 이미지가 없습니다.")
        return

    for path in sorted(candidates):
        print(f"\n[검사] {path.name}")
        try:
            text = pytesseract.image_to_string(Image.open(path), lang="eng")
        except Exception as e:
            print(f"  OCR 실패: {e}")
            continue

        name = target_name(text)
        if not name:
            print("  제목을 찾지 못했습니다. 수동으로 확인해주세요.")
            continue

        new_path = path.with_name(name + ".jpg")

        if new_path.resolve() == path.resolve():
            continue

        if new_path.exists():
            if md5(path) == md5(new_path):
                print(f"  '{new_path.name}' 과 완전히 동일한 중복 파일입니다. 그대로 둡니다 (직접 삭제해주세요).")
            else:
                print(f"  '{new_path.name}' 이미 존재하지만 내용이 다릅니다. 충돌 - 건너뜁니다.")
            continue

        print(f"  -> {new_path.name}")
        if not dry_run:
            path.rename(new_path)

    if dry_run:
        print("\n(dry-run 모드: 실제로 파일명은 바뀌지 않았습니다)")


if __name__ == "__main__":
    main()
