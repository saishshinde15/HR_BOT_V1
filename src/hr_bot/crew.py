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


@CrewBase
class HrBot():
    """
    Production-ready HR Bot with empathetic, human-like responses:
    - Emotionally intelligent and empathetic communication
            }
            if aws_region:
                llm_kwargs["aws_region_name"] = aws_region
    - Amazon Bedrock (Nova Micro) LLM for natural, conversational responses
    - Detailed, accurate answers with proper source citation
    """

    agents: List[BaseAgent]
    tasks: List[Task]
    
    def __init__(self):
        super().__init__()
        
        # Initialize Amazon Bedrock LLM (using environment variables)
        # Set AWS credentials for Bedrock access
        aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
        aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        aws_region = os.getenv("AWS_REGION", "ap-south-1")
        
        if aws_access_key:
            os.environ["AWS_ACCESS_KEY_ID"] = aws_access_key
        if aws_secret_key:
            os.environ["AWS_SECRET_ACCESS_KEY"] = aws_secret_key
        if aws_region:
            os.environ["AWS_REGION"] = aws_region
            os.environ["AWS_DEFAULT_REGION"] = aws_region
        
        llm_kwargs = {
            "model": os.getenv("BEDROCK_MODEL", "bedrock/us.amazon.nova-micro-v1:0"),
            "temperature": 0.7,  # Higher temperature for more natural, conversational responses
        }
        if aws_region:
            llm_kwargs["aws_region_name"] = aws_region

        self.llm = LLM(**llm_kwargs)
        
        # Initialize tools
        self.hybrid_rag_tool = HybridRAGTool(data_dir="data")

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
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        self.memory_storage_dir = os.path.join(project_root, "storage")
        os.makedirs(self.memory_storage_dir, exist_ok=True)
        self.memory_db_path = os.path.join(self.memory_storage_dir, "long_term_memory.db")
        self.long_term_memory = LongTermMemory(
            storage=LTMSQLiteStorage(
                db_path=self.memory_db_path
            )
        )
    
    @agent
    def hr_assistant(self) -> Agent:
        """
        Empathetic, human-like HR assistant with deep policy knowledge
        Configuration is loaded from agents.yaml
        """
        return Agent(
            config=self.agents_config['hr_assistant'],
            tools=[self.hybrid_rag_tool],
            llm=self.llm,
            verbose=True,
            max_iter=5,  # Limit iterations for faster responses
            memory=False,  # Disable agent-level memory (relies on crew long-term memory)
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
            memory=True,  # Enable crew-level memory while keeping agent memory disabled
            embedder=self.embedder_config,
            long_term_memory=self.long_term_memory,  # SQLite-based conversation history
            cache=True,   # Enable caching for faster repeated queries
        )
        hybrid_tool = self.hybrid_rag_tool

        class CrewWithSources:
            def __init__(self, inner, retrieval_tool, memory, memory_db_path: Optional[str]):
                self._inner = inner
                self._hybrid_tool = retrieval_tool
                self._memory = memory
                self._memory_db_path = memory_db_path

            def kickoff(self, *args, **kwargs):
                inputs = {}
                if kwargs.get("inputs") and isinstance(kwargs["inputs"], dict):
                    inputs = dict(kwargs["inputs"])

                query = inputs.get("query") if inputs else None
                retrieved_chunks = []
                query_terms: List[str] = []
                if query:
                    self._inject_memory_context(query, inputs)
                    kwargs["inputs"] = inputs

                if query:
                    try:
                        retrieved_chunks = self._hybrid_tool.retriever.hybrid_search(query, top_k=8)
                        if retrieved_chunks:
                            query_terms = [t for t in re.split(r"[^a-z0-9]+", query.lower()) if t and len(t) > 2]
                            context_snippets = []
                            for idx, chunk in enumerate(retrieved_chunks[:4], 1):
                                snippet = " ".join(chunk.content.strip().split())
                                if len(snippet) > 600:
                                    snippet = snippet[:600].rstrip() + "..."
                                context_snippets.append(f"[{idx}] {chunk.source}: {snippet}")

                            existing_context = inputs.get("context", "").strip()
                            context_sections = []
                            if existing_context:
                                context_sections.append(existing_context)
                            if context_snippets:
                                retrieved_section = "Retrieved context:\n" + "\n".join(context_snippets)
                                context_sections.append(retrieved_section)
                            if context_sections:
                                inputs["context"] = "\n\n".join(context_sections)
                                kwargs["inputs"] = inputs

                            sources = [f"[{idx}] {chunk.source}" for idx, chunk in enumerate(retrieved_chunks, 1)]
                            try:
                                object.__setattr__(self._hybrid_tool, '_last_sources', sources)
                                self._hybrid_tool.retriever._last_sources = sources
                            except Exception:
                                pass
                    except Exception:
                        retrieved_chunks = []

                output = self._inner.kickoff(*args, **kwargs)
                final_text: Optional[str] = None
                output_text: Optional[str] = None
                try:
                    output_text = str(output)
                    if "Sources:" not in output_text:
                        sources = self._hybrid_tool.last_sources()
                        if sources:
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
                    sources_for_memory = self._hybrid_tool.last_sources()
                except Exception:
                    sources_for_memory = []
                answer_text = None
                if final_text is not None:
                    answer_text = final_text
                elif output_text is not None:
                    answer_text = output_text
                elif output is not None:
                    answer_text = str(output)
                if query and answer_text:
                    self._persist_conversation_snippet(query, answer_text, sources_for_memory)
                return final_text if final_text is not None else output

            def __getattr__(self, item):
                return getattr(self._inner, item)

            def _inject_memory_context(self, query: str, inputs: dict) -> None:
                memories = self._load_recent_memories(query, limit=6)
                if not memories:
                    return
                tokens = {token for token in re.split(r"[^a-z0-9]+", query.lower()) if len(token) > 2}
                relevant = []
                for entry in memories:
                    entry_tokens = {token for token in re.split(r"[^a-z0-9]+", entry["query"].lower()) if len(token) > 2}
                    if not tokens or entry_tokens.intersection(tokens):
                        relevant.append(entry)
                if not relevant:
                    relevant = memories[:2]
                context_lines = ["Recent conversation:"]
                for item in reversed(relevant):
                    answer = item["answer"]
                    if len(answer) > 600:
                        answer = answer[:600].rstrip() + "..."
                    context_lines.append(f"- Employee: {item['query']}")
                    context_lines.append(f"  Assistant: {answer}")
                    sources = item.get("sources")
                    if sources:
                        if isinstance(sources, list):
                            sources_text = ", ".join(str(s) for s in sources if s)
                        else:
                            sources_text = str(sources)
                        if sources_text:
                            context_lines.append(f"  Sources referenced: {sources_text}")
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

        return CrewWithSources(crew, hybrid_tool, self.long_term_memory, self.memory_db_path)
