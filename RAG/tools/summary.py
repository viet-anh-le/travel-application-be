from langchain_core.prompts import ChatPromptTemplate
from RAG.core.llm import llm_summary

def summarize_text(text: str) -> str:
    llm = llm_summary()
    prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are a **professional Vietnamese travel editor**.

    Your task is to **summarize the provided content** into a **concise, well-structured travel itinerary in Vietnamese**.  
    The plan should highlight the **location, food, accommodation, weather, and key activities**, while ensuring smooth flow and readability.

    ### Requirements:
    - Use **only** the provided information — do **not** invent new details.  
    - Write naturally, using a **friendly and coherent Vietnamese tone** suitable for a travel article.  
    - If possible, organize the plan **by days (Ngày 1, Ngày 2, etc.)**.  
    - **Avoid repeating** the same restaurants, attractions, or activities across multiple days.  
    - Combine similar points into one section if repetition occurs.  
    - Ensure each day feels unique but consistent with the trip’s overall theme.  

    ### Output:
    A clear, engaging, and concise **Vietnamese travel plan** written in paragraph form, possibly divided by days.
    """
        ),
        (
            "human",
            "Dưới đây là nội dung cần được tóm tắt thành hành trình:\n\n{text}",
        ),
    ])

    chain = prompt | llm
    result = chain.invoke({"text": text})
    return result.content.strip()
