import httpx
from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel

router = APIRouter(prefix="/utils", tags=["Utils"])

TTS_SERVICE_URL = "http://localhost:8001"


class ClientTTSRequest(BaseModel):
    text: str


@router.post("/tts")
async def proxy_tts_request(payload: ClientTTSRequest):
    if not payload.text:
        raise HTTPException(status_code=400, detail="Text is required")

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Gọi sang TTS Server (Port 8001)
            response = await client.post(
                f"{TTS_SERVICE_URL}/synthesize", json={"text": payload.text, "speed": 1.5}
            )

            # Nếu bên kia lỗi
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code, detail=f"TTS Service Error: {response.text}"
                )

            # Trả nguyên cục audio nhận được về cho React Native
            return Response(content=response.content, media_type="audio/wav")

        except httpx.RequestError:
            print("⚠️ TTS Service busy or disconnected")
            return Response(status_code=204)
        except Exception as e:
            print(f"TTS Proxy Error: {e}")
            return Response(status_code=500)
