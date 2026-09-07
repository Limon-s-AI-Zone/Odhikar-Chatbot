# Odhikar (অধিকার) — AI Paralegal for Legal Aid Clients

[![BRAC IT CodeSprint 2026](https://img.shields.io/badge/BRAC%20IT-CodeSprint%202026-d92d20.svg)](#)
[![Python](https://img.shields.io/badge/Backend-FastAPI%20%7C%20LangGraph-0284c7.svg)](#)
[![React](https://img.shields.io/badge/Frontend-React%2018%20%7C%20TypeScript%20%7C%20Vite-61dafb.svg)](#)

A Bangla-language voice-first conversational AI and Human-in-the-Loop (HITL) paralegal system that helps low-literacy clients describe legal problems in their own words, structures their case facts, performs safety escalation, drafts reviewed complaints, and routes them to a clinic.

---

## 🌟 Key Features

1. **Voice-First Bangla Intake**:
   * Voice recording interface with timer and everyday Bangla text fallback.
   * Tolerant of non-linear, emotional narratives without legal jargon.
2. **Safety Escalation (Emergency Break-out)**:
   * Real-time detection of ongoing physical violence or threats on every turn.
   * Instantly halts automated questioning and surfaces emergency hotlines (**16430**, **109**, **999**) while marking the case as **URGENT** in the paralegal queue.
3. **Token Budget & Continuation Control (LangGraph State Checkpoint)**:
   * Dynamically tracks estimated token usage on long or rambling narratives.
   * If token consumption crosses the threshold, the LangGraph flow pauses execution and prompts the user in Bangla: *"আপনার বিবরণটি দীর্ঘ... আপনি কি পরবর্তী টোকেন সম্পন্ন করতে চান?"*
   * Only after the user confirms continuation does LangGraph resume generating subsequent tokens for fact extraction and complaint drafting.
4. **Structured Classification & Fact Extraction**:
   * Powered by **Gemini 3.8 Flash** via **OpenRouter** and orchestrated with **LangGraph**.
   * Covers: *দেনমোহর ও ভরণপোষণ (Dower & Maintenance)*, *যৌতুক (Dowry)*, *বকেয়া মজুরি (Unpaid Wages)*, and *জমিজমা সংক্রান্ত বিরোধ (Land Disputes)*.
   * Solves implicit arithmetic (e.g., 10 days × 550 Tk = 5500 Tk, paid 3000 Tk, outstanding 2500 Tk).
   * Explicitly tags inferred facts (`inferred`) so paralegals never mistake guesses for client statements.
4. **The Model Understands, Templates Speak**:
   * All legal explanations and complaint drafts are assembled from **human-reviewed templates**, eliminating the risk of AI hallucinating legal advice.
5. **Human-in-the-Loop Paralegal Dashboard**:
   * Live incoming queue sorted by urgency.
   * Side-by-side comparison of structured facts and client verbatim words.
   * Built-in complaint editor allowing paralegals to fill placeholders and approve documents.

---

## 🏗️ Project Structure

```text
Odhikar — AI Paralegal/
│
├── backend/
│   ├── middleware/         # Dedicated AI pipeline & security middleware
│   │   ├── __init__.py
│   │   └── ai_middleware.py# Latency metrics, safety auditing, and input validation
│   ├── ai_pipeline.py      # LangGraph state graph (Transcribe -> Safety -> Classify -> Extract -> Dialogue -> Templates)
│   ├── prompts.py          # System prompts for Bangla classification, extraction, and safety
│   ├── templates.py        # Reviewed legal templates for complaint drafts & rights explanations
│   ├── main.py             # FastAPI server endpoints (Intake, Cases CRUD, CORS)
│   ├── models.py           # SQLAlchemy SQLite database models
│   ├── schemas.py          # Pydantic validation schemas
│   ├── database.py         # SQLite connection setup
│   ├── test_scenarios.py   # Test suite for BRD scenarios (N1, N6, N7)
│   └── requirements.txt    # Python dependencies
│
├── frontend/
│   ├── src/
│   │   ├── App.tsx               # Main container with Client / Paralegal tab navigation
│   │   ├── ClientIntake.tsx      # Voice/Text intake, follow-ups, rights, and safety break-out screens
│   │   ├── ParalegalDashboard.tsx# Case queue, fact inspector, verbatim viewer, complaint editor
│   │   ├── style.css             # Modern responsive styling & design tokens
│   │   └── main.tsx              # React DOM entrypoint
│   ├── package.json        # Frontend dependencies (React, Vite, Axios, Lucide)
│   ├── vite.config.ts      # Vite configuration & backend proxy (/api -> :8000)
│   └── tsconfig.json       # TypeScript configuration
│
├── brd.pdf                                          # Business Requirements Document
├── Odhikar_Supporting_Materials_Md. Shaiful Islam 20.pdf # Wireframes & Architecture
├── Odhikar_Test_Narratives_Md. Shaiful Islam 20.pdf     # 8 Scripted Test Narratives
└── README.md
```

---

## 🚀 How to Run the Project

### Prerequisites
* **Python 3.10+**
* **Node.js 18+ & npm**
* An **OpenRouter API Key** (or Gemini API Key)

---

### Step 1: Start the Backend (FastAPI)

1. Open a terminal and navigate to the `backend/` folder:
   ```bash
   cd backend
   ```

2. Create and activate a Python virtual environment:
   * **Windows (PowerShell)**:
     ```powershell
     python -m venv venv
     .\venv\Scripts\activate
     ```
   * **macOS/Linux**:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. Install required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables in `backend/.env`:
   ```dotenv
   OPENROUTER_API_KEY=your_openrouter_api_key_here
   MODEL_NAME=google/gemini-3.8-flash
   PORT=8000
   ```
   *(The backend automatically loads this `.env` file upon startup).*

5. Start the FastAPI server:
   ```bash
   uvicorn main:app --port 8000 --reload
   ```

The backend will be live at:
* **API**: `http://127.0.0.1:8000`
* **Interactive Swagger Documentation**: `http://127.0.0.1:8000/docs`

---

### Step 2: Start the Frontend (React + Vite)

1. Open a new terminal and navigate to the `frontend/` folder:
   ```bash
   cd frontend
   ```

2. Install npm dependencies:
   ```bash
   npm install
   ```

3. Run the development server:
   ```bash
   npm run dev
   ```

4. Open your browser and go to:
   ```text
   http://localhost:5173
   ```

---

## 🧪 Running Automated Tests

To run the automated verification suite against the BRD test narratives (**N1 Baseline Dower**, **N6 Physical Violence Breakout**, and **N7 Out-of-Scope Poisoned Cow**):

```powershell
cd backend
.\venv\Scripts\activate
python test_scenarios.py
```

---

## 📋 Walkthrough Demo Scenarios

In the web interface (`http://localhost:5173`), click **ক্লায়েন্ট সেবা (Client Intake)**. Quick-fill buttons are provided to demonstrate the core flows:

1. **দেনমোহর ও ভরণপোষণ (Scenario N1)**:
   * Demonstrates extracting multiple claims (unpaid dower + withheld maintenance), calculating relative dates, and producing a structured complaint.
2. **বকেয়া মজুরি (Scenario N4)**:
   * Demonstrates extracting verbal agreements, implicit math calculation (10 days × 550 Tk = 5500 Tk), and identifying lack of written contract.
3. **সহিংসতা ব্রেক-আউট (Scenario N6)**:
   * Demonstrates the safety check interrupting the flow mid-conversation, displaying emergency telephone lines (**16430**, **109**, **999**), and flagging the case as **URGENT** in the Paralegal Dashboard.

Switch to **প্যারালিগ্যাল ড্যাশবোর্ড (Paralegal Dashboard)** to view the live case queue, review inferred facts, and edit/approve the complaint drafts.
