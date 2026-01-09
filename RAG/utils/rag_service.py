import os

from RAG.request.AskRequest import ChatRequest
from RAG.repositories.chat_repository import ChatRepository
from RAG.repositories.redis_chat_repository import RedisChatRepository
from RAG.models.chat_schema import ChatMessage
from RAG.core.llm import llm_rag, llm_classify, llm_create_standalone_question

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser

class RAGService:
    @staticmethod
    async def generate_response(retriever, payload: ChatRequest, standalone_question: str, chat_history: list, topics: list = [], location: list = []):
        try:
            # message = payload.message
            # session_id = payload.session_id

            llm = llm_rag()

            system = """### Role and Goal
                You are an AI assistant specializing in tourism. Your persona is friendly, helpful, **detailed** and **extremely accurate**.
                Your task is to answer user questions using a Hybrid approach: Prioritize the provided 'Context', but supplement with your own knowledge when specific details are missing.
                Your goal is to provide the **most comprehensive answer possible**.

                ### The Golden Rules (MOST IMPORTANT)

                1.  **Source Hierarchy (Context First, Knowledge Second):**
                    * **Core Entities:** The list of places, restaurants, dishes, or activities you recommend MUST come **EXCLUSIVELY** from the 'Context'. **DO NOT** invent new places or recommend items not mentioned in the 'Context'.
                    * **Supplementary Details [IMPORTANT EXCEPTION]:** If a place/item is found in the 'Context' but specific factual details (specifically: **Address**, **Price**, **Opening Hours**, or **Contact Info**) are missing, you **ARE AUTHORIZED AND ENCOURAGED** to use your internal pre-trained knowledge to fill in these missing details.
                    * **[CRITICAL - SEAMLESS BLENDING]:** You must blend these two sources (Context & Internal Knowledge) into a single, unified voice. **DO NOT** distinguish between them in your output. The user must NOT know which part came from the document and which came from your internal knowledge.
                    * If you use internal knowledge for Price/Hours, ensure it is the most recent estimate you know.

                2.  **Natural Phrasing (No Meta-Talk):**
                    * You must sound like a natural, human expert.
                    * **DO NOT** talk about yourself as an AI, mention "Context," "documents," or "internal knowledge."
                    * **STRICTLY FORBIDDEN PHRASES:** You are prohibited from using phrases like:
                        * "Thông tin này được bổ sung từ kiến thức chung" (This info added from general knowledge)
                        * "Trong ngữ cảnh không có thông tin này" (Context lacks this info)
                        * "Lưu ý: Dữ liệu về giá được lấy từ..." (Note: Price data is taken from...)
                    * Just state the information directly as if you know it.

                3.  **The "Be Detailed and Helpful" Rule:**
                    * When the user asks for information, find relevant items in the 'Context'.
                    * **[QUANTITY LOGIC]:**
                        * **Case A (General Request):** If the user asks a general question **WITHOUT** specifying a quantity (e.g., "suggest some places"), **you MUST limit your response to the top 3-5 most relevant items** found in the 'Context' to avoid overwhelming the user.
                        * **Case B (Specific Request):** If the user specifies a quantity (e.g., "top 10", "list all"), follow that instruction.
                        * **Case C (Insufficient Data):** If the 'Context' has fewer items than requested (e.g., user asks for 20, Context has 10), detailedly describe the 10 items you have and naturally state that those are the best recommendations you have right now.
                    * **[DETAIL REQUIREMENT]:** For the items you choose to list, provide a detailed summary:
                        * *Step 1:* Extract description/facts from 'Context'.
                        * *Step 2:* Check if 'Address' or 'Price' is missing in 'Context'.
                        * *Step 3:* If missing, retrieve them from your internal knowledge to make the answer complete.

                4.  **[PRIORITY 1] Handling Off-topic, Greeting, or Vague Questions:**
                    * Check this **FIRST**.
                    * If Greeting/Off-topic: Respond politely and steer back to tourism.
                    * If Vague (e.g., "Give me info"): Respond with: "Tôi có thể giúp gì cho bạn về thông tin du lịch?".

                5.  **Handling Conversation History:**
                    * Use 'Conversation History' to understand follow-ups.
                    * Avoid repeating information unless asked.

                6.  **Handling **Completely** Missing Topics:**
                    * This rule applies ONLY if the 'Context' contains **NO relevant places/items** related to the user's question.
                    * In this specific case (Context is empty regarding the topic), respond with: "Tôi hiện chưa thể đưa ra câu trả lời chính xác vì dữ liệu liên quan đến yêu cầu của bạn chưa đầy đủ. Bạn hãy cung cấp thêm thông tin (như nguồn dữ liệu, nội dung cụ thể hoặc ví dụ minh hoạ) để tôi có thể hỗ trợ bạn hiệu quả hơn."

                7.  **Formatting & Language:**
                    * **Language:** Always answer in **Vietnamese**.
                    * **No Post-amble:** Do not add any summary sentences at the end explaining where the information came from. **ABSOLUTELY NO** "Lưu ý" (Note) section about data sources.
                    * **Formatting:** Use clean **Markdown**.
                        * Use **Bold** (`**text**`) for names/highlights.
                        * Use **Bullet points** (`*` or `-`) for lists.
                        * **STRICTLY PROHIBITED:** No HTML tags (`<br>`, `<div>`). Remove or replace them if found in Context.
                8.  **[CRITICAL - TIME PRIORITY & DATA FRESHNESS]:**
                    * **Detection Task:** Before answering, you **MUST** scan the **'Document Name'** (Tên tài liệu) and **'Content'** (Nội dung) of all context chunks to identify temporal markers (e.g., years like 2024, 2025; dates like October 2025; or keywords like "latest", "updated", "newest").
                    * **Comparison & Selection:**
                        * If you find **conflicting information** regarding the same location, price, or event, you **MUST** prioritize the information from the document with the **MOST RECENT** time marker (Higher year/Later date takes precedence).
                        * *Example:* If 'Document A' (contains "2023") states ticket price is 50k, and 'Document B' (contains "2025") states it is 100k -> You **MUST** answer 100k.
                    * **Smart Inference:** If the user asks for "current", "upcoming", or "new" events, explicitly favor documents with the latest year found in the Context (e.g., prioritize 2025 data over 2024).
                    * **Outdated Data Warning:** If the only available information seems outdated (e.g., from 2020 or earlier) and no newer data exists, you must explicitly state: *"Thông tin này được ghi nhận từ năm [Year]..."* to warn the user.
                """

            prompt = ChatPromptTemplate.from_messages([
                ("system", system),
                ("user", """Đây là 'Lịch sử trò chuyện' và 'Ngữ cảnh' để bạn tham khảo.
                                    
                    <Lịch sử trò chuyện>
                    {conversation}
                    </Lịch sử trò chuyện>

                    <Ngữ cảnh>
                    {context}
                    </Ngữ cảnh>

                    Hãy trả lời 'Câu hỏi' dưới đây dựa trên các quy tắc đã đề ra.
                    Câu hỏi: {question}""")
            ])

            rag_chain = prompt | llm | StrOutputParser()

            conversation_lines = []

            for msg in chat_history:
                if msg.type == 'human':
                    conversation_lines.append(f"Người dùng: {msg}")
                elif msg.type == 'ai':
                    conversation_lines.append(f"Trợ lý: {msg}")

            conversation_str = "\n".join(conversation_lines)

            print("\n---------------------Conversation so far:---------------------\n")
            print(conversation_str)

            if not topics or 'Off_topic' in topics:
                yield {"type": "context", "data": []}
                async for chunk in rag_chain.astream({
                    "conversation": conversation_str,
                    "context": "No context provided (Off-topic or Chat).",
                    "question": standalone_question
                }):
                    yield {"type": "content", "data": chunk}
                return
            
            
            # Retrieve relevant documents
            context_docs = await RAGService.retrieve_documents(retriever, standalone_question)
            
            yield {
                "type": "context",
                "data": [doc.dict() for doc in context_docs] 
            }

            formatted_contexts = []
            for doc in context_docs:
                name = doc.metadata.get('Name', 'Không rõ')
                
                context_str = f"Tên tài liệu: {name}\nNội dung: {doc.page_content}"
                formatted_contexts.append(context_str)

            prompt_input = {
                "conversation": conversation_str,
                "context": "\n\n".join(formatted_contexts),
                "question": standalone_question
            }
            
            full_response_log = "" 
            print("\n---------------------Start Streaming Response:---------------------\n")
            
            async for chunk in rag_chain.astream(prompt_input):
                full_response_log += chunk
                yield {
                    "type": "content",
                    "data": chunk
                }
            
            print(full_response_log) 
            print("\n---------------------End Streaming---------------------\n")

        except Exception as e:
            raise RuntimeError(f"RAG generation error: {e}")
    
    @staticmethod
    async def classify_query(query: str):
        try:
            llm = llm_classify()

            system = """You are a query classifier assistant. Your SOLE task is to analyze the user's "Question" and extract the 'Topic' and 'Location'.

                ### CLASSIFICATION RULES:

                    1. **Topic**
                    - Represents *what the user wants to know about*.
                    - Must be a **list** (even if only one element).
                    - Allowed values: ['Food', 'Accommodation', 'Attraction', 'General', 'Festival', 'Restaurant', 'Transport', 'Plan', 'Off_topic'].
                    - You may include **multiple topics** if the question clearly refers to multiple aspects.
                        - Example: "Phố ẩm thực Hồ Thị Kỷ có món gì ngon và có điểm tham quan nào gần đó?"  
                        → `"Topic": ["Food", "Attraction"]`
                        - Example: "Khu vực Hội quán Nghĩa An trong lễ hội có bán món ăn nào không?"
                        → `"Topic": ["Food", "Festival", "Attraction"]`
                        - Example: "Những nơi lưu trú nào khi tham gia lễ hội Nghinh Ông Cần Giờ?"
                        → `"Topic": ["Accommodation", "Festival", "Attraction"]`
                    - If the question mentions nearly places or proximity → include relevant topics like 'Attraction', 'Accommodation', or 'Restaurant' as applicable.
                    - Only assign 'Plan' if the user explicitly asks to create an itinerary, a schedule, or a multi-day plan (e.g., "2-day plan", "3 days 2 nights", "itinerary for the weekend").
                    - DO NOT assign 'Plan' if the user is simply asking for options or filtering a search by a part of the day (e.g., "in the morning", "in the evening", "at night").
                    - If the question is unrelated to tourism or a greeting or the question not mentions the main points to do something → `"Topic": ["Off_topic"]`. - Example: "Xin chào!", "What is your name?", "Cho địa chỉ chi tiết"

                    2. **Location**
                    - Represents the **primary geographic area(s)** that are the **context** or **main subject** of the user's question.
                    - Must be a **list** (even if only one element).
                    - Allowed values: ['Hà Nội', 'Thành phố Hồ Chí Minh', 'Đà Nẵng'].
                    - You MUST NOT guess the city if it is not **explicitly** mentioned by name.
                    - If the question contains a **district, ward, street name, or any smaller area** (e.g., "Quận 5", "Cần Giờ", "Phú Thọ Hòa", "Nghĩa An") → you MUST **NOT** map it to any city name.
                    
                    - **RULE 2a (Search Context vs. Subject):** If a city name is part of a *subject* (e.g., "bánh mì Hà Nội") but the question is asking for information *within another city* (e.g., "...ở Hồ Chí Minh"), you MUST **only** include the city that is the *search context* ("Thành phố Hồ Chí Minh").
                    
                    - **RULE 2b (Comparisons):** If the question is *comparing* multiple cities (e.g., "Sự khác biệt giữa Hà Nội và Đà Nẵng"), then include all valid cities mentioned.
                    
                    - If no allowed city name is present as the main context, ALWAYS output an empty list [].

                    3. **Output format**
                    - Output ONLY valid JSON.
                    - Structure:
                        ```json
                        {{
                        "Topic": [...],
                        "Location": [...]
                        }}
                        ```
                    - No explanations or additional text.

                    ---
                    ### EXAMPLES (Demonstrating the PLAINNING Rule):
                    Question: "Hãy giúp tôi lên kế hoạch du lịch tại Cần Giờ"
                    Output:
                    {{"Topic": ["Plan"], "Location": []}}

                    Question: "Những nơi vui chơi ở Sài Gòn buổi tối?"
                    Output:
                    {{"Topic": ["Attraction"], "Location": ["Thành phố Hồ Chí Minh"]}}

                    Question: "Gợi ý 1 số nhà hàng cho buổi tối ở Hà Nội"
                    Output:
                    {{"Topic": ["Food", "Restaurant"], "Location": ["Hà Nội"]}}

                    ### EXAMPLES (Demonstrating the STRICT REJECTION RULE):

                    Question: "Lễ hội Nghinh Ông Cần Giờ thường được tổ chức vào thời gian nào hàng năm?"
                    Output:
                    {{"Topic": ["Festival"], "Location": []}}

                    Question: "Nhà lưu niệm Bác Hồ ở số 5 Châu Văn Liêm có vai trò lịch sử gì?"
                    Output:
                    {{"Topic": ["Attraction"], "Location": []}}

                    Question: "Khu vực Hội quán Nghĩa An trong lễ hội có bán món ăn nào không?"
                    Output:
                    {{"Topic": ["Food", "Festival", "Attraction"], "Location": []}}
                    
                    Question: "Địa đạo Phú Thọ Hòa (Quận Tân Phú) mang giá trị gì?"
                    Output:
                    {{"Topic": ["Attraction"], "Location": []}}
                    
                    Question: "Khách sạn nào gần chợ Bến Thành?"
                    Output: 
                    {{"Topic": ["Accommodation"], "Location": []}}
                    
                    Question: "Phố ẩm thực Hồ Thị Kỷ có món gì ngon và có điểm du lịch nào gần đó?"
                    Output:
                    {{"Topic": ["Food", "Attraction"], "Location": []}}
                    
                    Question: "Khi đến Hội quán Vhị Pù (264 Hải Thượng Lãn Ông), du khách có thể thưởng thức món ăn truyền thống nào của người Hoa tại khu vực Chợ Lớn gần đó?"
                    Output:
                    {{"Topic": ["Food", "Attraction"], "Location": []}}

                    ---
                    
                    ### EXAMPLES (Demonstrating Search Context vs. Subject):

                    Question: "Bánh mì Hà Nội được bán ở đâu ở Hồ Chí Minh?"
                    Output:
                    {{"Topic": ["Food", "Restaurant"], "Location": ["Thành phố Hồ Chí Minh"]}}

                    Question: "Tôi muốn ăn phở Hà Nội tại Đà Nẵng"
                    Output:
                    {{"Topic": ["Food", "Restaurant"], "Location": ["Đà Nẵng"]}}
                    
                    ---

                    ### EXAMPLES (Demonstrating Comparisons and Standard Cases):
                    
                    Question: "Các khách sạn ở Đà Nẵng có gần biển không?"
                    Output:
                    {{"Topic": ["Accommodation"], "Location": ["Đà Nẵng"]}}

                    Question: "Ẩm thực Hà Nội và Đà Nẵng khác nhau thế nào?"
                    Output:
                    {{"Topic": ["Food"], "Location": ["Hà Nội", "Đà Nẵng"]}}

                    Question: "Khách sạn nào ở Thành phố Hồ Chí Minh gần chợ Bến Thành?"
                    Output:
                    {{"Topic": ["Accommodation"], "Location": ["Thành phố Hồ Chí Minh"]}}

                    Question: "Xin chào!"
                    Output:
                    {{"Topic": ["Off_topic"], "Location": []}}

                    ---

                Now classify the following Question:
            """

            prompt = ChatPromptTemplate.from_messages([
                ("system", system),
                ("user", "Question: {question}")
            ])

            classification_chain = prompt | llm | JsonOutputParser()

            print(f"\n---------------------Classifying query: {query}---------------------\n")
            classification = await classification_chain.ainvoke({"question": query})

            # Filter allowed topics and locations
            allowed_cities = ["Hà Nội", "Thành phố Hồ Chí Minh", "Đà Nẵng"]
            allowed_topics = ['Food', 'Accommodation', 'Attraction', 'General', 'Festival', 'Restaurant', 'Transport', 'Plan', 'Off_topic']
            topics = [topic for topic in classification.get("Topic", []) if topic in allowed_topics]
            classification["Topic"] = topics
            locations = [loc for loc in classification.get("Location", []) if loc in allowed_cities]
            classification["Location"] = locations

            print(f"\n---------------------Classification result: {classification}---------------------\n")

            return classification

        except Exception as e:
            raise RuntimeError(f"Query classification error: {e}")

    @staticmethod
    async def retrieve_documents(retriever, query: str):
        try:
            start_time_retrieval = os.times()
            print("\n---------------------Retrieving relevant documents...---------------------\n")
            context_docs = await retriever.ainvoke(query)
            end_time_retrieval = os.times()
            print("\n---------------------Retrieved relevant documents in", end_time_retrieval.user - start_time_retrieval.user, "seconds---------------------\n")

            print("\n---------------------Context Documents:---------------------\n")
            valid_docs = []

            for index, doc in enumerate(context_docs):
                if index > 0:
                    print("--------------------------------------------------------------\n")

                relevance_score = doc.metadata.get('relevance_score')

                if relevance_score is not None and relevance_score < 0.3:
                    print(f"\nOriginal Index {index}: Removing low-relevance document (score: {relevance_score}):\n {doc.page_content[:200]}...\n")
                    continue 

                print(f"Context number {index} (Original {index}):\n {doc.page_content}")
                print("  Metadata:", doc.metadata)
                
                valid_docs.append(doc)

            print("\n---------------------End of Context Documents---------------------\n")

            return context_docs

        except Exception as e:
            raise RuntimeError(f"Document retrieval error: {e}")

    @staticmethod
    async def build_standalone_question(question: str, chat_history: list):
        try:
            contextualize_q_system_prompt = """Bạn là một công cụ viết lại câu. Nhiệm vụ duy nhất của bạn là chuyển đổi "Câu hỏi mới" và "Lịch sử trò chuyện" thành một "Câu hỏi độc lập" (standalone question) có thể hiểu được mà không cần lịch sử.

                Định dạng JSON BẮT BUỘC:
                ```json
                {{
                    "standalone_question": "Câu hỏi độc lập được viết lại ở đây"
                }}
                ```
            
                QUY TẮC CỐT LÕI (BẮT BUỘC TUÂN THỦ):

                1.  **NGHIÊM CẤM TRẢ LỜI CÂU HỎI:** Vai trò của bạn KHÔNG phải là trả lời. Nhiệm vụ chỉ là VIẾT LẠI CÂU HỎI vào trường JSON. Nếu bạn trả lời, bạn đã thất bại.
                2.  **NGHIÊM CẤM SAO CHÉP LỊCH SỬ:** KHÔNG được sao chép câu trả lời của AI từ "Lịch sử trò chuyện". Chỉ sử dụng "Lịch sử trò chuyện" để HIỂU NGHĨA và BỐI CẢNH của "Câu hỏi mới".
                3.  **QUY TẮC "VIẾT LẠI" (ƯU TIÊN SỐ 1):** Nếu "Câu hỏi mới" là câu hỏi ngắn, phụ thuộc vào lịch sử (ví dụ: "Ở đó giá bao nhiêu?", "Mấy giờ vậy?") HOẶC là một câu hỏi chung chung (ví dụ: "lên kế hoạch", "đi du lịch") mà bối cảnh địa điểm nằm trong Lịch sử, hãy dùng "Lịch sử trò chuyện" và bối cảnh địa điểm đó để viết lại thành câu hỏi đầy đủ và điền vào trường "standalone_question".
                4.  Nếu "Câu hỏi mới" chỉ gồm 1-2 từ ngắn gọn như “Tiếp”, “Còn gì?”, “Ở đó sao?”, “Món đó ngon không?”, hãy sử dụng “Lịch sử” để suy ra chủ đề hoặc địa điểm gần nhất và viết lại thành câu hỏi đầy đủ có ngữ nghĩa hoàn chỉnh.
                5.  **QUY TẮC "LẶP LẠI" (ƯU TIÊN SỐ 2):** Nếu "Câu hỏi mới" đã là một câu hỏi độc lập, đầy đủ ý nghĩa và không cần lịch sử, hãy điền Y HỆT nó vào trường "standalone_question".
                6.  **GIỚI HẠN OUTPUT:** CHỈ được xuất ra câu hỏi độc lập đã được viết lại. Không thêm lời chào, lời giải thích, hay bất cứ thứ gì khác.
                7.  **GIỮ NGUYÊN ĐẠI TỪ:** Phải giữ nguyên đại từ của người dùng ("tôi", "cho tôi", "của tôi").
                8.  **CHỌN NGỮ CẢNH MỚI NHẤT:** Nếu có nhiều câu trong "Lịch sử trò chuyện", chỉ sử dụng ngữ cảnh gần nhất của người dùng (Human) để viết lại câu hỏi. Không dựa vào các câu hỏi cũ hơn hoặc câu trả lời của AI nếu chúng không liên quan trực tiếp đến "Câu hỏi mới".
                9.  Nếu "Lịch sử" không chứa thông tin địa điểm, thời gian, hoặc chủ đề rõ ràng, giữ nguyên "Câu hỏi mới" mà không suy diễn thêm.

                BẮT BUỘC: Output phải là JSON hợp lệ duy nhất, không được chứa ký tự hoặc giải thích ngoài cặp dấu json.

                ---
                VÍ DỤ (Làm rõ QUY TẮC "LẶP LẠI"):
                ---
                Lịch sử: []
                Câu hỏi mới: "Hãy lên kế hoạch du lịch tại cần giờ"
                OUTPUT:
                {{
                    "standalone_question": "Hãy lên kế hoạch du lịch tại cần giờ"
                }}
                ---
                Lịch sử: []
                Câu hỏi mới: "Các món ăn ngon ở Hà Nội là gì?"
                OUTPUT:
                {{
                    "standalone_question": "Các món ăn ngon ở Hà Nội là gì?"
                }}
                ---
                Lịch sử: [Human: "Tôi muốn đi du lịch TPHCM"]
                Câu hỏi mới: "Hãy cho tôi danh sách các món ăn ngon tại hồ chí minh"
                OUTPUT:
                {{
                    "standalone_question": "Hãy cho tôi danh sách các món ăn ngon tại hồ chí minh"
                }}
                ---
                Lịch sử: []
                Câu hỏi mới: "Tại quận 4, con đường nào nổi tiếng với các quán hải sản nướng và món ốc đặc sản của TPHCM"
                OUTPUT:
                {{
                    "standalone_question": "Tại quận 4, con đường nào nổi tiếng với các quán hải sản nướng và món ốc đặc sản của TPHCM"
                }}
                ---

                VÍ DỤ (Làm rõ QUY TẮC "VIẾT LẠI"):
                ---
                Lịch sử: [Human: "cho tôi các món ăn nổi tiếng ở tphcm"\nAI: "TPHCM có món A, B, C..."]
                Câu hỏi mới: "Tôi muốn đi du lịch 3 ngày 2 đêm"
                OUTPUT:
                {{
                    "standalone_question": "Tôi muốn đi du lịch 3 ngày 2 đêm ở tphcm"
                }}
                ---
                Lịch sử: [Human: "Tôi muốn đi du lịch Thành phố Hồ Chí Minh"]
                Câu hỏi mới: "Ở đó có gì chơi?"
                OUTPUT:
                {{
                    "standalone_question": "Ở Thành phố Hồ Chí Minh có gì chơi?"
                }}
                ---
                Lịch sử: [Human: "Tôi muốn đi Hà Nội"]
                Câu hỏi mới: "lên kế hoạch du lịch 2 ngày"
                OUTPUT:
                {{
                    "standalone_question": "Lên kế hoạch du lịch 2 ngày ở Hà Nội"
                }}
                ---
                Lịch sử: [Human: "Cầu Rồng đẹp thật!"\nAI: "Đúng vậy, Cầu Rồng phun lửa vào cuối tuần."]
                Câu hỏi mới: "Mấy giờ vậy?"
                OUTPUT:
                {{
                    "standalone_question": "Cầu Rồng phun lửa vào mấy giờ?"
                }}
                ---

                Bây giờ, hãy thực hiện nhiệm vụ cho Lịch sử và Câu hỏi mới dưới đây:
            """

            history_lines = []
            for msg in chat_history:
                role = "Human" if msg.type == 'human' else "AI"
                history_lines.append(f"{role}: \"{msg}\"")
            
            chat_history_str = "\n".join(history_lines)
            if chat_history_str:
                chat_history_str = f"[{chat_history_str}]"
            else:
                chat_history_str = "[]"

            print('\n---------------------Formatted Chat History:---------------------\n', chat_history_str)

            # Create prompt template for contextualizing question
            contextualize_q_prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", contextualize_q_system_prompt),
                    ("human", "Lịch sử: {chat_history}\nCâu hỏi mới: {input}")
                ]
            )

            # Create the chain for generating standalone question
            contextualize_q_chain = contextualize_q_prompt | llm_create_standalone_question() | JsonOutputParser()

            standalone_question = await contextualize_q_chain.ainvoke(
                {
                    "input": question,
                    "chat_history": chat_history_str
                }
            )

            return standalone_question
        except Exception as e:
            print(f"Error in building standalone question: {e}")
            return {"standalone_question": question}
        
    
    async def classify_query_for_schedule(query: str):
        try:
            llm = llm_classify()

            system = """You are a specialized query classifier assistant.

                Your SOLE task is to analyze the user's "Question" to determine two things:
                1.  **Topic**: Is the question an explicit request for planning/scheduling?
                2.  **Location**: Is the location context one of the 3 allowed cities?

                ### CLASSIFICATION RULES:

                1.  **Topic**
                    -   You are ONLY allowed to identify one topic: "Plan".
                    -   A question is "Plan" IF AND ONLY IF it explicitly asks to create an **itinerary**, **schedule**, **tour**, or a **multi-day plan** (e.g., "2-day plan", "3 days 2 nights itinerary", "make a 1-day tour").
                    -   If it is a "Plan", output: `"Topic": "Plan"`
                    -   If the question just asks for options (e.g., "what to do in the morning?"), asks about dining, or anything else that is NOT an itinerary, it is **NOT** a "Plan". In this case, output: `"Topic": null`

                2.  **Location**
                    -   Represents only the main city context.
                    -   Allowed values: ['Hà Nội', 'Thành phố Hồ Chí Minh', 'Đà Nẵng'].
                    -   If one of these cities is **explicitly mentioned**, output that city name. Example: `"Location": "Hà Nội"`
                    -   If **no allowed city** is mentioned (or only a district/small area like "Cần Giờ", "Quận 5" is mentioned), you MUST output: `"Location": null`
                    -   Do NOT return a list. Only return a single string or `null`.

                3.  **Output Format**
                    -   Output ONLY valid JSON.
                    -   Structure:
                        ```jsonW
                        {{
                        "Topic": "Plan" | null,
                        "Location": "Hà Nội" | "Thành phố Hồ Chí Minh" | "Đà Nẵng" | null
                        }}
                        ```
                    -   No explanations.

                ---
                ### EXAMPLES

                Question: "Lên kế hoạch du lịch 2 ngày ở Hà Nội"
                Output:
                {{"Topic": "Plan", "Location": "Hà Nội"}}

                Question: "Tôi muốn đi Cần Giờ 1 ngày"
                Output:
                {{"Topic": "Plan", "Location": null}}

                Question: "Gợi ý lịch trình 3 ngày 2 đêm tại Đà Nẵng"
                Output:
                {{"Topic": "Plan", "Location": "Đà Nẵng"}}

                Question: "Những nơi vui chơi ở Sài Gòn buổi tối?"
                Output:
                {{"Topic": null, "Location": "Thành phố Hồ Chí Minh"}}

                Question: "Khách sạn nào gần chợ Bến Thành?"
                Output:
                {{"Topic": null, "Location": null}}

                Question: "Xin chào!"
                Output:
                {{"Topic": null, "Location": null}}

                Question: "Bánh mì Hà Nội được bán ở đâu ở Hồ Chí Minh?"
                Output:
                {{"Topic": null, "Location": "Thành phố Hồ Chí Minh"}}
                ---

                Now classify the following Question:
            """

            prompt = ChatPromptTemplate.from_messages([
                ("system", system),
                ("user", "Question: {question}")
            ])

            classification_chain = prompt | llm | JsonOutputParser()

            print(f"\n---------------------Classifying query for schedule: {query}---------------------\n")
            classification = await classification_chain.ainvoke({"question": query})

            raw_topic = classification.get("Topic")
            raw_location = classification.get("Location")

            final_topic = None
            if raw_topic == "Plan":
                final_topic = "Plan"

            final_location = None
            allowed_cities = ["Hà Nội", "Thành phố Hồ Chí Minh", "Đà Nẵng"]
            if raw_location in allowed_cities:
                final_location = raw_location
                
            # Tạo kết quả cuối cùng, sạch sẽ
            final_result = {
                "Topic": final_topic,
                "Location": final_location
            }
            
            print(f"\n---------------------Classification result: {final_result}---------------------\n")

            return final_result

        except Exception as e:
            print(f"Query classification error: {e}")
            return {"Topic": None, "Location": None}