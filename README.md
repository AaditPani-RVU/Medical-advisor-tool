# Verified Health Content Recommender

> **Educational content only. Not medical advice. If worried, seek professional care.**

A baseline POC system that provides **verified health videos/articles** from trusted sources, personalized for family groups, with rule-based seek-care guidance and specialist navigation — **without providing diagnosis or medical advice**.

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Install & Run Ollama (for content summarization)
```bash
# Install Ollama from https://ollama.com
ollama pull phi3:mini
ollama serve  # keep running in background
```

### 3. Set Up Environment
```bash
copy .env.example .env
# Edit .env if needed (defaults work for local dev)
```

### 4. Initialize Database
```bash
python scripts/init_db.py
```

### 5. Run Content Ingestion (optional — fetches from trusted sources)
```bash
python -m backend.ingest.ingest_runner
```

### 6. Start the API Server
```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 7. Start the Streamlit UI
```bash
streamlit run ui/streamlit_app.py
```

## Architecture

| Layer | Tech | Purpose |
|-------|------|---------|
| **UI** | Streamlit | Demo interface with feed, family, triage pages |
| **API** | FastAPI | REST endpoints for content, family, triage |
| **DB** | SQLite | Stores content items, family groups, saved items |
| **LLM** | Ollama (phi3:mini) | Neutral summarization & topic tagging ONLY |
| **Ingestion** | Python scripts | RSS, web, YouTube fetchers (allowlisted sources only) |

## Safety Guardrails

- ✅ Content from **allowlisted trusted sources only** (NHS, CDC, WHO, NIH, Mayo Clinic, etc.)
- ✅ LLM used **only for summarization** — never answers medical questions
- ✅ All LLM output filtered through **banned-phrase detector**
- ✅ Triage is **100% rule-based** — no LLM involvement in urgency decisions
- ✅ Specialist suggestions are **navigation only** ("commonly handled by...")
- ✅ Disclaimer on every page

## Adding Sources

Edit `configs/sources_allowlist.yaml` to add:
- **Trusted domains**: Add to `trusted_domains` list
- **RSS feeds**: Add to `trusted_rss` with URL, name, and source_tier
- **YouTube channels**: Add to `trusted_youtube_channels` with channel_id, name, source_tier

Then re-run ingestion: `python -m backend.ingest.ingest_runner`

## Project Structure

```
├── configs/           # YAML configs, prompts, safety policy
├── backend/
│   ├── main.py        # FastAPI app
│   ├── api/           # Route handlers
│   ├── core/          # DB, models, safety, ranking
│   ├── ingest/        # Content fetchers
│   └── llm/           # Ollama client, summarizer, tagger
├── ui/
│   ├── streamlit_app.py
│   └── components/    # UI components
├── scripts/           # DB init, run scripts
└── data/              # SQLite DB, cache
```
