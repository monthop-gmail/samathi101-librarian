import os
import shutil
import json
from google import genai
import pymupdf4llm

# 1. Setup Gemini
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY environment variable is not set.")
    client = None
else:
    client = genai.Client(api_key=GEMINI_API_KEY)

INBOX_DIR = "00_INBOX_UNPROCESSED"
MASTER_DIR = "01_Curriculum_Master_Data"
SURVEY_DIR = "02_Survey_Data"

# 2. Define standard courses context
COURSES_CONTEXT = """
หลักสูตรหลักของสถาบันพลังจิตตานุภาพ:
- WP-01: หลักสูตรครูสมาธิ (Willpower Course) - เล่ม 1, 2, 3
- WP-02: หลักสูตรวิทันตสาสมาธิ (Vitantasa Meditation)
- WP-03: หลักสูตรอัตตาสาสมาธิ (Attasa Meditation)
- WP-04: หลักสูตรชินนสาสมาธิ (Chinnasa Meditation)
- WP-05: หลักสูตรนิรสาสมาธิ (Nirasa Meditation)
- WP-10: หลักสูตรอาจาริยสาสมาธิ (Ajariyasa Meditation)
- WP-11: หลักสูตรญาณสาสมาธิ (Yanasa Meditation)
- WP-12: หลักสูตรอุตตมสาสมาธิ (Uttamasa Meditation)
- WP-99: การสอบภาคสนามธุดงค์ (Thudong Field Exam)
- WP-EX: หลักสูตรสมาธิออนไลน์ (Willpower Online)
- WP-CHILD: หลักสูตรสมาธิเด็กและเยาวชน
"""

def convert_pdf_to_md(target_path: str) -> None:
    """Converts a PDF file to a Markdown file in the same directory."""
    try:
        md_text = pymupdf4llm.to_markdown(target_path)
        md_path = os.path.splitext(target_path)[0] + ".md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_text)
        print(f"Converted {target_path} to markdown.")
    except Exception as e:
        print(f"Error converting {target_path} to markdown: {e}")

def process_file(file_path: str) -> None:
    """Processes a single file: Classifies, moves, generates metadata, and converts if PDF."""
    if not os.path.isfile(file_path) or os.path.basename(file_path).startswith('.'):
        return

    filename = os.path.basename(file_path)
    print(f"Processing: {filename}...")
    
    # Read snippet for better classification
    content_snippet = ""
    try:
        if file_path.lower().endswith(('.csv', '.txt', '.md')):
            with open(file_path, 'r', encoding='utf-8') as f:
                content_snippet = f.read(2000) # Increased to 2000
    except:
        pass

    prompt = f"""
    คุณคือบรรณารักษ์ดิจิทัลของสถาบันพลังจิตตานุภาพ
    ข้อมูลหลักสูตร: {COURSES_CONTEXT}
    
    ไฟล์ชื่อ: "{filename}"
    เนื้อหาบางส่วน: "{content_snippet}"
    
    งานของคุณ:
    1. ระบุรหัสหลักสูตร (ID) และชื่อหลักสูตร (อิงจากชื่อไฟล์และเนื้อหา)
    2. ระบุประเภท: 
       - "Manual" (คู่มือการเรียน/ตำรา) 
       - "Survey" (แบบประเมิน/ความพึงพอใจ/ข้อมูลดิบสำรวจ)
       - "Exam" (ข้อสอบ)
    3. ตั้งชื่อไฟล์ใหม่ให้เป็นมาตรฐาน: [ID]_[Type]_[Year].(ext)
    4. เลือกโฟลเดอร์ปลายทาง:
       - หากประเภทคือ Manual หรือ Exam ให้ใช้ "01_Curriculum_Master_Data"
       - หากประเภทคือ Survey ให้ใช้ "02_Survey_Data"
    
    ตอบกลับเป็น JSON เท่านั้น:
    {{
      "target_dir": "path/to/folder",
      "new_filename": "new_name.ext",
      "metadata": {{ 
          "course_id": "WP-XX", 
          "course_name": "...", 
          "doc_type": "Survey/Manual/Exam",
          "year": "...", 
          "missing_info": [] 
      }}
    }}
    """
    
    try:
        if client:
            # Using Gemini 2.0 Flash with JSON mode for robustness
            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt,
                config={
                    'response_mime_type': 'application/json',
                }
            )
            raw_json = response.text.strip()
            if not raw_json:
                raise ValueError("Empty response from Gemini")
            result = json.loads(raw_json)
        else:
            result = {
                "target_dir": MASTER_DIR,
                "new_filename": f"TEMP_{filename}",
                "metadata": {"course_id": "UNKNOWN", "course_name": "Unknown", "doc_type": "Other", "year": "2026", "missing_info": ["API Key missing"]}
            }

        target_dir = result['target_dir'].lstrip('/')
        # Ensure it doesn't use the literal variable name
        if target_dir.startswith("MASTER_DIR"):
            target_dir = target_dir.replace("MASTER_DIR", MASTER_DIR, 1)
        elif target_dir.startswith("SURVEY_DIR"):
            target_dir = target_dir.replace("SURVEY_DIR", SURVEY_DIR, 1)
            
        new_filename = result['new_filename']
        target_path = os.path.join(target_dir, new_filename)
        
        os.makedirs(target_dir, exist_ok=True)
        shutil.move(file_path, target_path)
        print(f"Moved to: {target_path}")
        
        meta_path = target_path + ".json"
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(result['metadata'], f, ensure_ascii=False, indent=2)

        if target_path.lower().endswith(".pdf") and "Manual" in result['metadata']['doc_type']:
            convert_pdf_to_md(target_path)
            
    except Exception as e:
        print(f"Error processing {filename}: {e}")

def main():
    if not os.path.exists(INBOX_DIR):
        print(f"Inbox directory {INBOX_DIR} not found.")
        return
        
    for f in os.listdir(INBOX_DIR):
        process_file(os.path.join(INBOX_DIR, f))

if __name__ == "__main__":
    main()
