from contextlib import asynccontextmanager

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field

from app.auth import verify_api_key
from app.config import load_settings, load_voice_presets
from app.edge_engine import list_all_voices, resolve_voice, synthesize


class SpeechRequest(BaseModel):
    model: str = "tts-1"
    input: str
    voice: str | None = None
    response_format: str = "mp3"
    speed: float = Field(default=1.0, ge=0.25, le=4.0)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="Edge TTS API",
    description="OpenAI 兼容的 Edge TTS 语音合成服务",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    settings = load_settings()
    return {
        "status": "ok",
        "default_voice": settings.get("default_voice"),
        "port": settings.get("port"),
    }


@app.get("/v1/models")
async def list_models():
    return {
        "object": "list",
        "data": [
            {"id": "tts-1", "object": "model", "owned_by": "edge-tts"},
            {"id": "tts-1-hd", "object": "model", "owned_by": "edge-tts"},
        ],
    }


@app.get("/v1/voices/presets")
async def voice_presets():
    return {"presets": load_voice_presets()}


@app.get("/v1/voices")
async def voices():
    try:
        all_voices = await list_all_voices()
        return {"voices": all_voices}
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail={"error": {"message": f"获取音色列表失败: {exc}"}},
        ) from exc


@app.post("/v1/audio/speech")
async def create_speech(
    body: SpeechRequest,
    authorization: str | None = Header(default=None),
):
    verify_api_key(authorization)

    text = (body.input or "").strip()
    if not text:
        raise HTTPException(
            status_code=400,
            detail={"error": {"message": "input 不能为空"}},
        )

    response_format = (body.response_format or "mp3").lower()
    if response_format != "mp3":
        raise HTTPException(
            status_code=400,
            detail={"error": {"message": "当前仅支持 response_format=mp3"}},
        )

    settings = load_settings()
    voice = resolve_voice(body.voice or "", settings.get("default_voice", "zh-CN-XiaoxiaoNeural"))

    try:
        audio = await synthesize(text, voice, body.speed)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail={"error": {"message": f"Edge TTS 合成失败: {exc}"}},
        ) from exc

    return Response(content=audio, media_type="audio/mpeg")


def run():
    import uvicorn

    settings = load_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.get("host", "0.0.0.0"),
        port=int(settings.get("port", 9880)),
        reload=False,
    )


if __name__ == "__main__":
    run()
