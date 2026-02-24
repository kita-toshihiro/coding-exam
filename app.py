import streamlit as st
import streamlit.components.v1 as stc

# 作成したモジュールをインポート
from database import init_all_dbs, get_resource_config
from utils import inject_custom_css
from auth import check_auth
from components.admin import run_admin_panel
from components.instructor import run_instructor_panel
from components.quiz import run_quiz_app

# ページ全体の基本設定
st.set_page_config(
    page_title="Programming Quiz",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# データベースの初期化（初回起動時のみ）
init_all_dbs()

# セキュリティ・UIの調整
# 右クリック禁止スクリプト
stc.html("<script>document.addEventListener('contextmenu', event => event.preventDefault());</script>", height=0)
# カスタムCSS
inject_custom_css()

# 管理者専用
if st.query_params.get("admin") == "truetrue":
    # run_admin_panel()
    st.stop()

# 認証処理
# 既にログイン済みか、URLトークンによる認証を試みる
if not check_auth():
    st.warning("MoodleのLTIリンクからアクセスしてください。")
    st.warning("Please access via the LTI link in Moodle.")
    st.stop()

# --- 以降、認証済みユーザーのみ実行される ---

# セッションからユーザー情報を取得
current_user = st.session_state.get('authenticated_user')
user_roles = st.session_state.get('user_roles', '')
resource_link_id = st.session_state.get('resource_link_id', '')

# 教員用パネルの表示 (ロールに "Instructor" が含まれる場合)
if "Instructor" in user_roles:
    run_instructor_panel(resource_link_id)

# クイズアプリの実行（学生・教員共通）
# リソース設定（examid, practice_mode）をDBから取得
config = get_resource_config(resource_link_id)

if not config["examid"]:
    st.info(f"ログインユーザー: {current_user}")
    st.warning(f"このリンク ({resource_link_id}) には試験IDが割り当てられていません。教師に問い合わせてください。")
    st.warning(f"This link ({resource_link_id}) does not have an exam ID assigned. Please contact your teacher.")
else:
    # メインのクイズ画面を起動
    run_quiz_app(current_user, resource_link_id, config)
