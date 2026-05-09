# 🔍 CodeLens

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](#)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![MiMo v2.5](https://img.shields.io/badge/MiMo-v2.5-orange.svg)](https://mimo.xiaomi.com)
[![API](https://img.shields.io/badge/API-REST-purple.svg)](#-api-documentation)

> **AI-powered code review & vulnerability scanner built on Xiaomi MiMo v2.5 reasoning engine.**

CodeLens analyzes source code for bugs, security vulnerabilities (OWASP Top 10), style issues, and performance problems using a multi-pass AI analysis pipeline. Drop in a file or integrate via API — get actionable findings with severity scores in seconds.

**[Live Demo](https://codelens-demo.trycloudflare.com)** · **[API Docs](docs/api.md)** · **[Report Bug](../../issues)** · **[Request Feature](../../issues)**

---

## 📸 Screenshots

| Dashboard | Code Review | Findings Detail |
|-----------|-------------|-----------------|
| ![Dashboard](docs/screenshots/dashboard.png) | ![Review](docs/screenshots/review.png) | ![Findings](docs/screenshots/findings.png) |

> Screenshots generated from live instance. See `docs/screenshots/` for full resolution.

---

## 🏗️ Architecture

```
                         ┌──────────────────────────────────┐
                         │          CodeLens Server          │
                         │           (Flask + Gunicorn)      │
                         └──────────┬───────────────────────┘
                                    │
           ┌────────────────────────┼────────────────────────┐
           │                        │                        │
    ┌──────▼──────┐         ┌──────▼──────┐         ┌──────▼──────┐
    │   Web UI    │         │  REST API   │         │  CI/CD Hook │
    │  (Jinja2)   │         │  (JSON)     │         │  (GitHub)   │
    └──────┬──────┘         └──────┬──────┘         └──────┬──────┘
           │                       │                       │
           └───────────────────────┼───────────────────────┘
                                   │
                            ┌──────▼──────┐
                            │  Analyzer   │
                            │  (Engine)   │
                            └──────┬──────┘
                                   │
           ┌───────────────────────┼───────────────────────┐
           │                       │                       │
    ┌──────▼──────┐         ┌──────▼──────┐         ┌──────▼──────┐
    │   Pre-      │         │   MiMo API  │         │  Severity   │
    │   process   │────────►│  (Multi-    │────────►│  Scoring &  │
    │   & Chunk   │         │   pass)     │         │  Dedupe     │
    └─────────────┘         └─────────────┘         └──────┬──────┘
                                                           │
                                                    ┌──────▼──────┐
                                                    │   SQLite    │
                                                    │   (History) │
                                                    └─────────────┘
```

### Analysis Pipeline

Each code review runs through 4 specialized analysis passes:

1. **Bug Detection** — Logic errors, null dereferences, off-by-one, race conditions, unhandled exceptions
2. **Security Scan** — SQL injection (CWE-89), XSS (CWE-79), path traversal (CWE-22), hardcoded secrets (CWE-798)
3. **Style Review** — Naming conventions, dead code, complexity metrics, missing documentation
4. **Performance Check** — N+1 queries, O(n²) loops, missing caching, unnecessary allocations

Results are deduplicated, severity-scored, and stored with line references for actionable feedback.

---

## ✨ Features

- 🔍 **Multi-Pass Analysis** — 4 specialized agents analyze code from different angles
- 🛡️ **OWASP & CWE Mapping** — Security findings mapped to standard vulnerability identifiers
- 📊 **Severity Scoring** — Critical / High / Medium / Low with color-coded dashboard
- 🔗 **CI/CD Integration** — REST API for automated review in GitHub Actions, GitLab CI, Jenkins
- 📈 **Token Usage Tracking** — Per-review and daily aggregate token consumption monitoring
- 🔄 **Deduplication** — Same code hash returns cached results (no wasted tokens)
- 🌐 **Multi-Language** — Python, JavaScript, TypeScript, Go, Rust, Java, C++, Ruby, PHP
- 🐳 **Docker Ready** — Single command deployment with Docker Compose

---

## 🔥 Token Economics

| Scenario | Code Size | Tokens/Review | Reviews/Day | Daily Tokens |
|----------|-----------|---------------|-------------|--------------|
| Solo developer | ~200 LOC | 3K–8K | 20–40 | ~200K |
| Small team (5 devs) | ~500 LOC avg | 5K–15K | 100–200 | ~1.5M |
| CI/CD pipeline (per push) | ~300 LOC diff | 4K–10K | 50–100 | ~600K |
| Enterprise (20+ devs) | varies | 5K–15K | 500+ | ~5M |
| Security audit (full repo) | 10K+ LOC | 30K–50K | 5–10 | ~400K |

**Budget management:** Set `DAILY_TOKEN_BUDGET` to cap consumption. Reviews are rejected when budget is exhausted.

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- MiMo API key ([get one here](https://mimo.xiaomi.com))

### Installation

```bash
# Clone
git clone https://github.com/bandarahalih-gif/codelens.git
cd codelens

# Virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\\Scripts\\activate

# Dependencies
pip install -r requirements.txt

# Configuration
cp .env.example .env
# Edit .env — set MIMO_API_KEY at minimum

# Run
python -m src.app
```

Open [http://localhost:5000](http://localhost:5000) in your browser.

### Docker

```bash
docker compose up --build
```

### Running Tests

```bash
pytest tests/ -v --cov=src --cov-report=term-missing
```

---

## 📖 API Documentation

### Create Review

```bash
curl -X POST http://localhost:5000/api/v1/review \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def login(user, pwd):\n    query = f\"SELECT * FROM users WHERE name='{user}'\"\n    return db.execute(query)",
    "filename": "auth.py",
    "language": "python"
  }'
```

**Response:**
```json
{
  "id": 1,
  "filename": "auth.py",
  "language": "python",
  "status": "complete",
  "total_findings": 1,
  "critical": 1,
  "high": 0,
  "medium": 0,
  "low": 0,
  "tokens_used": 4200,
  "analysis_time_ms": 890
}
```

### List Reviews

```bash
curl http://localhost:5000/api/v1/reviews?limit=10
```

### Get Review Details

```bash
curl http://localhost:5000/api/v1/reviews/1
```

### Usage Statistics

```bash
curl http://localhost:5000/api/v1/stats
```

Full API documentation: [`docs/api.md`](docs/api.md)

---

## ⚙️ Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `MIMO_API_KEY` | Your MiMo API key | — (required) |
| `MIMO_BASE_URL` | MiMo API endpoint | `https://api.mimo.xiaomi.com/v1` |
| `MIMO_MODEL` | Model identifier | `MiMo-v2.5` |
| `DATABASE_URL` | SQLite database path | `sqlite:///codelens.db` |
| `DAILY_TOKEN_BUDGET` | Max tokens/day | `5000000` |
| `REVIEW_TOKEN_LIMIT` | Max tokens/review | `50000` |
| `SECRET_KEY` | Flask session secret | — (required) |
| `PORT` | Server port | `5000` |

---

## 🤝 Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [Xiaomi MiMo](https://mimo.xiaomi.com) for the reasoning engine
- [Flask](https://flask.palletsprojects.com) for the web framework
- [OpenAI Python SDK](https://github.com/openai/openai) for API compatibility
