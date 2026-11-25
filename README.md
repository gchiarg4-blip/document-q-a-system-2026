# Document Question Answering System

A local Flask web application that accepts text-based PDF, DOCX, and TXT files, extracts their text, builds a keyword knowledge base, and retrieves relevant passages in response to questions.

## Project features

- Upload PDF, DOCX, and TXT documents (maximum 15 MB).
- Extract text from document paragraphs, PDF pages, and DOCX tables.
- Build an in-memory knowledge base and inverted keyword index.
- Retrieve evidence using simple keyword overlap and predefined question rules.
- Display the answer and matching source passages.
- No NLP model, embeddings, vector database, RAG pipeline, or external AI API is used.

## Requirements

- Python 3.10 or newer
- Packages listed in `requirements.txt`

## Run on Windows PowerShell

Open this folder in VS Code and run the following commands in the terminal:

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000` in your browser.

If the virtual environment already exists, skip the `python -m venv .venv` command. If it is already activated, you do not need to activate it again.

## How to use

1. Choose a text-based PDF, DOCX, or TXT file.
2. Select **Upload & build knowledge base**.
3. Wait for the upload-success message and record count.
4. Type a question and select **Ask**.
5. Review the retrieved answer and supporting source passages.

## Important limitations

- Scanned/image-only PDFs may not contain extractable text. OCR is not included.
- The knowledge base is stored in memory and is cleared when the Flask server stops.
- Keyword retrieval may miss answers expressed with words that do not appear in the question. It is not semantic search.
- The displayed match score measures keyword overlap; it is not a verified probability that an answer is correct.
- The built-in Flask development server is intended for local demonstration, not public production hosting.

## Main files

- `app.py`: Flask routes, document extraction, knowledge-base construction, and question answering.
- `templates/index.html`: webpage structure.
- `static/style.css`: page styling.
- `static/script.js`: upload and question interface logic.
- `uploads/`: uploaded documents saved during local testing.
