from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
import uvicorn
import threading
import os
import urllib.parse
import uuid
import time
from fastapi import HTTPException
from urllib.parse import urlparse

# --- Settings ---
LTI_CONSUMER_KEY = "ConsmKey999"  # Edit this
ALLOWED_LMS_HOST = "ALL"
# ALLOWED_LMS_HOST = "moodle.your.domain"

STREAMLIT_PORT = 8802
BRIDGE_PORT = 8803
HOST_IP = "0.0.0.0" # IP address of this web app
STREAMLIT_PUBLIC_URL = f"https://thisapp.your.domain:{STREAMLIT_PORT}"
#STREAMLIT_PUBLIC_URL = f"http://localhost:{STREAMLIT_PORT}"
cert_path='/etc/letsencrypt/live/thisapp.your.domain:/cert.pem'
key_path= '/etc/letsencrypt/live/thisapp.your.domain:/privkey.pem'

app = FastAPI()

# --- Global variables ---
# { "ワンタイムトークン": {"username": "ユーザー名", "expires_at": タイムスタンプ} }
# 簡易的にメモリに保存。
VALID_TOKENS = {}
TOKEN_LIFETIME_SECONDS = 30

# --- 1. LTI 受付用 endpoint (POST) ---
@app.post("/lti")
async def lti_login(request: Request):
    """
    MoodleからのPOSTリクエストを受け取り、
    StreamlitへGETリクエストとしてリダイレクトする
    """
    # 1. フォームデータを全て取得
    form_data = await request.form()
    
    # 2. 辞書型に変換してコンソールに綺麗に表示
    all_params = dict(form_data)
    print("\n" + "="*30)
    print(" [DEBUG] Moodle LTI Data Received:")
    for key, value in all_params.items():
        print(f" {key}: {value}")
    print("="*30 + "\n")

    # --- 言語設定の取得 ---
    # ja, ja_jp, ja-JP などの場合に 'ja' と判定
    locale = all_params.get('launch_presentation_locale', 'en').lower()
    lang = "ja" if locale.startswith("ja") else "en"

    # 1. Consumer Key の照合
    received_key = all_params.get("oauth_consumer_key")
    if received_key != LTI_CONSUMER_KEY:
        print(f"[ERROR] Invalid Consumer Key: {received_key}")
        raise HTTPException(status_code=403, detail="Invalid Consumer Key")

    # 2. ホスト名の制限
    if ALLOWED_LMS_HOST != "ALL":
        # 判定材料となるURLを取得
        target_url = all_params.get("launch_presentation_return_url") or all_params.get("tool_consumer_instance_guid")
        
        if target_url:
            # ホスト名を抽出
            parsed_host = urlparse(target_url).netloc or target_url
            print(f"[DEBUG] Validating host: {parsed_host} (Allowed: {ALLOWED_LMS_HOST})") # ここで出力
            
            if parsed_host != ALLOWED_LMS_HOST:
                print(f"[ERROR] Unauthorized host detected: {parsed_host}")
                raise HTTPException(status_code=403, detail=f"Access from {parsed_host} is not allowed.")
        else:
            print("[ERROR] Could not verify host origin (No URL data in LTI request)")
            raise HTTPException(status_code=403, detail="Origin verification failed.")
    else:
        print("[INFO] Host validation skipped (ALLOWED_LMS_HOST is not set)")

    
    # 3. 必要なデータを取り出す
    # getメソッドを使えば、項目がない場合もエラーにならず 'Guest' になる
    username = all_params.get('lis_person_sourcedid', 'Guest')
    #username = all_params.get('lis_person_name_full', 'Guest')
    roles = all_params.get('roles', '')
    resource_link_id = all_params.get('resource_link_id', '')
    resource_link_title = all_params.get('resource_link_title', 'Quiz') # タイトル取得
    
    # --- トークン生成と保存 ---
    token = str(uuid.uuid4()) # 一意なトークンを生成
    expires_at = time.time() + TOKEN_LIFETIME_SECONDS
    
    # トークン情報と有効期限を保存
    VALID_TOKENS[token] = {
        "username": username,
        "roles": roles,
        "resource_link_id": resource_link_id,
        "resource_link_title": resource_link_title,
        "lang": lang,
        "expires_at": expires_at
    }
    
    print(f"[DEBUG] Generated Token: {token} for user: {username}")
    
    # 4. Streamlitへリダイレクト

    # usernameの代わりにトークンをStreamlitへリダイレクト
    redirect_url = f"{STREAMLIT_PUBLIC_URL}/?token={token}"
    response = RedirectResponse(url=redirect_url, status_code=303)
    # 注意: LTIの仕様では302 (Found)が推奨される場合もありますが、
    # ここではブックマーク防止のために、トークンがすぐに期限切れになる前提で設計
    
    # セッションIDとしてトークンをCookieに保存 (samesite='None' はHTTPS必須)
    response.set_cookie(
        key="session_token", 
        value=token, 
        httponly=True, 
        secure=True, 
        samesite='None'
    )
    return response

# --- 3. Streamlitからのトークン検証用エンドポイント (GET/DELETE) ---
# main.py の validate_token エンドポイントのみ抜粋（他は変更なしでOK）
@app.get("/validate_token")
async def validate_token(token: str):
    if token not in VALID_TOKENS:
        # すでに削除されている場合にここに来る
        print(f"[WARN] Token already consumed or invalid: {token}")
        raise HTTPException(status_code=401, detail="Invalid or used token.")
        
    token_data = VALID_TOKENS[token]
    if time.time() > token_data["expires_at"]:
        del VALID_TOKENS[token]
        raise HTTPException(status_code=401, detail="Token expired.")
        
    # 全ての情報を返す
    data = {
        "username": token_data["username"],
        "roles": token_data["roles"],
        "resource_link_id": token_data["resource_link_id"],
        "resource_link_title": token_data.get("resource_link_title", ""),
        "lang": token_data.get("lang", "en")        
    }
    del VALID_TOKENS[token] # ここで削除される
    # print(f"[SUCCESS] Token validated and removed: {token} for {username}")
    return data

# --- 2. サーバー起動用の仕組み ---
def run_fastapi():
    """FastAPI (中継サーバー) を起動"""
    uvicorn.run(app, host=HOST_IP, port=BRIDGE_PORT,
                ssl_certfile=cert_path,
                ssl_keyfile=key_path
                )

def run_streamlit():
    """Streamlit アプリを起動"""
    # app.py は別途作成したStreamlitのファイル名
    #os.system(f"streamlit run app.py --server.port {STREAMLIT_PORT}")
    os.system(f"streamlit run app.py --server.port {STREAMLIT_PORT} --server.sslCertFile {cert_path} --server.sslKeyFile {key_path}")

    
if __name__ == "__main__":
    # FastAPIを別スレッドで起動しつつ、Streamlitをメインで起動
    t = threading.Thread(target=run_fastapi)
    t.daemon = True
    t.start()
    
    print("Starting Streamlit...")
    run_streamlit()

