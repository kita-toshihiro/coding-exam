import streamlit as st
import random
import json
import pandas as pd
from database import get_quiz_source_data, save_quiz_result
from utils import render_code_block, get_text

def run_quiz_app(username, resource_id, config):
    examid = config["examid"]
    practice_mode = config["practice_mode"]
    lang = st.session_state.get("lang", "en")

    # 2. 言語に基づいて DB ファイル名を決定 (xlsx2quizdata.py の仕様に合わせる)
    if lang == "ja":
        db_file = "exam_data.db"
    else:
        db_file = "exam_data.en.db"
    
    # 3. データの取得 (db_file を指定)
    db_entry = get_quiz_source_data(username, examid, db_file=db_file)
    
    if not db_entry:
        st.error(f"{get_text('data_not_found')} (ExamID: {examid}, DB: {db_file})")
        return

    st.markdown(f"##### {get_text('login_user')}: {username}")
    st.markdown(f"{get_text('quiz_instruction')} (examid: {examid})")
    #st.markdown(f"##### ログインユーザー: {username}")
    #st.markdown(f"ソースコードの各行の説明として**最も適切なもの**を、候補の中から選んでください。最後に必ず、一番下の [ **解答を提出する** ] のボタンを押してください。(examid: {examid})")

    quiz_data = json.loads(db_entry['quizdatajson'])

    # 言語ごとのキー定義
    if lang == "ja":
        K = {"ln": "行番号", "content": "行の内容", "imp": "重要度", "exp": "説明", "dist": "偽説明"}
    else:
        K = {"ln": "line_number", "content": "content", "imp": "importance", "exp": "explanation", "dist": "distractor"}
    
    # セッション状態の初期化
    if 'quiz_state' not in st.session_state:
        # 重要度(imp) 2以上の行を抽出
        candidates = [item for item in quiz_data if item.get(K["imp"], 1) >= 2]
        selected = sorted(random.sample(candidates, min(10, len(candidates))), key=lambda x: x[K["ln"]])
        
        # 選択肢の作成
        correct_answers = {item[K["ln"]]: item[K["exp"]] for item in selected}
        false_pool = [item[K["dist"]] for item in quiz_data if item[K["ln"]] in [s[K["ln"]] for s in selected]]
        options = list(correct_answers.values()) + false_pool
        random.shuffle(options)
        
        st.session_state.quiz_state = {
            "selected_lines": selected,
            "options": [get_text('select_placeholder')] + options,
            "correct_map": correct_answers,
            "scored": False
        }

    state = st.session_state.quiz_state
    
    # UIレイアウト
    col_left, col_right = st.columns([0.6, 0.4])
    with col_left:
        render_code_block(db_entry['sourcecode'])
    
    with col_right:
        user_answers = {}
        for item in state["selected_lines"]:
            ln = item[K["ln"]]
            # 言語によって「10行目」か「Line 10」か表示を切り替え
            line_text = f"{ln}{get_text('line_label')}" if lang == "ja" else f"{get_text('line_label')} {ln}"
            st.markdown(f"**{line_text}**: `{item[K['content']].strip()}`")

            user_answers[ln] = st.selectbox(
                f"Select description for line {ln}",  # 内部的なラベル（検索用など）
                state["options"], 
                key=f"sel_{ln}", 
                disabled=state["scored"],
                label_visibility="collapsed" 
            )

    # 提出ボタン
    if not state["scored"] and st.button(get_text("submit_btn"), type="primary"):
        score = sum(1 for ln, ans in user_answers.items() if ans == state["correct_map"][ln])
        # 結果の保存先も同様に db_file を指定可能なら渡す
        save_quiz_result(username, examid, resource_id, score, user_answers)
        state["score"] = score 
        state["scored"] = True
        st.rerun()

    if state["scored"]:
        st.success(get_text("save_success"))
        
        # 練習モードが有効な場合のみ詳細を表示
        if practice_mode:
            current_score = state.get("score", 0)
            st.markdown(f"## {get_text('score_title')}: {current_score} / {len(state['selected_lines'])}")
            
            # 結果表示用のデータリストを作成
            results_summary = []
            for item in state["selected_lines"]:
                ln = item[K["ln"]]
                user_ans = user_answers.get(ln)
                correct_ans = state["correct_map"].get(ln)
                is_correct = (user_ans == correct_ans)
                
                # テーブルのヘッダー
                results_summary.append({
                    get_text("col_line"): ln,
                    get_text("col_code"): item[K['content']].strip(),
                    get_text("col_your_ans"): user_ans,
                    get_text("col_judge"): get_text("judge_ok") if is_correct else get_text("judge_ng"),
                    get_text("col_correct"): correct_ans
                })
            
            # データフレームに変換して表示
            st.subheader(get_text("detail_header"))
            st.table(pd.DataFrame(results_summary))

