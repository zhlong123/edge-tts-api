import edge_tts

OPENAI_VOICE_ALIAS = {
    "alloy": "en-US-JennyNeural",
    "echo": "en-US-GuyNeural",
    "fable": "en-GB-SoniaNeural",
    "onyx": "zh-CN-YunyangNeural",
    "nova": "zh-CN-XiaoxiaoNeural",
    "shimmer": "zh-CN-XiaoyiNeural",
}


def resolve_voice(voice: str, default_voice: str) -> str:
    if not voice:
        return default_voice
    return OPENAI_VOICE_ALIAS.get(voice, voice)


def speed_to_rate(speed: float) -> str:
    clamped = max(0.25, min(4.0, float(speed)))
    pct = int(round((clamped - 1.0) * 100))
    return f"{pct:+d}%"


async def synthesize(text: str, voice: str, speed: float = 1.0) -> bytes:
    rate = speed_to_rate(speed)
    communicate = edge_tts.Communicate(text, voice=voice, rate=rate)
    audio_bytes = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_bytes += chunk["data"]
    if not audio_bytes:
        raise RuntimeError("Edge TTS 未返回音频数据")
    return audio_bytes


async def list_all_voices() -> list[dict]:
    voices = await edge_tts.list_voices()
    return sorted(voices, key=lambda item: item.get("ShortName", ""))
