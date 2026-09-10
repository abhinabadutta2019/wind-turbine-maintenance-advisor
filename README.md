# Wind Turbine Maintenance Advisor

## Overview

This project is an **evidence-grounded Wind Turbine Operation and Maintenance Advisor** built from a technical maintenance manual.

The system combines **Natural Language Processing (NLP)**, **Information Retrieval (IR)**, structured maintenance knowledge, and an optional **LLM-assisted rewriting layer**.

The application supports two answer modes:

- **Offline / Evidence-grounded mode**
- **LLM-assisted mode**

The offline advisor is the main technical reasoning system. It retrieves relevant information from the maintenance manual using **TF-IDF and cosine similarity**, detects the user's intent and turbine component, and generates a grounded maintenance response.

The optional LLM layer uses the **Groq API** to improve the wording and presentation of the already-generated answer.

The LLM does **not independently generate maintenance recommendations**. The offline advisor remains the technical source of truth.

---

## Main Features

- TF-IDF document retrieval
- Cosine similarity ranking
- Rule-based component detection
- Rule-based intent detection
- Structured maintenance knowledge base
- Evidence-grounded maintenance answers
- Confidence estimation
- Tool and material extraction
- Safety information
- Supporting evidence from the source manual
- Optional Groq LLM rewriting
- Automatic offline fallback if the LLM is unavailable
- FastAPI REST API
- Next.js / React frontend

---

## Architecture

```text
User
  |
  v
Next.js Frontend
  |
  v
FastAPI REST API
  |
  v
Offline Maintenance Advisor
  |
  |-- Intent Detection
  |
  |-- Component Detection
  |
  |-- TF-IDF Retrieval
  |
  |-- Cosine Similarity
  |
  |-- Structured Knowledge Base
  |
  `-- Evidence-Grounded Answer
              |
              v
        Optional Groq LLM
        (readability rewriting only)
              |
              v
          Final Response
```

The core workflow is:

```text
Maintenance Manual
        |
        v
Text Chunks + Structured Knowledge
        |
        v
TF-IDF Retrieval
        |
        v
Cosine Similarity Ranking
        |
        v
Intent + Component Detection
        |
        v
Evidence-Grounded Offline Answer
        |
        +----------------------+
        |                      |
        | Offline Mode         | LLM-Assisted Mode
        |                      |
        v                      v
   Final Answer        Groq LLM Rewrite
                               |
                               v
                          Final Answer
```

---

## Project Structure

```text
code-july-24/
|
|-- backend/
|   `-- main.py
|
|-- data/
|   |-- chunks.json
|   `-- knowledge_base.json
|
|-- frontend/
|   |-- public/
|   |-- src/
|   |-- package.json
|   `-- ...
|
|-- reports/
|
|-- src/
|   |-- __init__.py
|   |-- advisor.py
|   |-- app.py
|   `-- llm_answer.py
|
|-- tests/
|
|-- .gitignore
|-- pytest.ini
|-- README.md
`-- requirements.txt
```

---

## How the Offline Advisor Works

The offline advisor performs the main technical processing.

### 1. Intent Detection

The system identifies the type of user request, such as:

- Maintenance
- Troubleshooting
- Safety
- Inspection
- General operation

### 2. Component Detection

The system detects which turbine component the question refers to.

Examples include:

- Battery
- Blades
- Tower
- Generator
- Electrical system
- Controller

### 3. Information Retrieval

The maintenance manual is divided into searchable text chunks.

The system uses:

- **TF-IDF vectorization**
- **Cosine similarity**

to rank manual sections according to their relevance to the user's question.

### 4. Structured Knowledge

A structured JSON knowledge base provides additional maintenance information such as:

- Recommended actions
- Tools and materials
- Safety information
- Component-specific guidance

### 5. Evidence-Grounded Answer

The advisor produces an answer using the retrieved and structured maintenance information.

The application also returns the supporting manual chunks and similarity scores so the user can inspect the evidence behind the response.

---

## Offline vs LLM-Assisted Mode

### Offline / Evidence-Grounded Mode

In offline mode, the answer is generated directly from the NLP and information-retrieval pipeline.

Example:

```text
1. Check if current is going into the batteries.
2. Make sure batteries are air-cooled.
```

No external LLM is required for this mode.

---

### LLM-Assisted Mode

The LLM-assisted mode first generates the same evidence-grounded technical answer.

That answer is then sent to the LLM only for **wording and presentation improvement**.

Example:

```text
LLM-polished response:

• Verify that current is flowing into the batteries.
• Ensure the batteries are air-cooled.
```

The LLM is instructed not to:

- Add new maintenance procedures
- Add unsupported technical information
- Add new tools or materials
- Add new safety instructions
- Change the technical meaning of the offline answer
- Independently answer the user's maintenance question

This keeps the system grounded while still demonstrating controlled LLM integration.

---

## LLM Integration

The project currently uses the **Groq API** with:

```text
openai/gpt-oss-20b
```

The architecture is:

```text
Manual
   |
   v
Information Retrieval
   |
   v
Grounded Technical Answer
   |
   v
Optional LLM Rewrite
```

If the Groq API is unavailable or the request fails, the application automatically returns the original offline answer.

This means the maintenance advisor remains usable even without the LLM service.

---

## API

The backend is implemented using **FastAPI**.

### Health Check

```http
GET /health
```

Example response:

```json
{
  "status": "ok"
}
```

---

### Advisor Endpoint

```http
POST /api/advisor
```

Example request:

```json
{
  "question": "How do I maintain the battery?",
  "mode": "offline"
}
```

Available modes:

```text
offline
llm
```

Example response structure:

```json
{
  "question": "How do I maintain the battery?",
  "intent": "maintenance",
  "component": "battery",
  "confidence": "medium",
  "answer": "Generated maintenance answer",
  "tools_materials": ["clamp meter"],
  "safety_topics": ["electrical"],
  "safety_warnings": [],
  "evidence": [],
  "answer_mode": "offline_advisor"
}
```

---

## Running the Project Locally

### 1. Clone the Repository

```bash
git clone https://github.com/abhinabadutta2019/wind-turbine-maintenance-advisor.git
```

Move into the project directory:

```bash
cd wind-turbine-maintenance-advisor
```

---

### 2. Create a Python Virtual Environment

```bash
python3 -m venv venv
```

Activate it on Linux/macOS:

```bash
source venv/bin/activate
```

---

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

---

## Environment Configuration

For LLM-assisted mode, create a `.env` file in the project root.

```env
GROQ_API_KEY=your_groq_api_key
```

Do not commit the `.env` file or API key to GitHub.

The offline advisor works without the Groq API.

---

## Run the FastAPI Backend

From the project root:

```bash
uvicorn backend.main:app --reload
```

The backend will run at:

```text
http://127.0.0.1:8000
```

Health check:

```text
http://127.0.0.1:8000/health
```

FastAPI documentation:

```text
http://127.0.0.1:8000/docs
```

---

## Run the Frontend

Open another terminal.

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Create:

```text
frontend/.env.local
```

Add:

```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

Then run:

```bash
npm run dev
```

The frontend will be available at:

```text
http://localhost:3000
```

---

## CLI Usage

The original Python command-line interface is also available.

### Offline Mode

```bash
python src/app.py "How do I maintain the battery?"
```

### LLM-Assisted Mode

```bash
python src/app.py "How do I maintain the battery?" --use-llm
```

---

## Example Questions

The advisor can be tested with questions such as:

```text
How do I maintain the battery?
```

```text
What should I do in case of short circuit?
```

```text
What safety equipment should I wear?
```

```text
How should I deal with rust on the turbine?
```

---

## Technologies

### Backend

- Python
- FastAPI
- Uvicorn
- scikit-learn

### NLP / Information Retrieval

- TF-IDF
- Cosine Similarity
- Rule-based Intent Detection
- Rule-based Component Detection
- Structured JSON Knowledge Base

### LLM

- Groq API
- GPT-OSS 20B

### Frontend

- Next.js
- React
- TypeScript
- Tailwind CSS

---

## Design Principles

The project follows several important design principles:

- The **offline advisor remains the technical source of truth**.
- Maintenance recommendations are grounded in retrieved manual information.
- Retrieved evidence is exposed to the user.
- The LLM is used only as a controlled rewriting layer.
- The application continues working when the LLM service is unavailable.
- API keys and environment files are excluded from version control.

---

## Current Status

The current version includes:

- Working offline NLP/IR advisor
- TF-IDF retrieval
- Evidence display
- Component and intent detection
- Confidence estimation
- FastAPI backend
- REST API
- Next.js frontend
- Offline / LLM-assisted mode selector
- Groq LLM integration
- LLM failure fallback
- Supporting evidence interface

---

## Future Improvements

Possible future extensions include:

- Improved component and intent classification
- More structured maintenance rules
- Evaluation on a larger maintenance-question dataset
- Improved manual preprocessing
- Additional turbine manuals
- Retrieval evaluation metrics
- Containerized deployment
- Expanded automated testing

---

## Author

**Abhinaba Dutta**

MSc in Data, Algorithms and Machine Intelligence  
University of Palermo, Italy

GitHub: [abhinabadutta2019](https://github.com/abhinabadutta2019)
