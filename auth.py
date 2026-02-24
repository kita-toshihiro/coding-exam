import streamlit as st
import requests

# 認証サーバーのURL
FASTAPI_VALIDATE_URL = "https://thisapp.your.domain:8803/validate_token"

def check_auth():
    """
    ユーザーの認証状態をチェックし、必要に応じてトークン検証を行います。
    戻り値: 認証済みであれば True、未認証であれば False
    Checks the user's authentication status and performs token validation if necessary.
    Returns: True if authenticated, False if not.
    """
    # 1. 既にセッションにユーザー情報がある場合
    if "authenticated_user" in st.session_state:
        return True

    # 2. URLパラメータからトークンを取得
    params = st.query_params
    if "token" in params:
        url_token = params["token"]

        # 同一トークンの再処理を防止
        if st.session_state.get("last_processed_token") == url_token:
            st.error("このトークンはすでに使用されました。")
            return False

        try:
            # 認証サーバーへ検証リクエスト (SSL検証は元の設定に準拠)
            response = requests.get(
                FASTAPI_VALIDATE_URL, 
                params={"token": url_token}, 
                verify=False
            )

            if response.status_code == 200:
                auth_data = response.json()
                
                # セッション状態に必要な情報を格納
                st.session_state.update({
                    "authenticated_user": auth_data.get("username"),
                    "user_roles": auth_data.get("roles", ""),
                    "resource_link_id": auth_data.get("resource_link_id", ""),
                    "resource_link_title": auth_data.get("resource_link_title", ""),
                    "lang": auth_data.get("lang", "en"),
                    "last_processed_token": url_token
                })
                return True
            else:
                st.error("有効なトークンではありません。")
                return False

        except Exception as e:
            st.error(f"認証サーバーに接続できません: {e}")
            return False

    return False
