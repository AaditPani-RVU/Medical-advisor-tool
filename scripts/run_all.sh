#!/bin/bash
# ============================================================
# Verified Health Content — Run All Setup Steps
# ============================================================
# Usage: bash scripts/run_all.sh

set -e

echo "============================================"
echo " Verified Health Content — Setup"
echo "============================================"

# 1. Install dependencies
echo ""
echo ">>> Installing dependencies..."
pip install -r requirements.txt

# 2. Copy .env if not exists
if [ ! -f .env ]; then
    echo ""
    echo ">>> Creating .env from .env.example..."
    cp .env.example .env
fi

# 3. Initialize database
echo ""
echo ">>> Initializing database..."
python scripts/init_db.py

# 4. Run ingestion (will warn if Ollama is not running)
echo ""
echo ">>> Running content ingestion..."
python -m backend.ingest.ingest_runner

# 5. Start services
echo ""
echo "============================================"
echo " Setup complete! Start the services:"
echo "============================================"
echo ""
echo "  Terminal 1 (API):"
echo "    uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "  Terminal 2 (UI):"
echo "    streamlit run ui/streamlit_app.py"
echo ""
echo "  Optional — Ollama (for LLM summarization):"
echo "    ollama pull phi3:mini"
echo "    ollama serve"
echo ""
