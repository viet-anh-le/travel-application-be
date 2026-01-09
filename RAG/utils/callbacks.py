import asyncio
from typing import Any, Dict
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.agents import AgentAction

class AgentStatusCallbackHandler(BaseCallbackHandler):
    def __init__(self, queue: asyncio.Queue):
        self.queue = queue
        self.loop = asyncio.get_event_loop()

    def _put_in_queue(self, data: dict):
        self.loop.call_soon_threadsafe(self.queue.put_nowait, data)

    def on_agent_action(self, action: AgentAction, **kwargs: Any) -> Any:
        """Khi Agent quyết định dùng một Tool"""
        tool_name = action.tool
        tool_input = action.tool_input
        self._put_in_queue({
            "type": "thought",
            "data": f"Đang sử dụng công cụ: {tool_name}..."
        })

    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs: Any) -> Any:
        """Khi Tool bắt đầu chạy thực sự"""
        pass

    def on_tool_end(self, output: str, **kwargs: Any) -> Any:
        """Khi Tool chạy xong"""
        pass

    def on_chain_error(self, error: BaseException, **kwargs: Any) -> Any:
        """Khi gặp lỗi"""
        self._put_in_queue({"type": "error", "data": str(error)})