# Programming Quiz System (LTI Integration)

このプロジェクトは、LMS（Moodle等）から提出されたソースコードをAIで解析し、理解度チェック用のクイズを自動生成する学習支援ツールです。

## ⚙️ セキュリティ設定 (`main.py`)

LMSとの連携を安全に行うため、`main.py` 内の以下の変数を必ず設定してください。

* **`LTI_CONSUMER_KEY`**:
LMS側で設定する「コンシューマーキー」と一致させる必要があります。認証の整合性を保つための任意の文字列を指定してください。
* **`ALLOWED_LMS_HOST`**:
リクエストを許可するLMSのドメインを指定します（例: `canvas.instructure.com` や `moodle.your-u.ac.jp`）。
* 特定のホストに限定する場合: `ALLOWED_LMS_HOST = "md.kumamoto-u.ac.jp"`
* 開発中などで制限を設けない場合: `ALLOWED_LMS_HOST = "ALL"`



---

## 🌐 言語の切り替え方法 (日本語 / 英語)

本システムは多言語対応しており、以下の2つの方法で言語を切り替えることができます。

### 1. LTIパラメータによる自動判定

LMSから送信される LTI リクエスト内の `launch_presentation_locale` パラメータを自動的に読み取ります。

* `ja` を含む場合：日本語表示
* それ以外：英語表示（デフォルト）

### 2. 手動での切り替え（管理・デバッグ用）

`utils.py` 内の `get_text` 関数が言語リソースを管理しています。表示テキストを修正または追加したい場合は、`utils.py` 内の辞書オブジェクト（`TEXTS`）を編集してください。

> **注意**: 現在の言語設定は Streamlit の `st.session_state.lang` に保持されます。

---

## 🚀 構成図

---

## 📂 ファイル構成

| ファイル名 | 役割 |
| --- | --- |
| `main.py` | **LTI認証サーバー**: LTIリクエストを検証し、ワンタイムトークンを発行。 |
| `app.py` | **メインアプリ**: 認証チェック後、ユーザーのロールに応じたパネルを表示。 |
| `auth.py` | **認証ブリッジ**: FastAPIとStreamlit間のトークン検証を仲介。 |
| `components/quiz.py` | **学生用画面**: クイズの回答、採点、練習モード時の結果表示。 |
| `components/instructor.py` | **教員用パネル**: 試験ID設定、練習モード切替、成績CSV出力。 |
| `components/admin.py` | **管理者画面**: 全ユーザーの回答状況とソースコードのハイライト表示。 |
| `quizdata/xlsx2quizdata.py` | **AIクイズ生成**: Gemini 3 Flash を使用して Excel のコードを解析。 |
| `database.py` | **DB管理**: SQLite（`exam_data.db`）への読み書きを担当。 |
| `utils.py` | **多言語・UI管理**: 言語リソース定義とコピペ防止CSSの注入。 |

---

## 🛠 セットアップと実行

### 1. 依存ライブラリのインストール

```bash
pip install streamlit fastapi uvicorn requests pandas google-genai openpyxl

```

### 2. クイズデータの生成

あらかじめ `extracted_code_with_userid.xlsx` を用意し、AIによる問題生成を実行します。

```bash
python xlsx2quizdata.py

```

### 3. サーバーの起動

`main.py` を実行すると、FastAPI（ポート8803）とStreamlit（ポート8802）が同時に起動します。

```bash
python main.py

```

---

## 🔒 セキュリティ機能

* **コピペ制限**: `utils.py` の CSS 注入により、右クリック、テキスト選択、コピー、印刷を制限しています。
* **ワンタイムトークン**: `main.py` で生成されるトークンは 5分間 (`TOKEN_LIFETIME_SECONDS`) のみ有効で、一度検証されると破棄されます。

