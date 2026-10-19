import os
import glob
import json
import re
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# 📍 옵시디언 영어공부 폴더 경로
WATCH_DIR = r"C:\Users\skadp\OneDrive\문서\Obsidian Vault\영어공부\Learning English"
OUTPUT_JSON = "./learning_data.json"

def parse_markdown_files():
    """markdown_files 폴더 안의 모든 .md 파일을 읽어서 JSON으로 변환합니다."""
    all_data = []
    item_id = 1
    
    md_files = sorted(glob.glob(os.path.join(WATCH_DIR, "*.md")))
    print(f"\n🔄 총 {len(md_files)}개의 마크다운 파일을 파싱합니다...")

    for file_path in md_files:
        unit_name = os.path.basename(file_path).replace(".md", "").replace("_", " ")
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception as e:
            print(f"⚠️ 파일 읽기 실패 ({file_path}): {e}")
            continue
            
        for line in lines:
            line = line.strip()
            if line.startswith("|") and not "Expression" in line and not "---" in line:
                parts = [p.strip() for p in line.split("|")[1:-1]]
                if len(parts) >= 2:
                    expr = parts[0]
                    mean = parts[1]
                    ex = parts[2] if len(parts) >= 3 else ""
                    
                    expr_clean = re.sub(r"==|\*\*|<br>|~~", "", expr).strip()
                    mean_clean = re.sub(r"==|\*\*|<br>|~~", "", mean).strip()
                    ex_clean = re.sub(r"==|\*\*|<br>|~~", " ", ex).strip()
                    
                    if expr_clean:
                        has_ex = bool(ex_clean)
                        all_data.append({
                            "id": item_id,
                            "unit": unit_name,
                            "expression": expr_clean,
                            "meaning": mean_clean,
                            "example": ex_clean if has_ex else None,
                            "has_example": has_ex
                        })
                        item_id += 1

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
        
    print(f"✅ 파싱 완료! 총 {len(all_data)}개의 표현이 '{OUTPUT_JSON}'에 자동 저장되었습니다.")

class MDFileHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.src_path.endswith(".md"):
            print(f"✨ 새로운 수업 자료 감지: {event.src_path}")
            parse_markdown_files()

    def on_modified(self, event):
        if event.src_path.endswith(".md"):
            print(f"📝 수업 자료 수정 감지: {event.src_path}")
            parse_markdown_files()

if __name__ == "__main__":
    if not os.path.exists(WATCH_DIR):
        print(f"⚠️ 지정된 경로를 찾을 수 없습니다: {WATCH_DIR}")
        print("옵시디언 폴더 경로가 맞는지 확인해주세요.")
    else:
        parse_markdown_files()
        event_handler = MDFileHandler()
        observer = Observer()
        observer.schedule(event_handler, WATCH_DIR, recursive=False)
        observer.start()

        print(f"🚀 '{WATCH_DIR}' 폴더 감시 중... (옵시디언에서 노트를 수정하거나 추가하면 자동 반영됩니다)")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
