import streamlit as st

def inject_custom_css():
    """コピペ防止、コード表示、および画面余白最小化のためのCSSを注入します。"""
    """Injects CSS for copy-paste prevention, code display, and minimal margin of screen space."""
    st.markdown("""
        <style>
        /* 1. ページ全体の余白削減 */
        .block-container {
            padding-top: 1rem !important;    /* 上部余白を大幅に削る */
            padding-bottom: 0rem !important;
            max-width: 95% !important;      /* 横幅を広く使う */
        }
        
        /* 2. ヘッダーと余計なスペースの削除 */
        header { visibility: hidden; height: 0px; }
        div[data-testid="stVerticalBlock"] { gap: 0.5rem !important; } /* ウィジェット間の隙間 */

        /* 3. コピペ・印刷防止 */
        body {
            -webkit-user-select: none; -moz-user-select: none;
            -ms-user-select: none; user-select: none;
            -webkit-touch-callout: none;
        }
        @media print { body { display: none !important; } }

        /* 4. コード表示スタイル */
        code {
            font-family: 'Courier New', Courier, monospace;
            white-space: pre;
        }
        .code-table { width: 100%; border-collapse: collapse; margin-top: 0px; }
        .code-line-num {
            width: 30px; color: #888; text-align: right;
            padding-right: 10px; border-right: 1px solid #ddd;
            user-select: none;
        }
        .code-content { padding-left: 10px; white-space: pre-wrap; word-break: break-all; }
        
        /* 5. セレクトボックス周りの余白をさらに詰める */
        div[data-testid="stSelectbox"] { margin-bottom: -10px; }
        </style>
    """, unsafe_allow_html=True)

def render_code_block(source_code):
    """行番号付きのソースコードテーブルを生成します。"""
    """Generates source code tables with line numbers."""
    lines = source_code.split('\n')
    html = '<div class="no-copy"><table class="code-table">'
    for i, line in enumerate(lines, 1):
        # &nbsp; 変換はそのままに、各行の高さを抑える
        safe_line = line.replace(' ', '&nbsp;')
        html += f'<tr><td class="code-line-num">{i}</td><td class="code-content"><code>{safe_line}</code></td></tr>'
    html += '</table></div>'
    st.html(html)


def get_text(key):
    """セッションの言語設定(ja/en)に基づいて翻訳テキストを返します。"""
    """Returns translated text based on the session language setting (ja/en)."""
    lang = st.session_state.get("lang", "en")
    
    translations = {
        # ヘッダー・指示
        "login_user": {"ja": "ログインユーザー", "en": "Logged in as"},
        "quiz_instruction": {
            "ja": "ソースコードの各行の説明として**最も適切なもの**を、候補の中から選んでください。最後に必ず、一番下の [ **解答を提出する** ] のボタンを押してください。",
            "en": "Select the **most appropriate** description for each line of the source code. Make sure to click the [ **Submit Answers** ] button at the bottom."
        },
        "data_not_found": {"ja": "データが見つかりません", "en": "Data not found"},
        
        # 選択肢・ラベル
        "select_placeholder": {"ja": "--- 選択してください ---", "en": "--- select ---"},
        "line_label": {"ja": "行目", "en": "Line"},
        
        # ボタン・メッセージ
        "submit_btn": {"ja": "解答を提出する", "en": "Submit Answers"},
        "save_success": {"ja": "解答が保存されました", "en": "Answers saved successfully"},
        
        # スコア・結果詳細
        "score_title": {"ja": "スコア", "en": "Score"},
        "detail_header": {"ja": "📝 解答詳細", "en": "📝 Detailed Results"},
        "col_line": {"ja": "行番号", "en": "Line No."},
        "col_code": {"ja": "コード", "en": "Code"},
        "col_your_ans": {"ja": "あなたの回答", "en": "Your Answer"},
        "col_judge": {"ja": "判定", "en": "Result"},
        "col_correct": {"ja": "正解の説明", "en": "Correct Description"},
        "judge_ok": {"ja": "✅ 正解", "en": "✅ Correct"},
        "judge_ng": {"ja": "❌ 不正解", "en": "❌ Incorrect"},

        # 教師用設定 (instructor.py)
        "inst_title": {"ja": "🛠 教員用設定", "en": "🛠 Instructor Settings"},
        "save_btn": {"ja": "設定を保存", "en": "Save Settings"},
        "grade_data": {"ja": "📥 このリンクの成績データ", "en": "📥 Grade Data for this link"},
        "practice_mode_checkbox_label": {"ja": "練習モード (スコア・正解を学生に表示する)", "en": "Practice mode (Score and correct answers displayed to students)"},
        "label_exam_id": {"ja": "試験 ID", "en": "Exam ID"},
        "msg_save_success": {"ja": "設定を保存しました！", "en": "Settings saved successfully!"},
        "grade_data_header": {"ja": "📥 このリンクの成績データ", "en": "📥 Grade Data for this link"},
        "col_idnumber": {"ja": "学籍番号/ユーザー名", "en": "ID Number/Username"},
        "btn_download_grade": {"ja": "成績用CSVをダウンロード", "en": "Download Grade CSV"},
        "no_data_for_link": {"ja": "このリンクでの回答データはまだありません。", "en": "No submission data found for this link."},
        
        # --- 管理画面用 (admin.py)  ---
        "admin_title": {"ja": "クイズ回答データ管理画面", "en": "Quiz Results Management"},
        "no_data_info": {"ja": "まだ提出されたデータはありません。", "en": "No data submitted yet."},
        "results_list_header": {"ja": "回答一覧", "en": "Submission List"},
        "col_username": {"ja": "ユーザー名", "en": "Username"},
        "col_timestamp": {"ja": "提出時間", "en": "Timestamp"},
        "col_action": {"ja": "操作", "en": "Action"},
        "btn_detail": {"ja": "詳細", "en": "Details"},
        "btn_download_csv": {"ja": "全データCSVダウンロード", "en": "Download All Data (CSV)"},
        "detail_view_title": {"ja": "詳細結果", "en": "Detailed View"},
        "label_source_code": {"ja": "提出されたソースコード", "en": "Submitted Source Code"},
        "label_answer_detail": {"ja": "解答詳細", "en": "Answer Details"},
        "btn_close_detail": {"ja": "詳細を閉じる", "en": "Close Details"},
        "data_not_found_in_db": {"ja": "問題データが見つかりませんでした。", "en": "Question data not found in DB."}
    }
    
    return translations.get(key, {}).get(lang, key)
