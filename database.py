import sqlite3
import pandas as pd
import json
from datetime import datetime
import os

# 保存先ディレクトリの設定
DB_DIR = "./db"
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)

# データベースパスの更新
DB_NAME = os.path.join(DB_DIR, "quiz_results.db")
CONFIG_DB_NAME = os.path.join(DB_DIR, "config.db")

# デフォルトのソースデータパス
DEFAULT_SOURCE_DB = "./quizdata/exam_data.db"

def init_all_dbs():
    """すべてのデータベースとテーブルを初期化します。"""
    # 回答保存用DB
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS quiz_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                formatted_username TEXT,
                examid TEXT,
                resource_link_id TEXT,
                time TEXT,
                selected_answers TEXT,
                score INTEGER
            )
        ''')
    
    # 設定用DB
    with sqlite3.connect(CONFIG_DB_NAME) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS resource_links (
                resource_link_id TEXT PRIMARY KEY,
                examid TEXT,
                practice_mode INTEGER DEFAULT 0
            )
        ''')

def get_quiz_source_data(username, examid, db_file=None):
    """
    試験データDBからデータを取得します。
    db_file が指定されていない場合はデフォルト(日本語)のDBを参照します。
    """
    if db_file is None:
        target_db = DEFAULT_SOURCE_DB
    else:
        target_db = os.path.join("./quizdata", db_file)

    try:
        with sqlite3.connect(target_db) as conn:
            query = "SELECT examid, sourcecode, quizdatajson FROM exam_results WHERE username = ? AND examid = ? ORDER BY id DESC LIMIT 1"
            df = pd.read_sql_query(query, conn, params=(username, examid))
            return df.iloc[0].to_dict() if not df.empty else None
    except Exception as e:
        print(f"Database Error: {e}")
        return None

def save_quiz_result(username, examid, resource_id, score, answers_dict):
    """ユーザーの回答結果を保存します。"""
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute('''
            INSERT INTO quiz_results (username, formatted_username, examid, resource_link_id, time, selected_answers, score) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            username, username, examid, resource_id, 
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
            json.dumps(answers_dict, ensure_ascii=False), score
        ))

def get_resource_config(resource_link_id, default_practice=False):
    """リソースIDに紐付く設定を取得します。"""
    with sqlite3.connect(CONFIG_DB_NAME) as conn:
        c = conn.cursor()
        c.execute('SELECT examid, practice_mode FROM resource_links WHERE resource_link_id = ?', (resource_link_id,))
        row = c.fetchone()
        if row:
            return {"examid": row[0], "practice_mode": bool(row[1])}
        return {"examid": None, "practice_mode": default_practice}

def update_resource_config(resource_id, examid, practice_mode):
    """教員による設定変更を保存します。"""
    with sqlite3.connect(CONFIG_DB_NAME) as conn:
        conn.execute('''
            INSERT INTO resource_links (resource_link_id, examid, practice_mode) 
            VALUES (?, ?, ?)
            ON CONFLICT(resource_link_id) DO UPDATE SET 
                examid=excluded.examid, 
                practice_mode=excluded.practice_mode
        ''', (resource_id, examid, 1 if practice_mode else 0))

def get_all_results():
    """quiz_results.db からすべての回答データを取得します。"""
    with sqlite3.connect(DB_NAME) as conn:
        df = pd.read_sql_query("SELECT * FROM quiz_results ORDER BY time DESC", conn)
    return df
