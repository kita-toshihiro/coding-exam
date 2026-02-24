import streamlit as st
import pandas as pd
import json
import sqlite3
import os
from database import get_all_results
from utils import get_text

def run_admin_panel():
    st.title(f"📊 {get_text('admin_title')}")
    
    if "view_detail_id" not in st.session_state:
        st.session_state.view_detail_id = None

    df = get_all_results()
    if df.empty:
        st.info(get_text('no_data_info'))
        return

    st.subheader(get_text('results_list_header'))
    
    # テーブル形式で表示
    cols = st.columns([0.5, 1.5, 1, 1.5, 0.8, 1.5, 1])
    # 各カラムのヘッダーを get_text で取得
    headers = [
        "ID", 
        get_text('col_username'), 
        "ExamID", 
        "ResourceID", 
        get_text('col_score'), 
        get_text('col_timestamp'), 
        get_text('col_action')
    ]
    for col, head in zip(cols, headers):
        col.markdown(f"**{head}**")

    for _, row in df.iterrows():
        c1, c2, c3, c4, c5, c6, c7 = st.columns([0.5, 1.5, 1, 1.5, 0.8, 1.5, 1])
        c1.text(row['id'])
        c2.text(row['username'])
        c3.text(row['examid'])
        c4.text(row.get('resource_link_id', 'N/A'))
        c5.text(row['score'])
        c6.text(row['time'])
        # ボタン名「詳細」を多言語化
        if c7.button(get_text('btn_detail'), key=f"btn_{row['id']}"):
            st.session_state.view_detail_id = row['id']
            st.rerun()

    # 詳細表示エリア
    if st.session_state.view_detail_id:
        render_detail_view(df)

    st.divider()
    csv = df.to_csv(index=False).encode('utf_8_sig')
    st.download_button(get_text('btn_download_csv'), data=csv, file_name="all_results.csv", mime="text/csv")

def render_detail_view(df):
    detail_id = st.session_state.view_detail_id
    detail_row = df[df['id'] == detail_id].iloc[0]
    
    st.divider()
    st.subheader(f"📝 {get_text('detail_view_title')} (ID: {detail_id})")
    
    # DBを自動探索
    possible_dbs = ["./quizdata/exam_data.db", "./quizdata/exam_data.en.db"]
    q_df = pd.DataFrame()
    
    for db_path in possible_dbs:
        if not os.path.exists(db_path):
            continue
        try:
            with sqlite3.connect(db_path) as conn:
                query = "SELECT sourcecode, quizdatajson FROM exam_results WHERE username = ? AND examid = ? ORDER BY id DESC LIMIT 1"
                temp_df = pd.read_sql_query(query, conn, params=(detail_row['username'], detail_row['examid']))
                if not temp_df.empty:
                    q_df = temp_df
                    break
        except Exception:
            continue

    if not q_df.empty:
        source_code = q_df.iloc[0]['sourcecode']
        quiz_data = json.loads(q_df.iloc[0]['quizdatajson'])
        
        # キーの自動判別（日本語 or 英語）
        sample_item = quiz_data[0] if quiz_data else {}
        ln_key = "行番号" if "行番号" in sample_item else "line_number"
        exp_key = "説明" if "説明" in sample_item else "explanation"

        quiz_lookup = {str(item[ln_key]): item for item in quiz_data}
        user_answers = json.loads(detail_row['selected_answers'])

        col_left, col_right = st.columns([0.5, 0.5])
        with col_left:
            st.markdown(f"**{get_text('label_source_code')}**")
            display_highlighted_code(source_code, user_answers)

        with col_right:
            st.markdown(f"**{get_text('label_answer_detail')}**")
            show_results_table(user_answers, quiz_lookup, exp_key)
    else:
        st.warning(get_text('data_not_found_in_db'))
    
    if st.button(get_text('btn_close_detail'), type="primary"):
        st.session_state.view_detail_id = None
        st.rerun()

def display_highlighted_code(source_code, user_answers):
    lines = source_code.split('\n')
    code_html = '<div style="background-color: #f0f2f6; padding: 10px; font-family: monospace; font-size: 0.8em;">'
    for i, line in enumerate(lines, 1):
        bg_color = "#ffffcc" if str(i) in user_answers else "transparent"
        code_html += f'<div style="background-color: {bg_color};"><span style="color: #888; margin-right: 10px;">{i:02d}</span>{line.replace(" ", "&nbsp;")}</div>'
    code_html += '</div>'
    st.html(code_html)

def show_results_table(user_answers, quiz_lookup, exp_key):
    results = []
    for ln, ans in user_answers.items():
        q_info = quiz_lookup.get(str(ln), {})
        correct_desc = q_info.get(exp_key, "???")
        results.append({
            get_text('col_line'): ln,
            get_text('col_your_ans'): ans,
            get_text('col_correct'): correct_desc,
            get_text('col_judge'): "✅" if ans == correct_desc else "❌"
        })
    st.table(pd.DataFrame(results))
