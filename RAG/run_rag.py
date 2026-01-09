import os

# from langchain.tools.retriever import create_retriever_tool
# from langchain.agents import AgentExecutor, create_openai_functions_agent, create_react_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from utils.split_data import split_data
from utils.create_retriever import create_vectordb, create_ensemble_retriever, create_parent_retriever
from utils.get_llm import get_llm

current_dir = os.path.dirname(os.path.abspath(__file__))
FILEPATH_REL = "data/vi.wikipedia.org_wiki_V%C4%83n_Mi%E1%BA%BFu_%E2%80%93_Qu%E1%BB%91c_T%E1%BB%AD_Gi%C3%A1m/content.md"
FILEPATH = os.path.join(current_dir, FILEPATH_REL)

def run_rag(query):
    chunks = split_data(FILEPATH)
    vectordb = create_vectordb(chunks)
    retriever = create_parent_retriever(FILEPATH)
    # retriever = create_ensemble_retriever(vectordb, query)
    llm = get_llm()
    # tool = create_retriever_tool(
    #     retriever,
    #     "find",
    #     "Search for information of a question in the knowledge base."
    # )
    # tools = [tool]
    # system = """Bạn là chuyên gia AI về du lịch. Tên bạn là Nomado."""
    # prompt = ChatPromptTemplate.from_messages([
    #     ("system", system),
    #     ("system", "Chỉ sử dụng dữ liệu có trong tài liệu đã cung cấp, hãy trả lời những câu hỏi của người dùng. Bạn có thể sử dụng những công cụ hỗ trợ sau nếu cần thiết:{tools} với các tên tương ứng {tool_names}. Nếu bạn không chắc chắn, hãy đưa ra câu trả lời mà tài liệu cung cấp cho là đúng nhất."),
    #     ("human", "{input}"),
    #     ("assistant", "{agent_scratchpad}")
    # ])
    # agent = create_openai_functions_agent(llm=llm, tools=tools, prompt=prompt)
    # agent_executor = AgentExecutor(agent=agent, tools=[tool], verbose=True, handle_parsing_errors=True)
    # response = agent_executor.invoke({
    #     "input": query,
    #     "tools": agent_executor.tools,
    #     "tool_names": [tool.name for tool in agent_executor.tools]
    # })
    # return(response["output"])
    template = """
    Bạn là chuyên gia AI về du lịch. Tên bạn là Nomado.
    Hãy sử dụng những ngữ cảnh sau để trả lời câu hỏi của người dùng: {context}
    Dưới đây là câu hỏi: {question}
    """
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | llm
    context = retriever.invoke(query)
    print(context)
    result = chain.invoke({"context": context, "question": query})
    print(result)

# response = run_rag("Văn miếu được xây dựng từ năm nào?")
# print(response)
run_rag("Cuộc đại trùng tu năm 1483 được ghi lại như thế nào?")