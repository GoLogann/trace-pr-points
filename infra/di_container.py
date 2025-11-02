import os
from packages.adapters.calculator_adapter.apf_calculator import APFCalculator
from packages.adapters.github_adapter.pr_reader import GitHubPRReader
from packages.adapters.github_adapter.notifier import GitHubNotifier
from packages.adapters.github_adapter.status_publisher import GitHubStatusPublisher
from packages.adapters.baseline_repo_adapter.sql_repo import SQLBaselineRepo, SQLReportRepo

from packages.adapters.embedder_adapter.sbert_embedder import SBertEmbedder
from packages.adapters.parser_adapter.heuristics3 import HeuristicDiffParserAPFv3
from packages.adapters.vector_repo_adapter.qdrant_repo import QdrantRepo
from packages.adapters.llm_adapter.ollama_llm import OllamaLLM
from packages.adapters.llm_adapter.openai_llm import OpenAILLM

from apps.agent.graph import Env, build_graph

def build_graph_env() -> Env:
    # LLM provider
    provider = os.getenv("LLM_PROVIDER","openai").lower()
    print(f"Using LLM provider: {provider}")
    if provider == "openai":
        llm = OpenAILLM()
    else:
        llm = OllamaLLM()

    # RAG
    embedder = SBertEmbedder()
    vector = QdrantRepo(embedder)

    return Env(
        pr_reader=GitHubPRReader(),
        parser=HeuristicDiffParserAPFv3(),
        calculator=APFCalculator(),
        notifier=GitHubNotifier(),
        baseline_repo=SQLBaselineRepo(),
        report_repo=SQLReportRepo(),
        status_pub=GitHubStatusPublisher(),
        vector_repo=vector,
        llm=llm
    )

def build_graph_compiled():
    env = build_graph_env()
    return build_graph(env)
