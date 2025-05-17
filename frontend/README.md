# PhenoML FHIR Chat Interface

A modern chat interface for interacting with the PhenoML FHIR agent.

## Setup

1. Install frontend dependencies:
```bash
cd frontend
npm install
```

2. Install backend dependencies:
```bash
pip install flask flask-cors
```

## Running the Application

1. Start the backend server:
```bash
python server.py
```

2. In a new terminal, start the frontend development server:
```bash
cd frontend
npm start
```

The application will be available at http://localhost:3000

## Features

- Modern, responsive chat interface
- Real-time message updates
- Loading indicators
- Error handling
- Automatic scrolling to latest messages

## Environment Variables

Make sure you have the following environment variables set:
- PHENOML_TOKEN
- MEDPLUM_TOKEN or CANVAS_TOKEN
- CANVAS_INSTANCE_IDENTIFIER (if using Canvas) 