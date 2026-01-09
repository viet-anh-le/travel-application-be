import os
from dotenv import load_dotenv
from pathlib import Path
from langchain_ollama import OllamaLLM
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

env_path = Path(__file__).resolve().parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

def _gemini(model: str, temperature: float = 0.0, max_output_tokens: int = 4096) -> ChatGoogleGenerativeAI:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")
    return ChatGoogleGenerativeAI(
        model=model,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        google_api_key=api_key,
    )

def llm_plan() -> ChatGoogleGenerativeAI:
    return _gemini(model="gemini-2.5-flash-lite", temperature=0.3)

def llm_summary() -> ChatGroq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("LLM_MODEL_SUMMARY not set")

    model = "openai/gpt-oss-120b"
    temperature = 0.0

    # max_tokens = 1000

    timeout = 120

    return ChatGroq(
        groq_api_key=api_key,
        model=model,
        temperature=temperature,
        # max_tokens=max_tokens,
        timeout=timeout,
    )

def llm_create_standalone_question():
    return OllamaLLM(
        model="llama3.1:8b",
        temperature=0
    )

def llm_rag() -> ChatGroq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("LLM_RAG not set")

    model = "openai/gpt-oss-120b"
    temperature = 0.0

    # max_tokens = 1000

    timeout = 120

    return ChatGroq(
        groq_api_key=api_key,
        model=model,
        temperature=temperature,
        # max_tokens=max_tokens,
        timeout=timeout,
    )

def llm_classify():
    return OllamaLLM(
        model="llama3.1:8b",
        temperature=0
    )

def llm_evaluate_faithfulness():
    return OllamaLLM(
        model="llama3.1:8b",
        temperature=0
    )

def llm_evaluate_relevance():
    return OllamaLLM(
        model="llama3.1:8b",
        temperature=0
    )

def llm_evaluate_precision():
    return OllamaLLM(
        model="llama3.1:8b",
        temperature=0
    )

def llm_evaluate_recall():
    return OllamaLLM(
        model="llama3.1:8b",
        temperature=0
    )