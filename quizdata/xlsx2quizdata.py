import pandas as pd
import sqlite3
import json
import time
from google import genai

# --- Settings ---
API_KEY = "../../keys/gemini-key.txt"
EXCEL_FILE = "extracted_code_with_userid.xlsx"
MODEL_NAME = "gemini-3-flash-preview"

# --- Language ja ---
# LANG = "ja" 
# DB_FILE = "exam_data.db"

# --- Language en ---
LANG = "en" 
DB_FILE = "exam_data.en.db"

# --- Multi-language Config ---
CONFIG = {
    "ja": {
        "keys": ["行番号", "行の内容", "重要度", "説明", "偽説明"],
        "importance_key": "重要度",
        "prompt_instruction": """
以下のソースコードを解析し、1行ごとの解説を含むJSON配列を生成してください。
各要素は以下のキーを持つオブジェクトにしてください：
「行番号」(int), 「行の内容」(str), 「重要度」(1-3のint), 「説明」(str), 「偽説明」(str)

出力は純粋なJSON形式（配列）のみを返してください。
「偽説明」は、「説明」と似た内容だが正しくない選択肢として機能するようにしてください。
「説明」と「偽説明」は、それぞれ５０文字以内にしてください。
「print」文など自明な行の「重要度」は 1 にしてください。
必ず、重要なロジックを含む数行については「重要度」を 2 または 3 にしてください。
""",
    },
    "en": {
        "keys": ["line_number", "content", "importance", "explanation", "distractor"],
        "importance_key": "importance",
        "prompt_instruction": """
Analyze the following source code and generate a JSON array containing line-by-line explanations.
Each element must be an object with the following keys:
"line_number" (int), "content" (str), "importance" (int 1-3), "explanation" (str), "distractor" (str)

Return ONLY the pure JSON format (an array).
The "distractor" should be similar to the "explanation" but function as an incorrect option.
Keep "explanation" and "distractor" under 50 characters each.
Set "importance" to 1 for trivial lines like "print" statements.
Ensure that lines containing critical logic have an "importance" of 2 or 3.
""",
    }
}

# Initialize Client
with open(API_KEY, "r") as f:
    key = f.read().strip()

client = genai.Client(api_key=key)

def validate_quiz_json(json_str, lang):
    conf = CONFIG[lang]
    try:
        data = json.loads(json_str)
        if not isinstance(data, list):
            return False, "JSON is not a list."
        
        # extract lines of importance 2 or 3
        importance_key = conf["importance_key"]
        candidates = [item for item in data if isinstance(item, dict) and item.get(importance_key, 1) >= 2]
        
        if len(candidates) == 0:
            return False, f"No items with {importance_key} >= 2 found."
        
        required_keys = set(conf["keys"])
        for item in candidates:
            if not required_keys.issubset(item.keys()):
                return False, f"Missing keys: {required_keys - set(item.keys())}"
        
        return True, "OK"
    except json.JSONDecodeError:
        return False, "Failed to parse JSON."
    except Exception as e:
        return False, f"Unexpected error: {e}"

def generate_quiz_json_with_retry(source_code, lang, max_retries=3):
    """
    バリデーションを行い、失敗した場合は再試行する
    """
    conf = CONFIG[lang]
    prompt = f"{conf['prompt_instruction']}\n\n【Source Code】\n{source_code}"
    
    for i in range(max_retries):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt
            )
            clean_json = response.text.replace("```json", "").replace("```", "").strip()
            
            # バリデーション実行
            is_valid, message = validate_quiz_json(clean_json, lang)
            if is_valid:
                return clean_json
            else:
                print(f"  [Attempt {i+1}] Validation failed: {message} Retrying...")
        except Exception as e:
            print(f"  [Attempt {i+1}] Gemini API Error: {e}")
        
        time.sleep(2)
    
    return None

def main():
    print(f"Mode: {LANG}")
    print("Reading Excel file...")
    try:
        df = pd.read_excel(EXCEL_FILE)
    except Exception as e:
        print(f"Excel read error: {e}")
        return

    expected_col = 'extractedcode'
    if expected_col not in df.columns:
        print(f"Error: Column '{expected_col}' not found.")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exam_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            examid TEXT,
            submitfile TEXT,
            sourcecode TEXT,
            quizdatajson TEXT,
            UNIQUE(username, examid)
        )
    ''')

    for index, row in df.iterrows():
        username = str(row.get('username', 'Unknown'))
        examid = str(row.get('examid', ''))
        print(f"Processing ({index+1}/{len(df)}): {username} (ID: {examid})")
        
        # 言語設定を引数に渡す
        quiz_json = generate_quiz_json_with_retry(row[expected_col], LANG)
        
        if quiz_json:
            cursor.execute('''
                INSERT INTO exam_results (username, examid, submitfile, sourcecode, quizdatajson)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(username, examid) DO UPDATE SET
                    submitfile = excluded.submitfile,
                    sourcecode = excluded.sourcecode,
                    quizdatajson = excluded.quizdatajson
            ''', (
                username, 
                examid, 
                str(row.get('submitfile', '')), 
                str(row[expected_col]), 
                quiz_json
            ))
            conn.commit()
            print(f"Saved: {username}")
        else:
            print(f"❌ Failed: {username}")
        
        time.sleep(1)

    conn.close()
    print("Process completed.")

if __name__ == "__main__":
    main()
