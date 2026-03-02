# 🏗️ Agentic AI Construction POC

**Nikitha Build Tech Pvt Ltd** — AI-Powered Project Management Dashboard

A Streamlit application that connects to the live PostgreSQL database and provides AI-driven project analytics, risk prediction, and intelligent recommendations.

## Features

| Feature | Description |
|---------|-------------|
| **KPI Dashboard** | Real-time budget, timeline, manpower, and material metrics |
| **AI Risk Monitor** | Multi-factor risk scoring with gauge visualization |
| **Decision Agent** | Automated, prioritized recommendations |
| **Delay Prediction** | ML-based schedule delay forecasting |
| **Cost & Manpower Charts** | Plotly interactive visualizations |
| **AI Chat** | Natural language Q&A powered by project data (TF-IDF RAG) |
| **PDF Reports** | One-click downloadable project reports |
| **Email Alerts** | Real SMTP email notifications |
| **WhatsApp Alerts** | One-click WhatsApp message links |
| **Approval Workflow** | AUTO or MANUAL alert triggering |

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure credentials (already set up)
# Edit .streamlit/secrets.toml if needed

# 3. Run the app
streamlit run streamlit_app.py
```

## Architecture

```
streamlit_app.py        ← Main dashboard (entry point)
├── db.py               ← PostgreSQL connection layer
├── queries.py          ← All SQL queries (READ-ONLY)
├── agents/
│   ├── progress_agent  ← Timeline & cost analysis
│   ├── risk_agent      ← Multi-signal risk assessment
│   └── decision_agent  ← Actionable recommendations
├── ml/
│   ├── delay_model     ← Schedule delay prediction
│   └── risk_model      ← Risk classification
├── rag/
│   └── retriever       ← AI Chat (TF-IDF based)
└── services/
    ├── alert_store     ← In-memory alert log
    ├── notification    ← Email + WhatsApp
    └── report_service  ← PDF generation
```

## Database

Connects to the **Nikitha Build Tech PostgreSQL** database (AWS RDS). All queries are **read-only** — no modifications are made to production data.

## Deployment (Streamlit Cloud)

1. Push to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect repo → select `streamlit_app.py` → Deploy
4. Add secrets in Streamlit Cloud settings
