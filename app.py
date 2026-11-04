from flask import Flask, request, jsonify
import sqlite3
import re
import unicodedata
from difflib import SequenceMatcher

app = Flask(__name__)
DATABASE = "records.db"


def connect_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    with connect_db() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                value TEXT NOT NULL,
                normalized_value TEXT NOT NULL UNIQUE
            )
        """)


def normalize(value):
    """Make harmless differences such as case and extra spaces consistent."""
    value = unicodedata.normalize("NFKC", value)
    value = value.casefold().strip()
    return re.sub(r"\s+", " ", value)


def find_similar_record(normalized_value):
    """Return a close existing record, if one is found."""
    with connect_db() as connection:
        records = connection.execute(
            "SELECT id, value, normalized_value FROM records"
        ).fetchall()

    for record in records:
        similarity = SequenceMatcher(
            None, normalized_value, record["normalized_value"]
        ).ratio()

        if similarity >= 0.90:
            return {
                "id": record["id"],
                "value": record["value"],
                "similarity": round(similarity, 2)
            }

    return None


@app.get("/")
def home():
    return jsonify({
        "message": "Data Redundancy Removal System",
        "endpoints": {
            "POST /records": "Check and add a record",
            "GET /records": "View all stored records"
        }
    })


@app.post("/records")
def add_record():
    data = request.get_json(silent=True) or {}
    value = data.get("value")

    if not isinstance(value, str) or not value.strip():
        return jsonify({"error": "Please provide a non-empty 'value'."}), 400

    normalized_value = normalize(value)

    # Exact match: definitely redundant.
    with connect_db() as connection:
        existing = connection.execute(
            "SELECT id, value FROM records WHERE normalized_value = ?",
            (normalized_value,)
        ).fetchone()

        if existing:
            return jsonify({
                "classification": "redundant",
                "message": "This data already exists. It was not added.",
                "existing_record_id": existing["id"],
                "existing_value": existing["value"]
            }), 409

    # Similar match: do not reject automatically. It may be a false positive.
    possible_match = find_similar_record(normalized_value)

    if possible_match:
        return jsonify({
            "classification": "possible_duplicate",
            "message": (
                "A similar record was found. Review it before deciding. "
                "If it is different information, add it with confirmed_unique=true."
            ),
            "possible_match": possible_match
        }), 200

    return save_unique_record(value, normalized_value)


@app.post("/records/confirm")
def confirm_unique_record():
    """Save a similar-looking record after a person confirms it is genuinely unique."""
    data = request.get_json(silent=True) or {}
    value = data.get("value")
    confirmed = data.get("confirmed_unique", False)

    if not isinstance(value, str) or not value.strip():
        return jsonify({"error": "Please provide a non-empty 'value'."}), 400

    if confirmed is not True:
        return jsonify({
            "error": "Set confirmed_unique to true after reviewing the possible match."
        }), 400

    normalized_value = normalize(value)
    return save_unique_record(value, normalized_value, false_positive=True)


def save_unique_record(value, normalized_value, false_positive=False):
    try:
        with connect_db() as connection:
            cursor = connection.execute(
                "INSERT INTO records (value, normalized_value) VALUES (?, ?)",
                (value.strip(), normalized_value)
            )
            record_id = cursor.lastrowid

        classification = "false_positive" if false_positive else "unique"

        return jsonify({
            "classification": classification,
            "message": "Unique data successfully added.",
            "record_id": record_id
        }), 201

    except sqlite3.IntegrityError:
        # Protects against duplicates even if two requests arrive close together.
        return jsonify({
            "classification": "redundant",
            "message": "This data already exists. It was not added."
        }), 409


@app.get("/records")
def get_records():
    with connect_db() as connection:
        records = connection.execute(
            "SELECT id, value FROM records ORDER BY id"
        ).fetchall()

    return jsonify({
        "records": [dict(record) for record in records]
    })


initialize_database()

if __name__ == "__main__":
    app.run(debug=True)
