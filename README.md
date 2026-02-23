# Programming Quiz System (LTI Integration)

このプロジェクトは、LMS（Moodle等）から提出されたソースコードをAIで解析し、学生ごとにパーソナライズされた理解度チェック用のクイズを自動生成する学習支援ツールです。

動作検証は Ubuntu 22.04, Moodle 4.5 で行っています。

## LMSとの連携のための設定

LMSとの連携を安全に行うため、`main.py` 内の以下の変数を適切に設定してください。

* **`LTI_CONSUMER_KEY`**:
LMS側で設定するLTI呼び出し（Moodleでは「外部ツール」）の「コンシューマーキー」と一致させる必要があります。任意の文字列を指定してください。
* **`ALLOWED_LMS_HOST`**:
呼び出す元のLMSのドメインを指定します。
  * 特定のホストに限定する場合: `ALLOWED_LMS_HOST = "moodle.your-u.ac.jp"`
  * 構築中などで制限を設けない場合: `ALLOWED_LMS_HOST = "ALL"`


---

## 言語の切り替え (日本語 / 英語)

本システムは多言語対応しています。日本語か英語での表示です。

MoodleなどLMSの場合、LMS側の現在の言語設定に従って、本システムを呼び出した時の表示言語も変わります。

LMSから送信される LTI リクエスト内の `launch_presentation_locale` パラメータを自動的に読み取っています。
  * `ja` を含む場合：日本語表示
  * それ以外：英語表示（デフォルト）


---

## セットアップと実行

### 1. 依存ライブラリのインストール

```bash
pip3 install streamlit fastapi uvicorn requests pandas google-genai openpyxl

```

### 2. クイズデータの生成

あらかじめ `extracted_code_with_userid.xlsx` を用意してください。以下のコマンドによってAIによる問題生成を実行できます。

```bash
cd quizdata; python3 xlsx2quizdata.py

```

#### `extracted_code_with_userid.xlsx`の構造

クイズ生成の元となる Excel ファイルは、以下の列名を持つ必要があります。このデータを用いて、`xlsx2quizdata.py` が各学生専用のクイズを自動生成します。

| 列名 | 説明 |
| --- | --- |
| `username` | 学生の識別子（ユーザのDIナンバーなど）。LTIから渡されるユーザー名と一致させる必要があります。 |
| `examid` | 課題の識別番号（例: `1`, `2`）。教員パネルで指定する ID と連動します。 |
| `extractedcode` | 出題対象となるソースコード（学生が自分で提出したもの）。 |
| `filename` | （任意）提出時のファイル名。管理用に使用されます。 |
| `submitfile` | （任意）提出元ファイルのパスや詳細情報。 |

なお、quizdata/extract_code_and_save.ipynb を用いると、Moodleの課題に提出された各学習者の提出ファイルからプログラムのコードを抽出して、extracted_code_with_userid.xlsx に必要な構造を持つファイルを作成することができます。

### 3. サーバーの起動

`main.py` を実行すると、FastAPI（ポート8803）とStreamlit（ポート8802）が同時に起動します。
（8802 と 8803 のポートが、外部からアクセスできるようにしておく必要があります。）

```bash
python3 main.py

```

## セキュリティ機能

* **コピペ制限**: `utils.py` の CSS 注入により、右クリック、テキスト選択、コピー、印刷を制限しています。
* **ワンタイムトークン**: `main.py` で生成されるトークンは 5分間 (`TOKEN_LIFETIME_SECONDS`) のみ有効で、一度検証されると破棄されます。

---

## ファイル構成

| ファイル名 | 役割 |
| --- | --- |
| `main.py` | **LTI認証サーバー**: LTIリクエストを検証し、ワンタイムトークンを発行 |
| `app.py` | **メインアプリ**: 認証チェック後、ユーザーのロールに応じたパネルを表示 |
| `auth.py` | **認証ブリッジ**: FastAPIとStreamlit間のトークン検証を仲介 |
| `components/quiz.py` | **学生用画面**: クイズの回答、採点、練習モード時の結果表示 |
| `components/instructor.py` | **教員用パネル**: 試験ID設定、練習モード切替、成績CSV出力 |
| `components/admin.py` | **管理者画面**: 全ユーザーの回答状況とソースコードのハイライト表示 |
| `database.py` | **DB管理**: SQLite（`exam_data.db`）への読み書きを担当 |
| `utils.py` | **多言語・UI管理**: 言語リソース定義とコピペ防止CSSの注入 |
| `quizdata/xlsx2quizdata.py` | **生成AIでの問題データの生成**: Gemini を使用してコードを解析し問題を作成 |
| `quizdata/extract_code_and_save.ipynb` | Moodleの課題提出ファイルからプログラムのコードを抽出してデータファイルを作る | 

