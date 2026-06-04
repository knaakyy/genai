# 📚 영어 원서 AI 회화 학습 시스템

**제출자:** 김나경 | **학번/소속:** 2114278 / 컴퓨터과학과

## 📌 프로젝트 개요
Project Gutenberg의 영어 원서에서 대화문을 자동 추출하고,
**섀도잉 · 필사 · 롤플레잉** 세 가지 모드로 AI 회화 학습을 제공하는 시스템입니다.

---

## 🛠️ 사용 기술
| 기술 | 역할 |
|------|------|
| OpenAI GPT-4o-mini | 대화문 추출, 난이도 분류, 롤플레잉 응답, 피드백 생성 |
| OpenAI Whisper | 사용자 음성 → 텍스트 변환 (STT) |
| Google Cloud TTS | 원어민 음성 생성 (다양한 억양 지원) |
| Streamlit | 웹 UI |
| Project Gutenberg API | 원서 데이터 수집 |

---

## 🚀 설치 및 실행

### 1. 패키지 설치
```bash
pip install -r requirements.txt
```

### 2. API 키 설정
`.env.example`을 `.env`로 복사 후 키를 입력하세요:
```bash
cp .env.example .env
```
```
OPENAI_API_KEY=sk-...
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
```

### 3. 앱 실행
```bash
streamlit run app.py
```
브라우저에서 `http://localhost:8501` 접속

---

## 📖 사용 방법

### Step 1 — 원서 불러오기
- 인기 도서 목록에서 선택하거나 직접 제목/저자로 검색
- 원하는 챕터를 선택 후 **"GPT로 대화문 추출"** 클릭

### Step 2 — 대화문 목록 확인
- 난이도(Beginner/Intermediate/Advanced), 화자, 키워드로 필터링
- 핵심 표현과 현대 영어 변환 확인

### Step 3 — 학습 모드 선택
| 모드 | 학습 효과 |
|------|-----------|
| 🎧 섀도잉 | 음성 듣기 → 따라 말하기 → AI 발음 피드백 |
| ✍️ 필사 | 받아쓰기(Dictation) 또는 영작(Translation) |
| 🎭 롤플레잉 | 텍스트/음성으로 AI 캐릭터와 실시간 대화 |

---

## 📁 파일 구조
```
ai_conversation_app/
├── app.py                  # 메인 Streamlit 앱
├── gutenberg.py            # Project Gutenberg 데이터 수집/전처리
├── dialogue_extractor.py   # GPT 대화문 추출 & 롤플레잉
├── tts_handler.py          # Google Cloud TTS
├── stt_handler.py          # OpenAI Whisper STT
├── requirements.txt
├── .env.example
└── README.md
```

---

## ⚠️ 주의사항 & 제한사항
- **저작권:** Project Gutenberg 도서(퍼블릭 도메인)만 사용 가능
- **Google TTS:** credentials 없이도 STT/GPT 기능은 정상 작동
- **API 비용:** GPT-4o-mini 기준 추출 1회 ≈ $0.002 내외

## 🔮 향후 개선 계획
- 전자도서관(밀리의 서재) API 연동
- 감정 태그 지원 고급 TTS 적용
- 고전→현대 영어 자동 변환 기능 강화
- 학습 이력 DB 저장 및 시각화 대시보드
