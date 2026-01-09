from langchain_ollama import OllamaLLM

def get_llm():
  llm = OllamaLLM(
    model="llama3.1:8b",
    temperature=0
  )
  return llm

