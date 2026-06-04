"""OpenAI Whisper 기반 음성 인식 모듈"""
import io
import tempfile
import os
from openai import OpenAI

_client = None

def init_whisper(api_key: str):
    global _client
    _client = OpenAI(api_key=api_key)

def transcribe_audio(audio_bytes: bytes, file_ext: str = "wav") -> str:
    """오디오 bytes → 텍스트 변환"""
    if not _client:
        raise RuntimeError("Whisper client not initialized. Call init_whisper() first.")
    with tempfile.NamedTemporaryFile(suffix=f".{file_ext}", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name
    try:
        with open(tmp_path, "rb") as f:
            transcript = _client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                language="en",
            )
        return transcript.text
    finally:
        os.unlink(tmp_path)

def transcribe_file(filepath: str) -> str:
    """파일 경로로 직접 STT"""
    if not _client:
        raise RuntimeError("Whisper client not initialized.")
    with open(filepath, "rb") as f:
        transcript = _client.audio.transcriptions.create(
            model="whisper-1", file=f, language="en"
        )
    return transcript.text
