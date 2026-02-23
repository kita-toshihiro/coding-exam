import pandas as pd
import sqlite3
import json
import time
from google import genai

# --- Settings ---
API_KEY = "../../keys/gemini-key.txt"
EXCEL_FILE = "extracted_code_with_userid.xlsx"
DB_FILE = "exam_data.db"
MODEL_NAME = "gemini-3-flash-preview"

# Initialize Client
with open(API_KEY, "r") as f:
    key = f.read().strip()

client = genai.Client(api_key=key)

def validate_quiz_json(json_str):
    """
    生成されたJSONがアプリで正常に動作するかチェックする
    """
    try:
        data = json.loads(json_str)
        if not isinstance(data, list):
            return False, "JSONが配列形式ではありません。"
        
        # アプリのロジック: 重要度2以上の行を抽出してクイズにする
        candidates = [item for item in data if isinstance(item, dict) and item.get("重要度", 1) >= 2]
        
        if len(candidates) == 0:
            return False, "重要度2以上の行が見つかりません（クイズが生成できません）。"
        
        # 必要なキーが揃っているかチェック
        required_keys = {"行番号", "行の内容", "説明", "偽説明"}
        for item in candidates:
            if not required_keys.issubset(item.keys()):
                return False, f"必須キーが不足しています: {item}"
        
        return True, "OK"
    except json.JSONDecodeError:
        return False, "JSONのパースに失敗しました。"
    except Exception as e:
        return False, f"予期せぬエラー: {e}"

def generate_quiz_json_with_retry(source_code, max_retries=3):
    """
    バリデーションを行い、失敗した場合は再試行する
    """
    prompt = f"""
以下のソースコードを解析し、1行ごとの解説を含むJSON配列を生成してください。
各要素は以下のキーを持つオブジェクトにしてください：
「行番号」(int), 「行の内容」(str), 「重要度」(1-3のint), 「説明」(str), 「偽説明」(str)

出力は純粋なJSON形式（配列）のみを返してください。
「偽説明」は、「説明」と似た内容だが正しくない選択肢として機能するようにしてください。
「説明」と「偽説明」は、それぞれ５０文字以内にしてください。
「print」文など自明な行の「重要度」は 1 にしてください。
必ず、重要なロジックを含む数行については「重要度」を 2 または 3 にしてください。

【ソースコード】
{source_code}
"""
    for i in range(max_retries):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt
            )
            clean_json = response.text.replace("```json", "").replace("```", "").strip()
            
            # バリデーション実行
            is_valid, message = validate_quiz_json(clean_json)
            if is_valid:
                return clean_json
            else:
                print(f"  [試行 {i+1}] バリデーション失敗: {message} 再生成します...")
        except Exception as e:
            print(f"  [試行 {i+1}] Gemini API Error: {e}")
        
        time.sleep(2) # 再試行前の待機
    
    return None

def main():
    print("Excelファイルを読み込んでいます...")
    try:
        df = pd.read_excel(EXCEL_FILE)
    except Exception as e:
        print(f"Excel読み込みエラー: {e}")
        return

    expected_col = 'extractedcode'
    if expected_col not in df.columns:
        print(f"エラー: カラム '{expected_col}' が見つかりません。")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # テーブル作成時に UNIQUE 制約を追加しておくとUPSERTが楽になります
    # すでにDBファイルが存在する場合は、手動で削除するか、以下のロジックで対応します
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exam_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            examid TEXT,
            submitfile TEXT,
            sourcecode TEXT,
            quizdatajson TEXT,
            UNIQUE(username, examid) -- ここで重複を定義
        )
    ''')

    for index, row in df.iterrows():
        username = str(row.get('username', 'Unknown'))
        examid = str(row.get('examid', ''))
        print(f"処理中 ({index+1}/{len(df)}): {username} (ID: {examid})")
        
        quiz_json = generate_quiz_json_with_retry(row[expected_col])
        
        if quiz_json:
            # SQLite 3.24+ で利用可能な UPSERT (INSERT ... ON CONFLICT) を使用
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
            print(f"保存完了: {username}")
        else:
            print(f"❌ 保存失敗: {username} (有効なJSONを生成できませんでした)")
        
        time.sleep(1)

    conn.close()
    print("すべての処理が終了しました。")

if __name__ == "__main__":
    main()
