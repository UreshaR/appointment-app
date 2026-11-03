# Appointment Management App

A small web app to create, edit, search and cancel appointments.
Built with Python (Flask), SQLite and plain HTML/JavaScript.

## Features
- Create, edit, delete appointments
- Validation: required fields, no past dates, no double-booking
- Search and filter by patient, date and status

## Run it
```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000

## Run tests
```
pytest
```