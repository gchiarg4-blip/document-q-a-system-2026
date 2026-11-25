from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import re
import uuid

from flask import Flask, jsonify, render_template, request
from werkzeug.utils import secure_filename
from docx import Document
from pypdf import PdfReader


BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 15 * 1024 * 1024  # 15 MB

ALLOWED_EXTENSIONS = {"txt", "pdf", "docx"}
# Knowledge bases stay available while this local Flask process is running.
knowledge_bases: dict[str, dict] = {}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def normalize(text: str) -> str:
    """Basic lowercase and punctuation normalization; no NLP model is used."""
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def split_sentences(text: str) -> list[str]:
    """Split text into small searchable units using punctuation and line breaks."""
    pieces = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [re.sub(r"\s+", " ", piece).strip() for piece in pieces if piece.strip()]


def extract_document(path: Path, extension: str) -> list[dict[str, str]]:
    """Extract readable text from a TXT, PDF, or DOCX file."""
    units: list[dict[str, str]] = []

    if extension == "txt":
        raw = path.read_text(encoding="utf-8", errors="replace")
        for line_number, line in enumerate(raw.splitlines(), start=1):
            text = line.strip()
            if text:
                units.append({"source": f"Line {line_number}", "text": text})

    elif extension == "pdf":
        reader = PdfReader(str(path))
        for page_number, page in enumerate(reader.pages, start=1):
            raw = page.extract_text() or ""
            # Preserve paragraph boundaries where present. Sentence splitting
            # later still works if a PDF page extracts as one long paragraph.
            paragraphs = re.split(r"\n\s*\n", raw)
            for paragraph in paragraphs:
                text = re.sub(r"\s+", " ", paragraph).strip()
                if text:
                    units.append({"source": f"Page {page_number}", "text": text})

    elif extension == "docx":
        document = Document(str(path))
        for number, paragraph in enumerate(document.paragraphs, start=1):
            text = re.sub(r"\s+", " ", paragraph.text).strip()
            if text:
                units.append({"source": f"Paragraph {number}", "text": text})

        # Include tables because assignment details are often stored in tables.
        for table_number, table in enumerate(document.tables, start=1):
            for row_number, row in enumerate(table.rows, start=1):
                text = " | ".join(
                    cell.text.strip() for cell in row.cells if cell.text.strip()
                )
                if text:
                    units.append({
                        "source": f"Table {table_number}, row {row_number}",
                        "text": text,
                    })

    return units


def build_knowledge_base(units: list[dict[str, str]]) -> dict:
    """Build searchable records and a simple inverted keyword index."""
    records = []
    inverted_index: dict[str, set[int]] = defaultdict(set)

    for record_id, unit in enumerate(units):
        terms = set(normalize(unit["text"]).split())
        if not terms:
            continue

        record = {
            "id": record_id,
            "source": unit["source"],
            "text": unit["text"],
            "terms": terms,
        }
        records.append(record)

        for term in terms:
            inverted_index[term].add(record_id)

    return {"records": records, "index": inverted_index}


STOP_WORDS = {
    "what", "is", "the", "a", "an", "of", "to", "in", "on", "for",
    "and", "how", "when", "where", "who", "which", "are", "was",
    "were", "do", "does", "did", "me", "tell", "about", "please",
    "can", "you", "give", "explain", "find", "show", "describe",
}
DATE_PATTERN = re.compile(
    r"\b(?:"
    r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}"
    r"|\d{1,2}\s+(?:January|February|March|April|May|June|July|August|"
    r"September|October|November|December)\s*,?\s+\d{4}"
    r"|(?:January|February|March|April|May|June|July|August|September|"
    r"October|November|December)\s+\d{1,2},?\s+\d{4}"
    r")\b",
    re.IGNORECASE,
)


def answer_question(question: str, kb: dict) -> dict:
    """Retrieve evidence with keyword overlap and simple question-type rules."""
    question_terms = set(normalize(question).split())
    if not question_terms:
        return {"answer": "Please enter a question.", "matches": [], "confidence": 0}

    important_terms = question_terms - STOP_WORDS
    if not important_terms:
        important_terms = question_terms

    question_type = "general"
    if {"date", "when", "deadline", "due"} & question_terms:
        question_type = "date"
    elif {"who", "author", "person", "name"} & question_terms:
        question_type = "person"
    elif {"define", "definition", "meaning"} & question_terms:
        question_type = "definition"

    candidate_ids: set[int] = set()
    for term in important_terms:
        candidate_ids.update(kb["index"].get(term, set()))

    scored = []
    for record in kb["records"]:
        if record["id"] not in candidate_ids:
            continue

        for sentence in split_sentences(record["text"]):
            sentence_terms = set(normalize(sentence).split())
            overlap = important_terms & sentence_terms
            if not overlap:
                continue

            # A transparent keyword-overlap score, not a probability of correctness.
            score = len(overlap) / max(len(important_terms), 1)
            date_match = DATE_PATTERN.search(sentence)

            # Prefer a sentence containing a date for date-related questions.
            if question_type == "date" and date_match:
                score += 0.35
            if question_type == "date" and ({"date", "deadline", "submission", "due"} & sentence_terms):
                score += 0.10

            scored.append({
                "text": sentence,
                "source": record["source"],
                "score": min(score, 1.0),
                "date": date_match.group(0) if date_match else None,
            })

    scored.sort(key=lambda item: item["score"], reverse=True)

    if not scored or scored[0]["score"] < 0.25:
        return {
            "answer": "I could not find enough matching information in the uploaded document.",
            "matches": [],
            "confidence": 0,
        }

    best = scored[0]
    answer = best["text"]
    if question_type == "date" and best["date"]:
        answer = best["date"]

    matches = [
        {
            "text": item["text"],
            "source": item["source"],
            "score": round(item["score"], 2),
        }
        for item in scored[:3]
    ]

    return {
        "answer": answer,
        "matches": matches,
        "confidence": round(best["score"], 2),
    }


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/upload", methods=["POST"])
def upload_file():
    # The HTML form and JavaScript both use the exact key "file".
    if "file" not in request.files:
        return jsonify({"error": "No file was received. Please choose a document and try again."}), 400

    uploaded_file = request.files["file"]
    if not uploaded_file or uploaded_file.filename == "":
        return jsonify({"error": "No file selected. Choose a PDF, DOCX, or TXT file."}), 400

    if not allowed_file(uploaded_file.filename):
        return jsonify({"error": "Unsupported file type. Please upload a PDF, DOCX, or TXT file."}), 400

    safe_name = secure_filename(uploaded_file.filename)
    extension = safe_name.rsplit(".", 1)[1].lower()
    saved_path = UPLOAD_DIR / f"{uuid.uuid4().hex}_{safe_name}"

    try:
        uploaded_file.save(saved_path)
        units = extract_document(saved_path, extension)
        if not units:
            return jsonify({
                "error": "No readable text was found. The document may be empty or scanned as an image.",
            }), 400

        kb = build_knowledge_base(units)
        if not kb["records"]:
            return jsonify({"error": "The document did not contain searchable text."}), 400

        kb_id = str(uuid.uuid4())
        knowledge_bases[kb_id] = kb
        return jsonify({
            "message": "Document uploaded and knowledge base created.",
            "kb_id": kb_id,
            "filename": safe_name,
            "record_count": len(kb["records"]),
        }), 200

    except Exception as exc:
        app.logger.exception("Document upload failed")
        return jsonify({"error": f"Could not process this document: {exc}"}), 500
    finally:
        # Keep the uploaded document in uploads/ for local project demonstration.
        pass


@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json(silent=True) or {}
    question = str(data.get("question", "")).strip()
    kb_id = data.get("kb_id")

    if not question:
        return jsonify({"error": "Please enter a question."}), 400
    if not kb_id or kb_id not in knowledge_bases:
        return jsonify({"error": "Upload a document before asking questions."}), 400

    return jsonify(answer_question(question, knowledge_bases[kb_id]))


@app.errorhandler(413)
def file_too_large(_error):
    return jsonify({"error": "The file is too large. The maximum upload size is 15 MB."}), 413


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
