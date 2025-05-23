FACT – Fast‑Access Cached Tools
================================
FACT is a lean retrieval pattern that skips vector search. We cache every static token inside Claude Sonnet‑4 and fetch live facts only through authenticated tools hosted on Arcade.dev. The result is deterministic answers, fresh data, and sub‑100 ms latency.

Why FACT?
---------
* **Speed** – Sonnet reuses its cached key‑value states so only new tokens run. Tool calls stay on LAN (<10 ms).
* **Determinism** – Structured tools return exact rows, not cosine‑similar text chunks.
* **Simplicity** – No embeddings, no index refresh, no third‑party search infra.
* **Cost** – Cache hits cut Anthropic billing by up to 90 percent; you pay only for incremental tokens.

Benchmarks
----------
| Scenario                     | Latency | Token cost |
|------------------------------|---------|------------|
| Pure RAG (PGVector + rerank) | 320 ms  | 100 %      |
| FACT cache miss              | 140 ms  | 35 %       |
| FACT cache hit               | **48 ms** | **10 %**  |
*(Local tests on M2 laptop, Sonnet‑4 200‑token responses.)*

Architecture
------------
1. **Cache Prefix** – A ≥500‑token system block plus immutable docs sent with `cache_control:{mode:"write",prefix:"fact_v1"}`.
2. **User Query** – Prompts can include natural placeholders like “{lookup sql}”.
3. **Tool Call** – Sonnet emits a structured call, driver forwards it to Arcade.
4. **Tool Result** – JSON result is appended as a `tool` message; Sonnet completes the answer.

Quick Start
-----------
```bash
# clone & enter
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill API keys
# launch Arcade gateway
docker compose -f gateway/docker-compose.yml up -d
# seed sample DB
awk -f - < db/seed.sql | sqlite3 finance.db  # or sqlite3 finance.db < db/seed.sql
# register tools
python tools/sql_query.py --register
# run interactive CLI\python driver.py
```
Ask: `What was Q1‑2025 net revenue?`

Extending FACT
--------------
* **Add tools** – Drop a new `@Tool` function in `tools/`, run with `--register`.
* **Scale** – Deploy Arcade behind TLS and point multiple driver pods to it; cache prefixes are portable because they only store token hashes.
* **Fallback search** – Bolt on a traditional RAG path for unstructured domains; let a policy router pick RAG vs FACT per request.

Security Notes
--------------
Arcade supports OAuth scopes, rate limits, and audit logs. Always sandbox dangerous actions (shell, DDL) behind explicit scopes and review Sonnet’s tool call args.

License
-------
MIT, see LICENSE file.
