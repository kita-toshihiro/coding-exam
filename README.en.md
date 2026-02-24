# coding-exam: Programming Quiz System (LTI Tool)

This project is a learning support tool that uses AI to analyze source code submitted by learners as programming assignments. It automatically generates personalized comprehension check quizzes for each learner to ensure they truly understand the meaning of the code they submitted.

It is designed to be called from an LMS via LTI 1.1. Operation has been verified on Ubuntu 22.04 and Moodle 4.5.

---

## For Learners: Quiz Interface

This interface tests whether the learner correctly understands the role and meaning of specific (important) lines in their source code. It features a two-column layout: the source code is displayed on the left, and the questions/options are on the right, allowing learners to answer while referring to their code.

### Key Features

* **Dynamic Question Generation**: 10 high-importance lines are randomly extracted and presented as questions each time.
* **Shuffle Function**: Correct answers and distractors are mixed, presenting a different order of options every time the quiz is run.
* **Immediate Feedback**: When "Practice Mode" is enabled, learners can see the pass/fail status and the correct answers for each line immediately after submission.

### Usage Flow

1. **Answering**: Select the appropriate explanation for each line from the dropdown menus.
2. **Submission**: Click the [Submit Answers] button to save the answers and score.
3. **Review**: In Practice Mode, a table comparing the correct answers with the learner's responses is displayed instantly.

---

## For Instructors: Management Panel

For each LMS resource (LTI link to this system), instructors can customize quiz settings and manage learner grades.

### Key Features

* **Quiz Settings**:
  * **ExamID Mapping**: Set or change the target Exam ID for each `resource_link_id` (LMS resource unit).
  * **Practice Mode Control**: Toggle "Practice Mode" ON/OFF to determine if learners can see correct answers and detailed explanations immediately after submission.


* **Grade Management**:
  * **Grade Data Filtering**: Extract and display only the results associated with the currently viewed resource from the total grade data.
  * **Real-time Aggregation**: Automatically calculate and list the highest scores of participating learners.
  * **CSV Download**: Download the grade list in CSV format (UTF-8 with BOM) for importing into external systems like Moodle.



### Operational Flow

1. **Configuration**: Enter the Exam ID, select the Practice Mode setting, and click [Save].
2. **Verification**: Review the highest scores per learner in the data table at the bottom of the screen.
3. **Output**: Save the CSV file using the [Download Grade Data] button.

---

## Language Switching (Japanese / English)

This system supports display in both Japanese and English.

The display language changes based on the current language settings of the LMS (such as Moodle) when calling the system.

The system reads the `launch_presentation_locale` parameter within the LTI request sent from the LMS.

* If it contains `ja`: Japanese display
* Otherwise: English display

---

## Setup

### 1. Install Dependencies

```bash
pip3 install streamlit fastapi uvicorn requests pandas google-genai openpyxl

```

### 2. Generate Quiz Data

Prepare `extracted_code_with_userid.xlsx`, which contains the learners' submitted code, in advance. You can execute AI-based question generation with the following command:

```bash
cd quizdata; python3 xlsx2quizdata.py

```

#### Structure of `extracted_code_with_userid.xlsx`

The source Excel file for quiz generation must have the following column names. `xlsx2quizdata.py` uses this data to automatically generate a dedicated quiz for each learner.

| Column Name | Description |
| --- | --- |
| `username` | Learner identifier (e.g., User ID number). Must match the username passed from LTI. |
| `examid` | Assignment identifier (e.g., `1`, `2`). Links with the ID specified in the Instructor Panel. |
| `extractedcode` | The source code for the questions (the code actually submitted by the learner). |
| `filename` | (Optional) Filename at the time of submission. Used for management purposes. |

Note: By using `quizdata/extract_code_and_save.ipynb`, you can extract program code from files submitted to a Moodle assignment and create a file with the structure required for `extracted_code_with_userid.xlsx`.

### 3. Settings for LMS Integration

To ensure secure integration with the LMS, please set the following variables in `main.py` appropriately:

* **`LTI_CONSUMER_KEY`**: Must match the "Consumer Key" of the LTI call (External Tool in Moodle) configured on the LMS side. Specify any string.
* **`ALLOWED_LMS_HOST`**: Specify the domain of the originating LMS.
  * To limit to a specific host (example): `ALLOWED_LMS_HOST = "moodle.your.domain"`
  * To set no restrictions (e.g., during development): `ALLOWED_LMS_HOST = "ALL"`


* Note: This is a simplified implementation that performs Consumer Key matching only; OAuth signature verification is not implemented.

### 4. Starting the Server

Running `main.py` starts both FastAPI (Port 8803) and Streamlit (Port 8802) simultaneously.
(Ports 8802 and 8803 must be accessible from the outside.)

```bash
python3 main.py

```

---

## Security Features

* **Copy-Paste Restrictions**: Right-clicking, text selection, copying, and printing are restricted via CSS settings in `utils.py`.

---

## File Configuration

| Filename | Role |
| --- | --- |
| `main.py` | **LTI Authentication Server**: Validates LTI requests and issues one-time tokens. |
| `app.py` | **Main App**: Displays the appropriate panel based on the user's role after authentication check. |
| `auth.py` | **Authentication Bridge**: Mediates token verification between FastAPI and Streamlit. |
| `components/quiz.py` | **Learner Screen**: Quiz answering, scoring, and result display for Practice Mode. |
| `components/instructor.py` | **Instructor Panel**: Exam ID settings, Practice Mode toggle, and grade CSV output. |
| `components/admin.py` | **Admin Screen**: Displays submission status and source code highlighting for all users. |
| `database.py` | **DB Management**: Handles reading and writing to SQLite. |
| `utils.py` | **Multilingual/UI Management**: Definitions for language resources and anti-copy CSS injection. |
| `quizdata/xlsx2quizdata.py` | **AI Question Generation**: Uses Gemini to analyze code and create questions. |
| `quizdata/extract_code_and_save.ipynb` | Extracts program code from Moodle assignment files to create the data file. |
