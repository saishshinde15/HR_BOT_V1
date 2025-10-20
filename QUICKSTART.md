# 🚀 Quick Start Guide

## Prerequisites Check

Before starting, ensure you have:
- ✅ Python 3.10 - 3.13 installed
- ✅ UV package manager installed
- ✅ Google API key for Gemini
- ✅ HR documents in .docx format

## Step-by-Step Setup

### 1. Install Dependencies

```bash
# Navigate to the project directory
cd hr_bot

# Install all dependencies
crewai install

# This will install:
# - CrewAI framework
# - Langchain & Google AI integration
# - FAISS vector database
# - BM25 search
# - Document processing libraries
# - Caching and utilities
```

### 2. Configure Environment

```bash
# Copy the environment template
cp .env.example .env

# Edit .env file and add your credentials
nano .env  # or use any text editor
```

**Minimum Required Configuration:**
```bash
GOOGLE_API_KEY=your_actual_google_api_key_here
```

**Get Google API Key:**
1. Visit: https://makersuite.google.com/app/apikey
2. Click "Create API Key"
3. Copy and paste into `.env`

**Optional - API Deck (for HR system integration):**
1. Visit: https://developers.apideck.com
2. Sign up and create an application
3. Connect your HR platform
4. Add credentials to `.env`

### 3. Add HR Documents

```bash
# Add your HR policy documents to the data folder
# Supported format: .docx (Microsoft Word)

data/
├── Maternity-Policy.docx
├── Sick-Leave-Policy.docx
├── Remote-Work-Policy.docx
├── Benefits-Guide.docx
└── Employee-Handbook.docx
```

### 4. Run Setup Verification

```bash
hr_bot_setup
```

This will:
- ✅ Check for data directory
- ✅ Count documents
- ✅ Verify environment variables
- ✅ Display configuration status

### 5. First Run (Index Building)

```bash
# First time - will build search indexes (~10 seconds for 100 docs)
hr_bot "What is the sick leave policy?"
```

**What happens on first run:**
1. 📄 Loads all .docx files from data/
2. ✂️ Chunks documents intelligently (preserves tables)
3. 🔢 Creates BM25 index (keyword search)
4. 🧮 Creates vector embeddings (semantic search)
5. 💾 Saves indexes to disk (.rag_index/)
6. 🚀 Answers your query

**Subsequent runs:**
- ⚡ Loads cached indexes (~1 second)
- 🏃 Much faster responses

## 📖 Usage Examples

### Single Query Mode

```bash
# Ask a question directly
hr_bot "What is the maternity leave policy?"

# Or run without arguments
hr_bot
# Then type your question when prompted
```

### Interactive Mode (Recommended for multiple queries)

```bash
hr_bot_interactive
```

**Example session:**
```
💬 Your query: What is the sick leave policy?
🔍 Processing...

📝 Response:
According to the Sickness and Absence Policy document:

1. **Sick Leave Allowance**: Employees are entitled to [X] days 
   of paid sick leave per year.

2. **Notification Process**: 
   - Notify your manager as soon as possible
   - Provide medical certificate for absences over 3 days

3. **Return to Work**: A return-to-work meeting will be conducted
   with your manager.

Source: Sickness-And-Absence-Policy.docx

💬 Your query: How do I request time off?
🔍 Processing...

📝 Response:
[Response with time-off policy details...]
```

### Example Queries

**📚 Policy Questions (uses document search):**
```bash
# Leave policies
hr_bot "How many vacation days do I get?"
hr_bot "What is the maternity leave policy?"
hr_bot "Explain the sick leave process"

# Work arrangements
hr_bot "What is the remote work policy?"
hr_bot "Can I work from home?"
hr_bot "What are the flexible working options?"

# Benefits
hr_bot "What benefits does the company offer?"
hr_bot "Explain the health insurance coverage"

# Procedures
hr_bot "How do I submit a resignation?"
hr_bot "What is the promotion process?"
```

**🌐 HR System Queries (requires API Deck setup):**
```bash
# Employee information
hr_bot "Get details for employee ID 12345"
hr_bot "List all employees in Engineering department"

# Time off
hr_bot "Show pending time-off requests"
hr_bot "Get my leave balance"

# Departments
hr_bot "Get information about the Marketing department"
```

## 🎯 Best Practices

### For Best Results

1. **Be Specific**: 
   - ❌ "Tell me about leave"
   - ✅ "What is the maternity leave policy?"

2. **Use Full Questions**:
   - ❌ "vacation days?"
   - ✅ "How many vacation days do employees get?"

3. **Reference Context**:
   - ✅ "What documents do I need to submit for sick leave?"
   - ✅ "Explain the process for requesting flexible working"

### Document Organization

**Good document structure:**
- Clear headings and sections
- Tables for structured data
- Consistent formatting
- Policy names in document titles

**Tips:**
- Keep related policies in separate files
- Use descriptive filenames
- Update documents regularly
- Remove draft/temp files from data/

## 🔧 Configuration Tuning

### For Better Accuracy

If getting irrelevant results, adjust in `.env`:
```bash
TOP_K_RESULTS=10        # Get more results
BM25_WEIGHT=0.6         # Favor keyword matching
VECTOR_WEIGHT=0.4       # Reduce semantic search weight
```

### For Better Semantic Understanding

If missing context/related info:
```bash
TOP_K_RESULTS=5
BM25_WEIGHT=0.3         # Reduce keyword matching
VECTOR_WEIGHT=0.7       # Favor semantic search
```

### For Faster Responses

```bash
TOP_K_RESULTS=3         # Fewer results
ENABLE_CACHE=true       # Always keep this enabled
```

### For Larger Documents

```bash
CHUNK_SIZE=1200         # Bigger chunks
CHUNK_OVERLAP=300       # More overlap for context
```

## 🐛 Common Issues & Solutions

### "No documents found in data"

**Solution:**
```bash
# Check data directory exists
ls -la data/

# Add documents
cp /path/to/your/policies/*.docx data/

# Verify
ls -la data/
```

### "Google API Key not found"

**Solution:**
```bash
# Check .env file
cat .env | grep GOOGLE_API_KEY

# If empty, add your key
echo "GOOGLE_API_KEY=your_key_here" >> .env
```

### "Import errors" or "Module not found"

**Solution:**
```bash
# Reinstall dependencies
crewai install

# Or manually
pip install -e .
```

### Indexes not updating after adding new documents

**Solution:**
```bash
# Remove old indexes
rm -rf .rag_index/

# Next run will rebuild
hr_bot "test query"
```

### Out of memory errors

**Solution:**
```bash
# Reduce chunk size
# In .env:
CHUNK_SIZE=600
TOP_K_RESULTS=3
```

## 📊 Performance Tips

### First-Time Optimization

1. **Start with fewer documents** (~10-20 for testing)
2. **Verify results quality** before adding more
3. **Build index once**, benefits persist
4. **Keep cache enabled** for fast subsequent queries

### Production Deployment

1. **Pre-build indexes**:
   ```bash
   hr_bot "test" > /dev/null
   ```
   
2. **Use SSD storage** for cache/indexes

3. **Set appropriate cache TTL**:
   ```bash
   CACHE_TTL=7200  # 2 hours for dynamic data
   CACHE_TTL=86400 # 24 hours for static policies
   ```

4. **Monitor disk space**:
   ```bash
   du -sh .rag_index .rag_cache .apideck_cache
   ```

## 🎓 Next Steps

1. ✅ Complete setup
2. ✅ Run `hr_bot_setup` to verify
3. ✅ Try example queries
4. ✅ Add your HR documents
5. ✅ Configure API Deck (optional)
6. ✅ Tune parameters for your use case
7. ✅ Deploy to production

## 📚 Additional Resources

- [CrewAI Documentation](https://docs.crewai.com)
- [Gemini API Guide](https://ai.google.dev/docs)
- [API Deck Integration](https://developers.apideck.com/docs)

## 💬 Need Help?

- Check the main README.md
- Review troubleshooting section
- Open an issue on GitHub
- Join CrewAI Discord community

---

**Happy HR Bot-ing! 🤖🎉**
