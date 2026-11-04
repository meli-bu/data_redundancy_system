# Task 1: Data Redundancy Removal System

A small Flask + SQLite project that checks incoming data before saving it.

## Features

- Normalizes text to ignore case and repeated spaces.
- Classifies exact matches as `redundant`.
- Detects close matches as `possible_duplicate` for review.
- Allows a reviewer to confirm that a similar-looking entry is genuinely unique; it is then labelled `false_positive`.
- Saves only unique, verified records.
- Uses parameterized SQL queries and a database uniqueness constraint.

## Run

```bash
python -m venv .venv
```

Activate the environment:

Windows:
```powershell
.venv\Scripts\activate
```

macOS/Linux:
```bash
source .venv/bin/activate
```

Install and start:

```bash
pip install -r requirements.txt
python app.py
```

The API runs at `http://127.0.0.1:5000`.

## Test with Postman or Thunder Client

### Add a new record

`POST http://127.0.0.1:5000/records`

JSON:
```json
{"value": "Adama Science and Technology University"}
```

### Try the same record again

Send the same text, or change its letter case / add extra spaces. It will be classified as `redundant`.

### Review a similar record

Send a similar but not identical value. The API may return `possible_duplicate`. Review the suggested match.

If it is genuinely different information, confirm it:

`POST http://127.0.0.1:5000/records/confirm`

JSON:
```json
{
  "value": "Adama Science and Technology University Library",
  "confirmed_unique": true
}
```

The result is classified as `false_positive` and saved.

### View all records

`GET http://127.0.0.1:5000/records`

## Push to GitHub

```bash
git init
git add .
git commit -m "Implement data redundancy removal system"
git branch -M main
git remote add origin YOUR_GITHUB_REPOSITORY_URL
git push -u origin main
```

This is an educational prototype. The similarity threshold is a simple heuristic and should be adjusted for the kind of data being stored. A real system should include authentication and a proper review interface.
