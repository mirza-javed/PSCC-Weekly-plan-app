# PSCC Weekly Teaching Plan — All-in-One Vercel Deployment Guide

This repository is configured for **100% Free All-in-One deployment on Vercel** (Frontend React SPA + Python Serverless API + Google Sheets Backend).

---

## 1. Local Development Setup

### Prerequisites
* Python 3.10+ installed
* Node.js 18+ installed

### Step 1: Install Dependencies
```bash
# 1. Activate Python virtual environment and install backend requirements
venv\Scripts\activate          # Windows
pip install -r requirements.txt

# 2. Install frontend dependencies
npm install
```

### Step 2: Run Development Servers
Open two terminal windows:

**Terminal 1 (Backend API):**
```bash
venv\Scripts\activate
python dev_server.py
# API runs on http://127.0.0.1:8000
```

**Terminal 2 (Frontend SPA):**
```bash
npm run dev
# React App opens on http://localhost:5173
```

---

## 2. Deploying to Vercel (100% Free)

### Option A: Deploy via GitHub (Recommended)
1. Push your repository to GitHub (`git push origin main`).
2. Go to **[vercel.com](https://vercel.com)** and sign in with your GitHub account.
3. Click **"Add New..."** → **"Project"** and import your `Time_Table_Weekly_planner` repository.
4. In the Project Configuration:
   * **Framework Preset:** Vite
   * **Root Directory:** `./`
5. Under **Environment Variables**, add:
   * `SPREADSHEET_ID`: `1x5wykhZlN2-pFqrreCFvQmDZikZkV8_1fr5igQ-6GCk`
   * `GCP_SERVICE_ACCOUNT`: Paste the **entire contents** of your `.streamlit/secrets.toml` service account JSON object (or service account JSON file).
6. Click **"Deploy"**.

Vercel will build the frontend into static assets and deploy the `/api` directory as Python serverless functions under a single, free `.vercel.app` URL (with free SSL and custom domain support).

---

## 3. Architecture Summary

```
+-------------------------------------------------------------------------+
|                       VERCEL HOSTING (100% FREE)                        |
|                                                                         |
|  [Static Frontend CDN]                                                  |
|  - React 19 / Preact + Vite (~73 KB gzipped)                           |
|  - 100% Mobile-first UI with 48px tap targets                          |
|  - Urdu / Sindhi Nastaliq RTL auto-detection                            |
|  - Local draft saving in localStorage                                   |
|                                                                         |
|  [Serverless Python API (/api)]                                         |
|  - FastAPI (Python 3.12 serverless runtime)                             |
|  - Bilingual PDF generation (FPDF2 + uharfbuzz text shaping)            |
|  - Google Sheets API integration with retry & optimistic locking        |
+-------------------------------------------------------------------------+
```
