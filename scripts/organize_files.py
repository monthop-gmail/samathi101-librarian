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

# 2. Define standard courses context (Master Data for AI)
COURSES_CONTEXT = """
จำแนกไฟล์เข้าตามกลุ่มหลักสูตรของสถาบันพลังจิตตานุภาพ ดังนี้:

1. กลุ่มหลักสูตรพื้นฐาน (Foundation):
   - WP-01: หลักสูตรครูสมาธิ (หลักสูตรหลัก 6 เดือน)
   - WP-02: หลักสูตรวิทันตสาสมาธิ (สำหรับผู้บริหาร/บุคคลทั่วไป)
   - WP-03: หลักสูตรอัตตาสาสมาธิ (สมาธิเพื่อดูแลตนเอง)
   - WP-04: หลักสูตรชินนสาสมาธิ (สมาธิชนะใจตนเอง 1 วัน)
   - WP-05: หลักสูตรนิรสาสมาธิ (สมาธิเพื่อความดับทุกข์ 3 วัน 2 คืน)

2. กลุ่มหลักสูตรขั้นสูง (Advanced):
   - WP-10: หลักสูตรอาจาริยสาสมาธิ (การฝึกอบรมอาจารย์สอนสมาธิ)
   - WP-11: หลักสูตรญาณสาสมาธิ (ขั้นสูงสำหรับผู้จบครูสมาธิ)
   - WP-12: หลักสูตรอุตตมสาสมาธิ

3. กลุ่มหลักสูตรพิเศษและกิจกรรม:
   - WP-99: การสอบภาคสนามธุดงค์ (ดอยอินทนนท์ หรือพื้นที่อื่นๆ)
   - WP-EX: หลักสูตรสมาธิออนไลน์ (Willpower Online)
   - WP-CHILD: หลักสูตรสมาธิเด็กและเยาวชน
"""

COURSES_LIST = [
    {"id": "WP-01", "name": "ครูสมาธิ"},
    {"id": "WP-02", "name": "วิทันตสาสมาธิ"},
    {"id": "WP-03", "name": "อัตตาสาสมาธิ"},
    {"id": "WP-04", "name": "ชินนสาสมาธิ"},
    {"id": "WP-05", "name": "นิรสาสมาธิ"},
    {"id": "WP-10", "name": "อาจาริยสาสมาธิ"},
    {"id": "WP-11", "name": "ญาณสาสมาธิ"},
    {"id": "WP-12", "name": "อุตตมสาสมาธิ"},
    {"id": "WP-99", "name": "สอบภาคสนามธุดงค์"},
]

def update_dashboard():
    """Updates the inventory table in README.md based on processed files."""
    print("Updating Dashboard...")
    inventory_header = "## 🏆 Meditation Course Data Inventory\n\n"
    table_header = "| ID | หลักสูตร | คู่มือ (Manuals) | แบบสอบถาม (Surveys) | สถานะความพร้อม (RAG Ready) |\n"
    table_sep = "| :--- | :--- | :---: | :---: | :---: |\n"
    
    rows = []
    for course in COURSES_LIST:
        cid = course["id"]
        name = course["name"]
        
        # Count manuals in MASTER_DIR
        manual_count = 0
        if os.path.exists(MASTER_DIR):
            manual_count = len([f for f in os.listdir(MASTER_DIR) if f.startswith(cid) and f.endswith(('.pdf', '.md'))])
        
        # Count surveys in SURVEY_DIR
        survey_count = 0
        if os.path.exists(SURVEY_DIR):
            survey_count = len([f for f in os.listdir(SURVEY_DIR) if f.startswith(cid) and f.endswith('.csv')])
            
        status = "⚡ พร้อมใช้งาน" if manual_count > 0 and survey_count > 0 else "🟡 ข้อมูลไม่ครบ"
        if manual_count == 0 and survey_count == 0:
            status = "⏳ รอข้อมูล"
            
        rows.append(f"| {cid} | {name} | {manual_count} | {survey_count} | {status} |")
    
    new_inventory = inventory_header + table_header + table_sep + "\n".join(rows) + "\n"
    
    # Read existing README and replace the inventory section
    if os.path.exists("README.md"):
        with open("README.md", "r", encoding="utf-8") as f:
            content = f.read()
        
        if "## 🏆 Meditation Course Data Inventory" in content:
            # Replace existing section
            # Simple replacement: everything after the header up to the next horizontal rule or end of file
            parts = content.split("## 🏆 Meditation Course Data Inventory")
            # We assume the inventory is the last major section or we just append
            with open("README.md", "w", encoding="utf-8") as f:
                f.write(parts[0] + new_inventory)
        else:
            # Append to end
            with open("README.md", "a", encoding="utf-8") as f:
                f.write("\n\n---\n" + new_inventory)
        print("README.md updated.")

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
                content_snippet = f.read(2000)
    except:
        pass

    prompt = f"""
    คุณคือบรรณารักษ์ดิจิทัลของสถาบันพลังจิตตานุภาพ
    ข้อมูลหลักสูตร: {COURSES_CONTEXT}
    
    ไฟล์ชื่อ: "{filename}"
    เนื้อหาบางส่วน: "{content_snippet}"
    
    งานของคุณ:
    1. ระบุรหัสหลักสูตร (ID) และชื่อหลักสูตร
    2. ระบุประเภท: 
       - "Manual" (คู่มือการเรียน/ตำรา) 
       - "Survey" (แบบประเมิน/ความพึงพอใจ/ข้อมูลดิบสำรวจ)
       - "Exam" (ข้อสอบ)
    3. ตั้งชื่อไฟล์ใหม่ให้เป็นมาตรฐาน: [ID]_[Type]_[Year].(ext)
    4. เลือกโฟลเดอร์ปลายทาง:
       - หากประเภทคือ Manual หรือ Exam ให้ใช้ "01_Curriculum_Master_Data"
       - หากประเภทคือ Survey ให้ใช้ "02_Survey_Data"
    
    ตอบกลับเป็น JSON เท่านั้น โดยมีโครงสร้าง Metadata สำหรับ Gemini RAG ดังนี้:
    {{
      "target_dir": "path/to/folder",
      "new_filename": "new_name.ext",
      "metadata": {{ 
          "assigned_course": "[ID]: [Name]", 
          "category": "Curriculum_Manual / Survey_Data / Exam_Paper", 
          "level": "Foundation / Intermediate / Advanced",
          "year": "2568", 
          "status": "Processed",
          "missing_info": ["...", "..."] 
      }}
    }}
    """
    
    try:
        if client:
            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt,
                config={'response_mime_type': 'application/json'}
            )
            raw_json = response.text.strip()
            if not raw_json:
                raise ValueError("Empty response from Gemini")
            result = json.loads(raw_json)
        else:
            result = {
                "target_dir": MASTER_DIR,
                "new_filename": f"TEMP_{filename}",
                "metadata": {"assigned_course": "UNKNOWN", "category": "Other", "level": "N/A", "year": "2026", "status": "Error", "missing_info": ["API Key missing"]}
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

        if target_path.lower().endswith(".pdf") and "Manual" in result['metadata']['category']:
            convert_pdf_to_md(target_path)
            
    except Exception as e:
        print(f"Error processing {filename}: {e}")

def main():
    if not os.path.exists(INBOX_DIR):
        print(f"Inbox directory {INBOX_DIR} not found.")
        return
        
    for f in os.listdir(INBOX_DIR):
        process_file(os.path.join(INBOX_DIR, f))
    
    update_dashboard()

if __name__ == "__main__":
    main()
