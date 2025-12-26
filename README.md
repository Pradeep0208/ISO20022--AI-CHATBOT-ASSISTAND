# ISO20022 AI Chatbot Assistant (RAG-based)

## 1) What is this project?
This project is a **website + backend service** that works like a smart assistant for **ISO 20022 payments messages** (like `pain.001`, `pacs.008`, `camt.053`, etc.).

Instead of searching a huge PDF manually, you can type a question like:

- “What is MsgId in pain.001?”
- “What is the definition and usage of <Assgnr> in camt.026?”
- “Show message building blocks for pacs.008”

…and the assistant will:
1. **Find the answer inside the ISO 20022 PDF documents**
2. **Explain it in simple language**
3. **Show the page number**
4. **Provide a PDF link** so you can verify it

This is useful for:
- Business Analysts in Payments & Wires
- Developers working on ISO 20022 migrations
- Anyone learning ISO 20022 message structures

---

## 2) What problem does it solve?
ISO 20022 documentation is large and complex (hundreds of pages per message family). Finding the correct definition/usage for an XML tag is slow and frustrating.

 This project turns ISO 20022 PDFs into a **searchable Q&A assistant**, saving time and improving understanding.

---

## 3) What does “RAG” mean (in simple words)?
**RAG = Retrieval-Augmented Generation**

That sounds technical, but here’s the simple meaning:

- **Retrieval** = the system first searches the PDFs and *retrieves the correct section*
- **Generation** = then it uses an AI model to rewrite that content in a clear answer

So the AI is not “guessing”.
It is answering **using your PDF content**, and it shows the page number for proof.

---

## 4) What is included in this repository?
This repo has two main parts:

### Backend (Python FastAPI)
- Runs the API (the “brain”)
- Reads ISO 20022 PDFs
- Extracts definitions, usage, and message building blocks
- Uses a local AI model (Ollama) to rewrite responses clearly

Folder:
```
backend/
  app/
    main.py
    rag_engine.py
  data/
    pain_messages.pdf
    pacs_messages.pdf
    camt_messages.pdf
```

### Frontend (React + Vite)
- The website UI (the “face”)
- Chat screen for questions and answers
- Sends your question to backend and displays the response

Folder:
```
frontend/
  src/
    App.jsx
    main.jsx
    api/apiClient.js
    components/ChatWindow.jsx
    components/MessageBubble.jsx
```

---

## 5) Tools & Technologies used (and why)

### Backend Technologies
| Tool / Tech | What it is | Why we used it | Benefit |
|------------|------------|----------------|---------|
| Python | Programming language | Backend logic | Fast to build, widely used |
| FastAPI | Web API framework | Creates endpoints like `/api/chat` | Very fast + automatic docs |
| PyPDF (pypdf) | PDF reader | Extracts text page-by-page | Reads ISO PDFs directly |
| Ollama | Local AI model runner | Turns extracted content into clean explanation | No cloud cost, runs locally |
| CORS | Browser security setting | Allows frontend to talk to backend | Needed for React ↔ API |

### Frontend Technologies
| Tool / Tech | What it is | Why we used it | Benefit |
|------------|------------|----------------|---------|
| React | UI library | Builds chat interface | Reusable components |
| Vite | Frontend build tool | Runs React fast | Very quick development |
| JavaScript | Web language | Frontend logic | Standard for web apps |
| Fetch API | Browser HTTP requests | Sends question to backend | Simple and reliable |

### Dev / Version Control
| Tool | Purpose | Benefit |
|------|---------|---------|
| Git | Tracks code changes | Safe history, rollback, collaboration |
| GitHub | Online repo hosting | Share with recruiters, portfolio proof |

---

## 6) How the system works (step-by-step)
When you ask a question in the chat:

### Step 1 — Frontend sends your question
The React frontend calls the backend API:
- Endpoint: `POST /api/chat`
- Payload: `{ "message": "your question here" }`

### Step 2 — Backend understands the intent
The backend checks what the user is asking:
- Is it asking for **definition/usage**?
- Is it asking for **message building blocks**?
- Which message family? (`pain`, `pacs`, `camt`)

### Step 3 — Backend searches the correct PDF pages
The RAG engine uses:
- Message → correct PDF file (pain/pacs/camt)
- Section mapping (table-of-contents style page range)
- Pattern-based extraction to locate:
  - **Definition**
  - **Usage**
  - Relevant explanation text

### Step 4 — AI improves readability (Ollama)
After extracting raw PDF text, the backend sends it to a local AI model via **Ollama**.
The AI rewrites it into:
- bullet points
- simplified explanation
- clean format

### Step 5 — Response returned to UI
The system returns:
- the answer
- page number
- PDF link (so you can verify)

---

## 7) How to run this project locally (beginner friendly)

### Prerequisites (install these first)
1. **Python** (recommended 3.10+)
2. **Node.js** (recommended 18+)
3. **Ollama** installed and running (for local AI rewriting)

---

### A) Run the Backend (FastAPI)

#### 1. Open terminal in backend folder:
Example path:
```
C:\Users\Pradeep Anand\Project\ISO20022\backend
```

#### 2. Create and activate a virtual environment (recommended)
```bash
python -m venv .venv
.\.venv\Scripts\activate
```

#### 3. Install required packages
If you have a `requirements.txt`, run:
```bash
pip install -r requirements.txt
```

If not, install the minimum:
```bash
pip install fastapi uvicorn pydantic requests pypdf
```

#### 4. Start the backend server
```bash
uvicorn app.main:app --reload --port 8000
```

Backend runs at:
- http://localhost:8000

---

### B) Run the Frontend (React)

#### 1. Open terminal in frontend folder:
Example path:
```
C:\Users\Pradeep Anand\Project\ISO20022\frontend
```

#### 2. Install frontend dependencies
```bash
npm install
```

#### 3. Start frontend
```bash
npm run dev
```

Frontend runs at:
- http://localhost:5173

---

## 8) How to use the chatbot
Open the website (frontend URL), and ask questions like:

- “What is MsgId in pain.001?”
- “Definition and usage of <Assgnr> in camt.026”
- “Message building blocks for pacs.008”

You will receive:
 Answer  
 Page number  
 PDF download link (for proof)

---

## 9) Important notes about PDFs
This repo includes ISO 20022 reference PDFs inside:

```
backend/data/
  pain_messages.pdf
  pacs_messages.pdf
  camt_messages.pdf
```

These PDFs are the main “knowledge source” for the chatbot.

---

## 10) Security / Secrets (.env handling)
This project supports `.env` files for secrets.

 `.env` files should **not** be pushed to GitHub.

This repo includes `.gitignore` rules for:
- `.env`
- `.env.*` (like `.env.local`, `.env.production`)
- `.venv`
- `node_modules`

If you ever need to share environment variables safely, use:
- `.env.example` (a template with empty values)

---

## 11) Common troubleshooting

### Problem: GitHub push permission denied (403)
 Fix: Make sure you are logged into the correct GitHub account in browser AND in Git credentials.
You already solved this by authenticating in browser.

---

### Problem: Backend runs but frontend shows no answer
 Check:
- Backend running at `http://localhost:8000`
- Frontend running at `http://localhost:5173`
- CORS allows frontend URL

---

### Problem: AI answer looks incomplete
 Usually means:
- the content was on the next page
- or the extraction didn’t capture full section
You can improve extraction rules in:
- `backend/app/rag_engine.py`

---

## 12) Future improvements (Roadmap)
Ideas to make this even stronger:
- Add support for more ISO 20022 families (sepa, acmt, etc.)
- Add “search by XML tag” dropdown
- Add citations for multiple pages
- Add deployment version (Hugging Face / Render / Railway)
- Add vector database retrieval for even smarter RAG

---

## 13) About the author
**Pradeep Anand M**  
Business Analyst / Scrum Master — Payments & Wires domain  
Project built to demonstrate:
- ISO 20022 domain expertise
- RAG + AI assistant capability
- Full-stack implementation (FastAPI + React)

---

## 14) License
This project is shared for learning and portfolio demonstration.
(You can add a LICENSE file if required.)
