"""Google Cloud TTS 기반 음성 생성 모듈"""
import os
import io
import base64
from google.cloud import texttospeech

_tts_client = None

VOICE_OPTIONS = {
    "American Female (Standard)":  {"name": "en-US-Standard-C",  "gender": texttospeech.SsmlVoiceGender.FEMALE},
    "American Male (Standard)":    {"name": "en-US-Standard-B",  "gender": texttospeech.SsmlVoiceGender.MALE},
    "American Female (WaveNet)":   {"name": "en-US-Wavenet-F",   "gender": texttospeech.SsmlVoiceGender.FEMALE},
    "American Male (WaveNet)":     {"name": "en-US-Wavenet-D",   "gender": texttospeech.SsmlVoiceGender.MALE},
    "British Female (WaveNet)":    {"name": "en-GB-Wavenet-A",   "gender": texttospeech.SsmlVoiceGender.FEMALE},
    "British Male (WaveNet)":      {"name": "en-GB-Wavenet-B",   "gender": texttospeech.SsmlVoiceGender.MALE},
    "Australian Female (WaveNet)": {"name": "en-AU-Wavenet-C",   "gender": texttospeech.SsmlVoiceGender.FEMALE},
}

def init_tts(credentials_path: str = None):
    global _tts_client
    if credentials_path:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
    _tts_client = texttospeech.TextToSpeechClient()

def text_to_speech(text: str, voice_key: str = "American Female (WaveNet)",
                   speaking_rate: float = 1.0, pitch: float = 0.0) -> bytes:
    """텍스트를 MP3 bytes로 변환"""
    if not _tts_client:
        raise RuntimeError("TTS client not initialized. Call init_tts() first.")
    voice_cfg = VOICE_OPTIONS.get(voice_key, VOICE_OPTIONS["American Female (WaveNet)"])
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US" if "US" in voice_cfg["name"] else
                       "en-GB" if "GB" in voice_cfg["name"] else "en-AU",
        name=voice_cfg["name"],
        ssml_gender=voice_cfg["gender"],
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=speaking_rate,
        pitch=pitch,
    )
    response = _tts_client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )
    return response.audio_content

def audio_bytes_to_b64(audio_bytes: bytes) -> str:
    return base64.b64encode(audio_bytes).decode("utf-8")
