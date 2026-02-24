import streamlit as st
import pandas as pd
from database import get_resource_config, update_resource_config, get_all_results
from utils import get_text

def run_instructor_panel(resource_link_id):
    st.divider()
    st.subheader(get_text("inst_title"))

    # 現在の設定を取得
    config = get_resource_config(resource_link_id)
    
    with st.form("set_config"):
        label_exam_id = f"{get_text('label_exam_id')} (resource_link_id: {resource_link_id})"
        new_examid = st.text_input(label_exam_id, value=config["examid"] or "")
        new_practice = st.checkbox(get_text("practice_mode_checkbox_label"), value=config["practice_mode"])
        
        if st.form_submit_button(get_text("save_btn")):
            update_resource_config(resource_link_id, new_examid, new_practice)
            st.success(get_text("msg_save_success"))
            st.rerun()

    # 成績データの表示・ダウンロード
    if config["examid"]:
        st.write("---")
        st.subheader(get_text("grade_data_header"))
        
        all_results_df = get_all_results()
        if not all_results_df.empty:
            # 現在のリソースリンクIDでフィルタリング
            filtered_df = all_results_df[all_results_df['resource_link_id'] == resource_link_id].copy()
            
            if not filtered_df.empty:
                session_title = st.session_state.get('resource_link_title', f"Exam_{config['examid']}")
                
                # ユーザーごとの最高点を算出
                grade_df = filtered_df.groupby('username')['score'].max().reset_index()
                grade_df.columns = [get_text('col_idnumber'), session_title]

                st.dataframe(grade_df, use_container_width=True)

                csv_data = grade_df.to_csv(index=False).encode('utf_8_sig')
                st.download_button(
                    label=f"{get_text('btn_download_grade')} ({session_title})",
                    data=csv_data,
                    file_name=f"grades_{resource_link_id}.csv",
                    mime="text/csv"
                )
            else:
                st.info(get_text("no_data_for_link"))
