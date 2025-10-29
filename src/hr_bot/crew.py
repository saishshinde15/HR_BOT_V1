"""
Production-Ready HR Bot Crew
Single agent system with Hybrid RAG - Empathetic and Human-like
"""

from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.memory import LongTermMemory
from crewai.memory.long_term.long_term_memory_item import LongTermMemoryItem
from crewai.memory.storage.ltm_sqlite_storage import LTMSQLiteStorage
from typing import List, Optional
import hashlib
import json
import os
import re
import sqlite3
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from hr_bot.tools.hybrid_rag_tool import HybridRAGTool
from hr_bot.tools.master_actions_tool import MasterActionsTool
from hr_bot.utils.cache import ResponseCache


def remove_document_evidence_section(text: str) -> str:
    """Strip any trailing 'Document Evidence' sections from model output."""
    lines = text.splitlines()
    cleaned_lines = []
    skipping = False

    for line in lines:
        normalized = line.strip().lower()
        if skipping:
            if normalized.startswith("sources:"):
                cleaned_lines.append(line)
                skipping = False
            continue

        if normalized.startswith("document evidence"):
            skipping = True
            continue

        cleaned_lines.append(line)

    return "\n".join(cleaned_lines).rstrip()


def validate_response_against_sources(response_text: str, sources: List[str], retrieved_content: str, original_query: str) -> dict:
    """
    Validate if response is grounded in actual retrieved documents.
    Returns dict with validation status and corrected response if needed.
    """
    # Check if response is actually using tool results
    if not sources or len(sources) == 0:
        # No sources means no search was done - potential hallucination
        if any(keyword in response_text.lower() for keyword in [
            "policy", "according to", "procedure", "entitled", "must", "should",
            "company requires", "your manager", "hr department", "form", "days"
        ]):
            return {
                "is_valid": False,
                "reason": "policy_answer_without_search",
                "corrected_response": (
                    "I apologize, but I couldn't find specific information about this in our HR policies. "
                    "This topic may not be covered in our current documentation. "
                    "I recommend checking with your HR department directly for guidance on this matter.\n\n"
                    "Is there anything else I can help you with?"
                )
            }
    
    # CRITICAL: Check if retrieved documents are actually relevant to the query
    # Extract key topics from query
    query_lower = original_query.lower()
    query_keywords = set(word for word in query_lower.split() if len(word) > 3 and word not in {
        "what", "when", "where", "which", "this", "that", "there", "with", "from", "have"
    })
    
    # Check if retrieved content has any relevance to query
    if retrieved_content:
        content_lower = retrieved_content.lower()
        # Count keyword matches
        matches = sum(1 for keyword in query_keywords if keyword in content_lower)
        relevance_ratio = matches / max(len(query_keywords), 1)
        
        # If less than 20% of keywords found in documents, they're irrelevant
        if relevance_ratio < 0.2:
            return {
                "is_valid": False,
                "reason": "irrelevant_documents",
                "corrected_response": (
                    "I searched our HR documentation but couldn't find relevant policies that address your specific question. "
                    "This topic doesn't appear to be covered in our current HR policies. "
                    "I recommend contacting your HR department directly for guidance on this matter.\n\n"
                    "Is there anything else I can help you with?"
                )
            }
    
    # Check for fabricated procedures not in documents
    if retrieved_content:
        # Common hallucination phrases that indicate fabricated procedures
        fabrication_indicators = [
            ("review the company", retrieved_content),
            ("consult with the finance", retrieved_content),
            ("submit a formal request", retrieved_content),
            ("contact your manager", retrieved_content),
            ("approval from relevant authorities", retrieved_content),
            ("follow the company's procurement", retrieved_content),
        ]
        
        for phrase, document_text in fabrication_indicators:
            if phrase in response_text.lower() and phrase not in document_text.lower():
                # Bot is making up procedures
                return {
                    "is_valid": False,
                    "reason": "fabricated_procedures",
                    "corrected_response": (
                        "I searched our HR policies but couldn't find information that directly addresses your question. "
                        "This specific topic doesn't appear to be covered in our current HR documentation. "
                        "Please contact your HR department for guidance on this matter.\n\n"
                        "Is there anything else I can help you with?"
                    )
                }
    
    # Check for common hallucination patterns
    hallucination_patterns = [
        r"contact.*hr.*at.*@",  # Email addresses
        r"call.*\d{3}[-.]?\d{3}[-.]?\d{4}",  # Phone numbers
        r"form.*\d+",  # Form numbers
        r"\[insert\s+\w+\]",  # Placeholder text
    ]
    
    import re
    for pattern in hallucination_patterns:
        if re.search(pattern, response_text, re.IGNORECASE):
            # Check if this pattern exists in retrieved content
            if retrieved_content and not re.search(pattern, retrieved_content, re.IGNORECASE):
                return {
                    "is_valid": False,
                    "reason": "fabricated_details",
                    "corrected_response": (
                        "I found some information related to your question, but I don't have the complete "
                        "details in our HR documentation. Please verify specific contact information, forms, "
                        "or procedures directly with your HR department to ensure accuracy.\n\n"
                        "Is there anything else I can help clarify?"
                    )
                }
    
    return {"is_valid": True, "reason": "grounded_response"}


@CrewBase
class HrBot():
    """
    Production-ready HR Bot with empathetic, human-like responses:
    - Emotionally intelligent and empathetic communication
    - Amazon Bedrock (Amazon Nova Lite) LLM for natural, conversational responses
    - Detailed, accurate answers with proper source citation
    """

    agents: List[BaseAgent]
    tasks: List[Task]
    
    def __init__(self):
        super().__init__()
        
        # Initialize Amazon Bedrock LLM with Nova Pro
        # Set AWS credentials for Bedrock access
        aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
        aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        aws_region = os.getenv("AWS_REGION", "us-east-1")
        
        if aws_access_key:
            os.environ["AWS_ACCESS_KEY_ID"] = aws_access_key
        if aws_secret_key:
            os.environ["AWS_SECRET_ACCESS_KEY"] = aws_secret_key
        if aws_region:
            os.environ["AWS_REGION"] = aws_region
            os.environ["AWS_DEFAULT_REGION"] = aws_region
        
        llm_kwargs = {
            "model": os.getenv("BEDROCK_MODEL", "bedrock/amazon.nova-pro-v1:0"),
            "temperature": 0.7,
            "max_tokens": 4000,
        }
        if aws_region:
            llm_kwargs["aws_region_name"] = aws_region

        self.llm = LLM(**llm_kwargs)
        
        # Resolve project root once for downstream paths
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        
        # Initialize tools with absolute data directory so document loading works in UI/CLI contexts
        data_dir_path = os.path.join(project_root, "data")
        self.hybrid_rag_tool = HybridRAGTool(data_dir=data_dir_path)
        self.master_actions_tool = MasterActionsTool()  # Initialize Master Actions Tool

        # Persist AWS configuration for downstream components (e.g., memory embedder)
        self.aws_access_key = os.environ.get("AWS_ACCESS_KEY_ID")
        self.aws_secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
        self.aws_region = os.environ.get("AWS_REGION", aws_region)

        # Configure Bedrock embedder for crew-level memory (falls back to env defaults)
        embedder_region = os.getenv("BEDROCK_EMBED_REGION", self.aws_region)
        embedder_model = os.getenv("BEDROCK_EMBED_MODEL", "amazon.titan-embed-text-v1")
        embedder_config = {
            "provider": "amazon-bedrock",
            "config": {
                "aws_access_key_id": self.aws_access_key,
                "aws_secret_access_key": self.aws_secret_key,
                "region_name": embedder_region,
                "model": embedder_model,
            },
        }
        embedder_config["config"] = {
            key: value for key, value in embedder_config["config"].items() if value
        }
        self.embedder_config = embedder_config if embedder_config["config"] else None

        # Configure long-term memory storage
        self.memory_storage_dir = os.path.join(project_root, "storage")
        os.makedirs(self.memory_storage_dir, exist_ok=True)
        self.memory_db_path = os.path.join(self.memory_storage_dir, "long_term_memory.db")
        self.long_term_memory = LongTermMemory(
            storage=LTMSQLiteStorage(
                db_path=self.memory_db_path
            )
        )
        
        # Initialize semantic response caching with 60% similarity threshold
        cache_ttl_hours = int(os.getenv("CACHE_TTL_HOURS", "72"))
        cache_similarity = float(os.getenv("CACHE_SIMILARITY_THRESHOLD", "0.60"))  # 60% default
        self.response_cache = ResponseCache(
            cache_dir=os.path.join(self.memory_storage_dir, "response_cache"),
            ttl_hours=cache_ttl_hours,
            max_memory_items=200,
            similarity_threshold=cache_similarity
        )
        print(f"✅ Semantic caching enabled (TTL: {cache_ttl_hours}h, Similarity: {cache_similarity:.0%})")
    
    def query_with_cache(self, query: str, context: str = "") -> str:
        """
        Query the crew with aggressive caching for ultra-fast responses.
        
        Args:
            query: User's question
            context: Conversation context (optional)
        
        Returns:
            Formatted response string
        """
        # Check for inappropriate content FIRST (before cache/processing)
        safety_response = self._check_content_safety(query)
        if safety_response:
            print("🛡️ CONTENT SAFETY - Inappropriate content detected")
            return safety_response
        
        # Check cache first
        cached_response = self.response_cache.get(query, context)
        if cached_response:
            print("⚡ CACHE HIT - Returning instant response!")
            return cached_response
        
        small_talk_response = self._small_talk_response(query, context)
        if small_talk_response:
            print("💬 SMALL TALK - Skipping retrieval for conversational pleasantries.")
            self.response_cache.set(query, small_talk_response, context)
            return small_talk_response

        # Cache miss - execute crew with full memory
        print("🔄 CACHE MISS - Executing crew...")
        inputs = {"query": query, "context": context}
        result = self.crew().kickoff(inputs=inputs)
        
        # Format and cache response
        response_text = str(result.raw) if hasattr(result, 'raw') else str(result)
        formatted_response = remove_document_evidence_section(response_text)
        
        # Save to cache for future queries
        self.response_cache.set(query, formatted_response, context)
        
        return formatted_response
    
    def get_cache_stats(self) -> dict:
        """Get cache performance statistics"""
        return self.response_cache.get_stats()

    def _small_talk_response(self, query: str, context: str) -> Optional[str]:
        """Return tailored responses for greetings, farewells, and similar small-talk."""
        normalized = self._normalize_small_talk(query)
        if not normalized:
            return None

        greetings = {
            "hi",
            "hello",
            "hey",
            "hi there",
            "hello there",
            "hey there",
            "good morning",
            "good afternoon",
            "good evening",
            "greetings",
        }
        gratitude = {
            "thanks",
            "thank you",
            "thanks a lot",
            "thank you so much",
            "thanks so much",
            "cool thanks",
            "ok thanks",
            "okay thanks",
            "appreciate it",
            "many thanks",
        }
        farewells = {
            "bye",
            "goodbye",
            "see you",
            "see you later",
            "talk soon",
            "take care",
            "catch you later",
        }
        identity = {
            "who are you",
            "what are you",
            "introduce yourself",
            "tell me about you",
            "who are you hr bot",
        }

        identity_key = normalized.rstrip("?")
        if identity_key in identity:
            return (
                "I'm the company's HR policy assistant, ready to translate every guideline and benefit into clear, confident next steps for you."
            )

        # Skip if the message clearly contains a substantive question or keywords
        if self._looks_like_question(normalized):
            return None

        if normalized in greetings:
            return (
                "Hello! I'm your HR companion, ready to unpack policies, benefits, and anything HR-related whenever you are."
            )

        if normalized in gratitude or (
            ("thank" in normalized or "thanks" in normalized) and len(normalized.split()) <= 6
        ):
            return (
                "You're very welcome! If another HR detail pops up, just say the word and I'll jump right back in."
            )

        if normalized in farewells:
            return (
                "Take care! Whenever you need clarity on HR policies or next steps, I'll be right here to help."
            )

        # Handle short greetings that include light extras (e.g., "hi there!", "hello hr bot")
        for phrase in greetings:
            if normalized.startswith(phrase) and len(normalized.split()) <= 5:
                return (
                    "Hi there! Whenever you're ready to chat HR policies or benefits, I'll guide you through every detail."
                )

        for phrase in farewells:
            if normalized.startswith(phrase) and len(normalized.split()) <= 5:
                return (
                    "Sending you off with good vibes! Circle back anytime you want to explore HR topics together."
                )

        return None

    def _normalize_small_talk(self, query: str) -> str:
        """Lowercase, trim, and collapse whitespace for comparison."""
        normalized = query.lower().strip()
        normalized = re.sub(r"[^a-z0-9\s?]", "", normalized)
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized

    def _looks_like_question(self, normalized: str) -> bool:
        """Determine if a message likely contains a substantive question."""
        if not normalized:
            return False

        # If query mentions policy-related terms or has a question mark, treat as substantive
        question_mark = "?" in normalized
        policy_terms = [
            "policy",
            "leave",
            "benefit",
            "procedure",
            "how",
            "what",
            "when",
            "where",
            "why",
            "who",
            "can",
            "should",
            "need",
            "help",
        ]
        if question_mark:
            return True
        words = normalized.split()
        if len(words) > 6:
            return True
        for term in policy_terms:
            if term in words and term not in {"who"}:
                return True
        # Treat combinations like "hi can you" as substantive
        if any(normalized.startswith(prefix) for prefix in ["hi can", "hello can", "hey can"]):
            return True

        return False
    
    def _check_content_safety(self, query: str) -> Optional[str]:
        """
        Check for inappropriate, NSFW, or abusive content.
        Returns warning message if inappropriate content detected, None otherwise.
        Allows legitimate HR policy questions.
        """
        normalized = query.lower().strip()
        
        # Legitimate HR policy keywords that override blocking
        legitimate_hr_terms = [
            'policy', 'policies', 'harassment policy', 'sexual harassment',
            'report harassment', 'complaint', 'discrimination', 'workplace harassment',
            'hr policy', 'company policy', 'code of conduct', 'what is the policy',
            'workplace safety', 'report', 'file complaint'
        ]
        
        # Check if it's a legitimate HR policy question
        is_policy_question = any(term in normalized for term in legitimate_hr_terms)
        
        # Strong profanity patterns - ALWAYS block regardless
        strong_profanity = [
            r'\bf+u+c+k+\w*',
            r'\bs+h+i+t+\w*',
            r'\bb+i+t+c+h+\w*',
            r'\ba+s+s+h+o+l+e+',
            r'\bc+u+n+t+',
            r'\bm+o+t+h+e+r+f+u+c+k+',
            r'\bb+a+s+t+a+r+d+',
            r'\bd+i+c+k+h+e+a+d+',
            r'\bp+i+s+s+ +o+f+f+',
            r'\bb+u+l+l+s+h+i+t+',
        ]
        
        # Check for strong profanity - always block
        for pattern in strong_profanity:
            if re.search(pattern, normalized):
                return (
                    "⚠️ **Inappropriate Language Detected**\n\n"
                    "Your message contains profanity that violates workplace communication standards. "
                    "Using abusive or offensive language may result in disciplinary action according to company policy.\n\n"
                    "As your HR assistant, I'm here to help with professional questions in a respectful manner. "
                    "Please rephrase your question professionally, and I'll be happy to assist you."
                )
        
        # Explicit sexual content - block unless it's a policy question
        explicit_sexual_patterns = [
            r'\bf+u+c+k+ (my|an?|the|with)',
            r'\bsleep with',
            r'\bhave sex with',
            r'\bhook(ing)? up with',
            r'\baffair with',
            r'\bdate? (my|an?|the) (coworker|colleague|employee|boss)',
            r'\bmake love',
            r'\bget laid',
            r'\bone night stand',
            r'\bsexual (favor|act|relationship)',
        ]
        
        # NSFW terms - block unless it's a policy question
        nsfw_keywords = [
            'nude', 'naked', 'porn', 'pornography', 'xxx', 'adult content',
            'erotic', 'masturbat', 'sex tape', 'explicit content'
        ]
        
        if not is_policy_question:
            # Check explicit sexual patterns
            for pattern in explicit_sexual_patterns:
                if re.search(pattern, normalized):
                    return (
                        "⚠️ **NSFW Content Detected**\n\n"
                        "Your message contains explicit sexual content that is inappropriate for the workplace. "
                        "This type of content violates company policies and may result in disciplinary action.\n\n"
                        "If you have legitimate questions about workplace conduct policies, sexual harassment policies, "
                        "or how to report inappropriate behavior, please rephrase your question professionally."
                    )
            
            # Check NSFW keywords
            for keyword in nsfw_keywords:
                if keyword in normalized:
                    return (
                        "⚠️ **NSFW Content Detected**\n\n"
                        "Your message contains content that is inappropriate for workplace communication. "
                        "This may violate company policies and could result in disciplinary action.\n\n"
                        "I'm here to help with HR policies and procedures. Please rephrase your question professionally, "
                        "or contact your HR department directly for sensitive matters."
                    )
        
        # Violent or threatening language
        violent_keywords = [
            'kill', 'murder', 'harm', 'hurt', 'attack', 'beat', 'destroy',
            'violence', 'weapon', 'gun', 'knife', 'bomb', 'threat'
        ]
        
        # Check for violent language
        for keyword in violent_keywords:
            if keyword in normalized:
                # Exception: workplace safety questions
                if any(safe in normalized for safe in ['safety', 'policy', 'procedure', 'prevent', 'report']):
                    continue
                return (
                    "⚠️ **Concerning Language Detected**\n\n"
                    "Your message contains language that may indicate a safety concern. "
                    "If you're experiencing a safety issue or feel threatened, please contact your manager, "
                    "HR department, or security immediately. You can also call emergency services if needed.\n\n"
                    "For policy questions about workplace safety, please rephrase your question professionally."
                )
        
        # Check for discriminatory language (if hate speech patterns exist)
        hate_speech_keywords = ['racist', 'sexist', 'homophobic', 'transphobic', 'xenophobic']
        for keyword in hate_speech_keywords:
            if keyword in normalized:
                # Exception: anti-discrimination policy questions
                if any(policy in normalized for policy in ['policy', 'procedure', 'prevent', 'report', 'complaint']):
                    continue
                return (
                    "⚠️ I noticed language that may be discriminatory or offensive. "
                    "Our workplace values diversity, equity, and inclusion. "
                    "If you're inquiring about discrimination policies or need to report a concern, "
                    "please rephrase your question professionally, or contact HR directly for sensitive matters."
                )
        
        return None
    
    @agent
    def hr_assistant(self) -> Agent:
        """
        Empathetic, human-like HR assistant with deep policy knowledge
        Configuration is loaded from agents.yaml
        """
        return Agent(
            config=self.agents_config['hr_assistant'],
            tools=[self.hybrid_rag_tool, self.master_actions_tool],  # Both tools available
            llm=self.llm,
            verbose=True,
            max_iter=15,  # Increased to allow multiple tool calls if needed
            memory=False,  # Disable agent-level memory (relies on crew long-term memory)
            allow_delegation=False,  # Single agent, no delegation needed
            function_calling_llm=self.llm,  # Explicitly set function calling LLM
        )
    
    @task
    def answer_hr_query(self) -> Task:
        """
        Main task: Answer employee HR queries with empathy, accuracy, and detailed information
        Configuration is loaded from tasks.yaml
        """
        return Task(
            config=self.tasks_config['answer_hr_query'],
            agent=self.hr_assistant(),
        )
    
    @crew
    def crew(self) -> Crew:
        """Creates the production-ready HR Bot crew"""
        crew = Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            memory=True,  # Re-enabled with concise context injection
            embedder=self.embedder_config,
            cache=False,  # Use explicit response cache to avoid stale tool plans
        )
        hybrid_tool = self.hybrid_rag_tool
        master_tool = self.master_actions_tool

        return self._wrap_crew_with_sources(crew, hybrid_tool, master_tool, self.long_term_memory, self.memory_db_path)
    
    def _wrap_crew_with_sources(self, crew: Crew, hybrid_tool, master_tool, memory, memory_db_path):
        """Wraps crew with source tracking logic for both tools"""

        class CrewWithSources:
            def __init__(self, inner, retrieval_tool, master_tool, memory, memory_db_path: Optional[str]):
                self._inner = inner
                self._hybrid_tool = retrieval_tool
                self._master_tool = master_tool
                self._memory = memory
                self._memory_db_path = memory_db_path

            def kickoff(self, *args, **kwargs):
                inputs = {}
                if kwargs.get("inputs") and isinstance(kwargs["inputs"], dict):
                    inputs = dict(kwargs["inputs"])

                query = inputs.get("query") if inputs else None
                retrieved_chunks = []
                query_terms: List[str] = []
                
                # Inject concise memory context for conversation continuity
                if query:
                    self._inject_memory_context(query, inputs)
                    kwargs["inputs"] = inputs

                # Remove pre-retrieval injection - let agent call the tool naturally
                # This was causing the agent to output "Action: hr_document_search(...)" 
                # as text instead of executing the tool

                output = self._inner.kickoff(*args, **kwargs)

                if isinstance(output, str):
                    class _OutputWrapper:
                        def __init__(self, text: str):
                            self.raw = text
                            self.final_output = text
                            self.tasks_output = []

                        def __str__(self) -> str:
                            return self.raw

                    output = _OutputWrapper(output)
                final_text: Optional[str] = None
                output_text: Optional[str] = None
                try:
                    output_text = str(output)
                    
                    # Collect sources from BOTH tools (hybrid RAG + Master Actions)
                    rag_sources = self._hybrid_tool.last_sources() if hasattr(self._hybrid_tool, 'last_sources') else []
                    action_sources = self._master_tool.last_sources() if hasattr(self._master_tool, 'last_sources') else []
                    
                    # Combine sources intelligently
                    all_sources = []
                    if action_sources:
                        all_sources.extend(action_sources)
                    if rag_sources:
                        all_sources.extend(rag_sources)
                    
                    # Remove duplicates while preserving order
                    sources = list(dict.fromkeys(all_sources))
                    
                    # Validation will be done in post-processing if needed
                    # The tool itself handles NO_RELEVANT_DOCUMENTS case
                    
                    # Check if response indicates no information was found
                    no_info_indicators = [
                        "couldn't find any information",
                        "couldn't find information",
                        "couldn't find specific information", 
                        "couldn't find relevant",
                        "no information about",
                        "don't have information",
                        "doesn't appear to be covered",
                        "not covered in our current",
                        "contact your HR department",
                        "please contact your HR",
                        "recommend contacting HR"
                    ]
                    
                    output_lower = output_text.lower()
                    has_no_info = any(indicator in output_lower for indicator in no_info_indicators)
                    
                    if "Sources:" not in output_text:
                        # Only add sources if we actually found information
                        if sources and not has_no_info:
                            sources_line = "Sources: " + ", ".join(sources)
                            separator = "\n" if output_text.endswith("\n") else "\n\n"
                            new_text = f"{output_text}{separator}{sources_line}"
                            if hasattr(output, "raw"):
                                output.raw = new_text
                            if hasattr(output, "final_output"):
                                output.final_output = new_text
                            if hasattr(output, "tasks_output") and isinstance(output.tasks_output, list):
                                for task in output.tasks_output:
                                    if isinstance(task, dict) and "output" in task:
                                        task["output"] = new_text
                            output_text = new_text
                            final_text = new_text

                    # Document Evidence section disabled - using Sources line only
                    # evidence_lines = []
                    # if retrieved_chunks:
                    #     seen_quotes = set()
                    #     def extract_quotes(text: str) -> List[str]:
                    #         sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
                    #         selected: List[str] = []
                    #         for sentence in sentences:
                    #             if len(sentence) < 30:
                    #                 continue
                    #             lower = sentence.lower()
                    #             if query_terms and not any(term in lower for term in query_terms):
                    #                 continue
                    #             selected.append(sentence)
                    #             if len(selected) >= 2:
                    #                 break
                    #         if not selected and sentences:
                    #             selected.append(sentences[0])
                    #         return selected
                    #     for idx, chunk in enumerate(retrieved_chunks[:4], 1):
                    #         quotes = extract_quotes(chunk.content)
                    #         filtered = []
                    #         for quote in quotes:
                    #             normalized = " ".join(quote.split())
                    #             if normalized in seen_quotes:
                    #                 continue
                    #             seen_quotes.add(normalized)
                    #             if len(normalized) > 400:
                    #                 normalized = normalized[:400].rstrip() + "..."
                    #             filtered.append(normalized)
                    #         if filtered:
                    #             if len(filtered) == 1:
                    #                 evidence_lines.append(f"- **{chunk.source}**: \"{filtered[0]}\"")
                    #             else:
                    #                 joined = "\"; \"".join(filtered)
                    #                 evidence_lines.append(f"- **{chunk.source}**: \"{joined}\"")
                    # if evidence_lines:
                    #     evidence_section = "\n\n**Document Evidence**\n" + "\n".join(evidence_lines)
                    #     new_text = output_text.rstrip() + evidence_section
                    #     if hasattr(output, "raw"):
                    #         output.raw = new_text
                    #     if hasattr(output, "final_output"):
                    #         output.final_output = new_text
                    #     if hasattr(output, "tasks_output") and isinstance(output.tasks_output, list):
                    #         for task in output.tasks_output:
                    #             if isinstance(task, dict) and "output" in task:
                    #                 task["output"] = new_text
                    #     output_text = new_text
                    #     final_text = new_text
                except Exception:
                    pass
                try:
                    # Collect sources from both tools for memory persistence
                    rag_sources = self._hybrid_tool.last_sources() if hasattr(self._hybrid_tool, 'last_sources') else []
                    action_sources = self._master_tool.last_sources() if hasattr(self._master_tool, 'last_sources') else []
                    sources_for_memory = list(dict.fromkeys(rag_sources + action_sources))
                except Exception:
                    sources_for_memory = []
                answer_text = None
                if final_text is not None:
                    answer_text = final_text
                elif output_text is not None:
                    answer_text = output_text
                elif output is not None:
                    answer_text = str(output)
                if final_text is not None:
                    if hasattr(output, "raw"):
                        output.raw = final_text
                    if hasattr(output, "final_output"):
                        output.final_output = final_text
                if query and answer_text:
                    self._persist_conversation_snippet(query, answer_text, sources_for_memory)
                return output

            def __getattr__(self, item):
                return getattr(self._inner, item)

            def _inject_memory_context(self, query: str, inputs: dict) -> None:
                """Inject concise memory context to avoid overwhelming prompt"""
                memories = self._load_recent_memories(query, limit=3)  # Reduced from 6 to 3
                if not memories:
                    return
                
                tokens = {token for token in re.split(r"[^a-z0-9]+", query.lower()) if len(token) > 2}
                relevant = []
                for entry in memories:
                    entry_tokens = {token for token in re.split(r"[^a-z0-9]+", entry["query"].lower()) if len(token) > 2}
                    if not tokens or entry_tokens.intersection(tokens):
                        relevant.append(entry)
                
                if not relevant:
                    relevant = memories[:1]  # Only 1 fallback instead of 2
                
                # CONCISE format - just queries, no full answers
                context_lines = ["Recent conversation:"]
                for item in reversed(relevant[-2:]):  # Only last 2 conversations
                    context_lines.append(f"- Employee: {item['query']}")
                    # Include only a very brief summary (first 100 chars of answer)
                    answer_summary = item["answer"][:100].strip()
                    if len(item["answer"]) > 100:
                        answer_summary += "..."
                    context_lines.append(f"  Assistant: {answer_summary}")
                
                memory_context = "\n".join(context_lines)
                existing_context = inputs.get("context", "").strip()
                if existing_context:
                    if memory_context in existing_context:
                        return
                    inputs["context"] = f"{memory_context}\n\n{existing_context}"
                else:
                    inputs["context"] = memory_context

            def _load_recent_memories(self, query: str, limit: int = 5) -> List[dict]:
                if not self._memory_db_path:
                    return []
                try:
                    with sqlite3.connect(self._memory_db_path) as conn:
                        cursor = conn.cursor()
                        cursor.execute(
                            """
                                SELECT metadata, datetime
                                FROM long_term_memories
                                WHERE metadata LIKE '%"type": "conversation"%'
                                ORDER BY datetime DESC
                                LIMIT ?
                            """,
                            (max(limit, 1),),
                        )
                        rows = cursor.fetchall()
                except Exception:
                    return []
                memories: List[dict] = []
                seen_hashes = set()
                for metadata_json, dt in rows:
                    try:
                        data = json.loads(metadata_json)
                    except Exception:
                        continue
                    if data.get("type") != "conversation":
                        continue
                    entry_hash = data.get("hash")
                    if entry_hash and entry_hash in seen_hashes:
                        continue
                    seen_hashes.add(entry_hash)
                    remembered_query = data.get("query")
                    answer = data.get("answer")
                    if not remembered_query or not answer:
                        continue
                    memories.append(
                        {
                            "query": remembered_query.strip(),
                            "answer": answer.strip(),
                            "datetime": dt,
                            "sources": data.get("sources"),
                        }
                    )
                return memories

            def _persist_conversation_snippet(self, query: str, answer: str, sources: List[str]) -> None:
                if not self._memory:
                    return
                trimmed_answer = answer.strip()
                if not trimmed_answer:
                    return
                if len(trimmed_answer) > 4000:
                    trimmed_answer = trimmed_answer[:4000].rstrip() + "..."
                digest_input = f"{query.strip()}\n{trimmed_answer}"
                entry_hash = hashlib.sha256(digest_input.encode("utf-8")).hexdigest()
                metadata = {
                    "type": "conversation",
                    "query": query.strip(),
                    "answer": trimmed_answer,
                    "sources": list(sources) if isinstance(sources, list) else [],
                    "hash": entry_hash,
                    "quality": 1.0,
                }
                if self._memory_db_path:
                    try:
                        with sqlite3.connect(self._memory_db_path) as conn:
                            cursor = conn.cursor()
                            cursor.execute(
                                "SELECT 1 FROM long_term_memories WHERE metadata LIKE ? LIMIT 1",
                                (f'%"hash": "{entry_hash}"%',),
                            )
                            if cursor.fetchone():
                                return
                    except Exception:
                        pass
                try:
                    item = LongTermMemoryItem(
                        agent="hr_assistant",
                        task=f"Conversation log: {query.strip()}",
                        expected_output=trimmed_answer,
                        datetime=datetime.utcnow().isoformat(),
                        quality=metadata["quality"],
                        metadata=metadata,
                    )
                    self._memory.save(item)
                except Exception:
                    pass

        return CrewWithSources(crew, hybrid_tool, master_tool, self.long_term_memory, self.memory_db_path)
