from langchain_core.messages import HumanMessage, AIMessage

def build_chat_history_from_db(messages: list) -> list:
    chat_history = []

    for message in messages:
        role = message.get("role")
        content = message.get("content")
        if role == "human":
            chat_history.append(HumanMessage(content=content))
        elif role == "ai":
            chat_history.append(AIMessage(content=content))
            
    return chat_history