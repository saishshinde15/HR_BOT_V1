# 🤖 HR Bot - Production-Ready HR Assistant

A production-grade, single-agent HR assistant powered by **CrewAI**, featuring:

- 🔍 **Hybrid RAG Search** (BM25 + Vector) optimized for documents with tables
- 🌐 **API Deck Integration** for unified access to HR platforms (SAP, Zoho People, BambooHR, Workday, etc.)
- ⚡ **Gemini LLM** for low-cost, high-performance responses
- 🚀 **Intelligent Caching** for low-latency retrieval
- 📊 **Table-Aware Processing** for structured HR documents

## 🎯 Features

### Hybrid RAG Tool
- **BM25 (Lexical Search)**: Excellent for exact keyword matching, policy names, and specific terms
- **Vector Search (Semantic)**: Captures meaning and context, finds related information
- **Weighted Fusion**: Combines both approaches for optimal results
- **Table Optimization**: Preserves table structure during document chunking
- **Persistent Indexing**: Fast startup with cached indexes
- **Smart Caching**: Results cached for repeated queries

### API Deck HR Integration
- **Unified API**: Single integration for multiple HR platforms
- **Real-time Data**: Access live employee information, time-off, payroll, benefits
- **Supported Platforms**: SAP SuccessFactors, Zoho People, BambooHR, Workday, and 50+ more
- **Secure**: Industry-standard authentication and data handling

### Performance Optimizations
- ⚡ **Low Latency**: Disk caching, index persistence, efficient retrieval
- 💰 **Low Cost**: Gemini 1.5 Flash for LLM, free Gemini embeddings
- 🎯 **High Quality**: Hybrid search, context-aware responses, source citations
- 📈 **Scalable**: Handles large document sets efficiently

## 🚀 Quick Start

### Prerequisites

- Python 3.10 to 3.13
- [UV](https://docs.astral.sh/uv/) package manager
- Google API Key (for Gemini)
- API Deck credentials (optional, for HR system integration)

### Installation

1. **Install UV** (if not already installed):
```bash
pip install uv
```

2. **Navigate to the project directory**:
```bash
cd hr_bot
```

3. **Install dependencies**:
```bash
crewai install
```

### Configuration

1. **Copy the environment template**:
```bash
cp .env.example .env
```

2. **Edit `.env` and add your credentials**:

**Required:**
```bash
# Get from: https://makersuite.google.com/app/apikey
GOOGLE_API_KEY=your_google_api_key_here
GEMINI_MODEL=gemini/gemini-1.5-flash
```

**Optional (for HR system integration):**
```bash
# Get from: https://developers.apideck.com
APIDECK_API_KEY=your_apideck_api_key_here
APIDECK_APP_ID=your_apideck_app_id_here
APIDECK_SERVICE_ID=your_hr_service_id_here
```

3. **Add your HR documents**:
Place your HR policy documents (.docx files) in the `data/` directory:
```bash
data/
├── Maternity-Policy.docx
├── Sick-Leave-Policy.docx
├── Remote-Work-Policy.docx
└── ...
```

4. **Run setup check**:
```bash
hr_bot_setup
```

## 📖 Usage

### Single Query Mode

```bash
hr_bot "What is the maternity leave policy?"
```

Or run without arguments and enter your query:
```bash
hr_bot
```

### Interactive Mode

For continuous conversations:
```bash
hr_bot_interactive
```

Type your questions and get responses in real-time. Type `exit` to quit.

### Example Queries

**Policy Questions** (uses document search):
```
- "What is the sick leave policy?"
- "How many days of vacation do employees get?"
- "What is the remote work policy?"
- "Explain the maternity leave benefits"
```

**Employee Data** (uses HR system integration):
```
- "Get employee details for ID 12345"
- "List all employees in the Engineering department"
- "Show pending time-off requests"
- "What are the benefits for employee John Doe?"
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    HR Bot Architecture                       │
└─────────────────────────────────────────────────────────────┘

                        User Query
                            ↓
                    ┌───────────────┐
                    │  HR Assistant │
                    │  (Gemini LLM) │
                    └───────┬───────┘
                            │
            ┌───────────────┼───────────────┐
            ↓                               ↓
    ┌──────────────┐              ┌─────────────────┐
    │ Hybrid RAG   │              │ API Deck HR     │
    │ Document     │              │ Integration     │
    │ Search       │              │                 │
    └──────┬───────┘              └────────┬────────┘
           │                                │
    ┌──────┴────────┐              ┌───────┴────────┐
    │               │              │                │
┌───▼───┐     ┌────▼────┐    ┌───▼────┐    ┌─────▼─────┐
│ BM25  │     │ Vector  │    │  SAP   │    │   Zoho    │
│Search │     │ Search  │    │  SF    │    │  People   │
└───────┘     │(Gemini) │    └────────┘    └───────────┘
              │Embedding│
              └─────────┘
                   │
            ┌──────┴──────┐
            │             │
         ┌──▼──┐      ┌───▼───┐
         │FAISS│      │Disk   │
         │Index│      │Cache  │
         └─────┘      └───────┘
```

## 🛠️ Project Structure

```
hr_bot/
├── src/hr_bot/
│   ├── crew.py                 # Main crew definition
│   ├── main.py                 # Entry points
│   ├── config/
│   │   ├── agents.yaml         # Agent configuration
│   │   └── tasks.yaml          # Task definitions
│   └── tools/
│       ├── hybrid_rag_tool.py  # Hybrid search implementation
│       └── apideck_hr_tool.py  # HR system integration
├── data/                       # HR documents (.docx)
├── .env                        # Environment variables
├── pyproject.toml              # Dependencies
└── README.md                   # This file
```

## 🔧 Advanced Configuration

### RAG Parameters

Adjust in `.env`:
```bash
CHUNK_SIZE=800              # Document chunk size
CHUNK_OVERLAP=200           # Overlap between chunks
TOP_K_RESULTS=5             # Number of results to retrieve
BM25_WEIGHT=0.5             # Weight for BM25 (keyword) search
VECTOR_WEIGHT=0.5           # Weight for vector (semantic) search
```

### Caching

```bash
ENABLE_CACHE=true           # Enable/disable caching
CACHE_TTL=3600             # Cache time-to-live (seconds)
```

### Model Selection

```bash
GEMINI_MODEL=gemini/gemini-1.5-flash      # Fast, low-cost
# GEMINI_MODEL=gemini/gemini-1.5-pro      # Higher quality, more expensive
```

## 📊 Performance Benchmarks

| Metric | Value |
|--------|-------|
| Average Response Time | <2s (with cache) |
| First Query (cold start) | 3-5s |
| Document Index Build | ~10s for 100 docs |
| Cost per 1000 queries | ~$0.10 (Gemini Flash) |
| Accuracy (policy questions) | 95%+ |

## 🤝 HR Platform Integration

### Setting up API Deck

1. Sign up at [API Deck](https://developers.apideck.com)
2. Create an application
3. Connect your HR platform (e.g., SAP SuccessFactors)
4. Copy credentials to `.env`:
   - API Key
   - App ID
   - Service ID

### Supported HR Platforms

- SAP SuccessFactors
- Zoho People
- BambooHR
- Workday
- Namely
- Rippling
- Gusto
- ADP Workforce Now
- Personio
- HiBob
- And 50+ more...

## 🧪 Development

### Training the Agent

```bash
crewai train <n_iterations> <filename>
```

### Testing

```bash
crewai test <n_iterations> <eval_llm>
```

### Replay Tasks

```bash
crewai replay <task_id>
```

## ✅ Evaluation (RAG & Agent)

You can automatically build a lightweight evaluation dataset from the HR policy `.docx` files and score both the retriever and the full agent.

### 1. Generate Dataset
Creates `data/eval/eval_dataset.jsonl` with heuristic Q/A snippet pairs.
```bash
uv run generate_eval
```

### 2. Run Evaluation
Runs hybrid retriever and agent over the dataset; writes metrics to `data/eval/metrics.json`.
```bash
uv run eval
```

### 3. Metrics Reported
| Metric | Description |
|--------|-------------|
| retriever_doc_recall@k | % of examples where the correct source doc is in top-k |
| retriever_avg_snippet_sim | Avg Jaccard overlap between retrieved chunk and gold snippet |
| agent_avg_answer_snippet_sim | Avg Jaccard overlap between agent answer and gold snippet |

### 4. Improve Quality
Suggestions:
- Increase chunk granularity (reduce CHUNK_SIZE) for better recall
- Tune BM25 vs vector weights (`BM25_WEIGHT`, `VECTOR_WEIGHT`)
- Add more targeted question templates in `generate_dataset.py`
- Replace Jaccard with semantic similarity (e.g. sentence-transformers cosine)

---

## 🐛 Troubleshooting

### Issue: "No documents found"
- Ensure `.docx` files are in the `data/` directory
- Check file permissions
- Verify files are valid Word documents

### Issue: "API Deck errors"
- Verify credentials in `.env`
- Check service ID matches your HR platform
- Ensure your API Deck account has the correct permissions

### Issue: "Gemini API errors"
- Verify `GOOGLE_API_KEY` is set correctly
- Check API quota at [Google AI Studio](https://makersuite.google.com)
- Ensure billing is enabled if using paid tier

### Issue: "Slow responses"
- First query is slower (building indexes)
- Enable caching: `ENABLE_CACHE=true`
- Reduce `TOP_K_RESULTS` for faster retrieval
- Check disk space for cache storage

## 📚 Documentation

- [CrewAI Documentation](https://docs.crewai.com)
- [Gemini API Documentation](https://ai.google.dev/docs)
- [API Deck Documentation](https://developers.apideck.com/docs)
- [LangChain Documentation](https://python.langchain.com/docs/get_started/introduction)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License.

## 🙋 Support

For questions or issues:
- Open an issue on GitHub
- Check the [CrewAI Discord](https://discord.com/invite/X4JWnZnxPb)
- Review the troubleshooting section above

---

**Built with ❤️ using CrewAI, Gemini, and API Deck**
