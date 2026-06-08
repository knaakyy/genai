"""
영어 원서 대화문 추출 기반 AI 회화 학습 시스템
Author: 김나경 (2114278 / 컴퓨터과학과)
"""

import streamlit as st
import os
import json
import time
import traceback
from dotenv import load_dotenv

load_dotenv()

# ── 페이지 설정 ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="📚 영어 원서 AI 회화 학습",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS 커스터마이징 ──────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem; font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-title { font-size: 1rem; color: #6c757d; margin-bottom: 2rem; }
    .dialogue-card {
        background: #f8f9ff; border-left: 4px solid #667eea;
        border-radius: 8px; padding: 1rem 1.2rem; margin: 0.5rem 0;
    }
    .speaker-name { font-weight: 700; color: #667eea; font-size: 0.95rem; }
    .dialogue-line { font-size: 1.05rem; color: #2d3436; margin: 0.3rem 0; }
    .modern-eq { font-size: 0.88rem; color: #636e72; font-style: italic; }
    .badge-beginner    { background:#d4edda; color:#155724; padding:2px 10px; border-radius:12px; font-size:0.8rem; }
    .badge-intermediate{ background:#fff3cd; color:#856404; padding:2px 10px; border-radius:12px; font-size:0.8rem; }
    .badge-advanced    { background:#f8d7da; color:#721c24; padding:2px 10px; border-radius:12px; font-size:0.8rem; }
    .score-box {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white; border-radius: 12px; padding: 1.5rem; text-align: center;
    }
    .score-num { font-size: 3rem; font-weight: 800; }
    .mode-card {
        border: 2px solid #e9ecef; border-radius: 12px; padding: 1.5rem;
        text-align: center; cursor: pointer; transition: all 0.2s;
    }
    .mode-card:hover { border-color: #667eea; background: #f8f9ff; }
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white; border: none; border-radius: 8px; font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


# ── 세션 상태 초기화 ─────────────────────────────────────────────────────────
def init_session():
    defaults = {
        "openai_key": os.getenv("OPENAI_API_KEY", ""),
        "google_creds": os.getenv("GOOGLE_APPLICATION_CREDENTIALS", ""),
        "api_ready": False,
        "book_text": "",
        "book_title": "",
        "chapters": {},
        "dialogues": [],
        "filtered_dialogues": [],
        "roleplay_setup": None,
        "roleplay_messages": [],
        "current_mode": None,
        "shadowing_idx": 0,
        "transcription_idx": 0,
        "transcription_input": "",
        "feedback_history": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()


# ── 사이드바: API 설정 ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ 설정")
    st.markdown("---")

    with st.expander("🔑 API 키 설정", expanded=not st.session_state.api_ready):
        oai_key = st.text_input("OpenAI API Key", value=st.session_state.openai_key,
                                type="password", placeholder="sk-...")
        g_creds = st.text_input("Google Credentials Path", value=st.session_state.google_creds,
                                placeholder="/path/to/credentials.json")

        if st.button("✅ API 연결"):
            if oai_key:
                try:
                    import dialogue_extractor as de
                    de.init_client(oai_key)
                    import stt_handler as stt
                    stt.init_whisper(oai_key)
                    st.session_state.openai_key = oai_key
                    st.session_state.api_ready = True
                    st.success("OpenAI 연결 완료!")
                except Exception as e:
                    st.error(f"OpenAI 연결 실패: {e}")
            if g_creds and os.path.exists(g_creds):
                try:
                    import tts_handler as tts
                    tts.init_tts(g_creds)
                    st.session_state.google_creds = g_creds
                    st.success("Google TTS 연결 완료!")
                except Exception as e:
                    st.warning(f"Google TTS 연결 실패: {e}")

    if st.session_state.api_ready:
        st.success("🟢 OpenAI 연결됨")

    st.markdown("---")
    st.markdown("## 🎙️ 음성 설정")
    voice_choice = st.selectbox("TTS 음성", [
        "American Female (WaveNet)", "American Male (WaveNet)",
        "British Female (WaveNet)", "British Male (WaveNet)",
        "Australian Female (WaveNet)",
        "American Female (Standard)", "American Male (Standard)",
    ])
    speech_rate = st.slider("재생 속도", 0.5, 1.5, 1.0, 0.1)

    st.markdown("---")
    st.markdown("## 📊 학습 현황")
    total = len(st.session_state.dialogues)
    fb_count = len(st.session_state.feedback_history)
    if total:
        avg_score = (sum(f.get("accuracy_score", 0) for f in st.session_state.feedback_history) / fb_count
                     if fb_count else 0)
        st.metric("추출된 대화문", total)
        st.metric("연습 횟수", fb_count)
        if fb_count:
            st.metric("평균 정확도", f"{avg_score:.0f}점")
    else:
        st.info("원서를 불러오면 통계가 표시됩니다.")


# ── 메인 화면 ─────────────────────────────────────────────────────────────────
st.markdown('<p class="main-title">📚 영어 원서 AI 회화 학습 시스템</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Project Gutenberg 원서에서 대화문을 추출하고 섀도잉·필사·롤플레잉으로 회화를 연습하세요</p>',
            unsafe_allow_html=True)

# ── 탭 구성 ──────────────────────────────────────────────────────────────────
tab_book, tab_dialogues, tab_shadow, tab_trans, tab_roleplay = st.tabs([
    "📖 원서 불러오기", "💬 대화문 목록", "🎧 섀도잉", "✍️ 필사", "🎭 롤플레잉"
])


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: 원서 불러오기
# ═══════════════════════════════════════════════════════════════════════════════
with tab_book:
    st.markdown("### 원서 선택")

    st.markdown("#### 📋 인기 도서 목록")

    import gutenberg as gb
    book_options = list(gb.POPULAR_BOOKS.keys())
    selected_book = st.selectbox(
        "도서를 선택하세요",
        ["-- 선택하세요 --"] + book_options
    )

    if st.button("📥 선택한 도서 불러오기") and selected_book != "-- 선택하세요 --":
        book_id = gb.POPULAR_BOOKS[selected_book]

        with st.spinner(f"'{selected_book}' 다운로드 중..."):
            raw = gb.fetch_book_text(book_id)

            if raw:
                processed = gb.preprocess_text(raw)
                st.session_state.book_text = processed
                st.session_state.book_title = selected_book
                st.session_state.chapters = gb.extract_chapters(processed)
                st.session_state.dialogues = []

                st.success(
                    f"✅ '{selected_book}' 로드 완료! ({len(processed):,}자)"
                )
            else:
                st.error("❌ 도서를 불러오지 못했습니다. 잠시 후 다시 시도하세요.")

    # 챕터 선택 & 대화문 추출
    if st.session_state.book_text:
        st.markdown("---")
        st.markdown(f"### 📑 **{st.session_state.book_title}** — 챕터 선택 및 대화문 추출")

        chapters = st.session_state.chapters
        chapter_names = list(chapters.keys())
        selected_chapters = st.multiselect("분석할 챕터를 선택하세요 (복수 선택 가능)", chapter_names,
                                           default=chapter_names[:2] if len(chapter_names) >= 2 else chapter_names)

        col_a, col_b = st.columns([2, 1])
        with col_a:
            if st.button("🤖 GPT로 대화문 추출", disabled=not st.session_state.api_ready):
                combined = "\n\n".join(chapters[c][:3000] for c in selected_chapters)
                import dialogue_extractor as de
                with st.spinner("GPT가 대화문을 분석 중입니다..."):
                    try:
                        dialogues = de.extract_dialogues(combined)
                        st.session_state.dialogues = dialogues
                        st.session_state.filtered_dialogues = dialogues
                        st.success(f"✅ {len(dialogues)}개의 대화문을 추출했습니다!")
                    except Exception as e:
                        st.error(traceback.format_exc())

        with col_b:
            if not st.session_state.api_ready:
                st.warning("⚠️ 사이드바에서 API 키를 먼저 연결하세요.")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2: 대화문 목록
# ═══════════════════════════════════════════════════════════════════════════════
with tab_dialogues:
    if not st.session_state.dialogues:
        st.info("📖 먼저 '원서 불러오기' 탭에서 대화문을 추출해주세요.")
    else:
        dialogues = st.session_state.dialogues
        st.markdown(f"### 💬 추출된 대화문 ({len(dialogues)}개)")

        # 필터
        col1, col2, col3 = st.columns(3)
        with col1:
            diff_filter = st.multiselect("난이도 필터",
                ["Beginner", "Intermediate", "Advanced"],
                default=["Beginner", "Intermediate", "Advanced"])
        with col2:
            speakers = list({d.get("speaker", "Unknown") for d in dialogues})
            speaker_filter = st.multiselect("화자 필터", ["전체"] + speakers, default=["전체"])
        with col3:
            search_kw = st.text_input("🔍 키워드 검색", placeholder="표현 검색...")

        filtered = [d for d in dialogues
                    if d.get("difficulty", "Intermediate") in diff_filter
                    and (speaker_filter == ["전체"] or d.get("speaker") in speaker_filter)
                    and (not search_kw or search_kw.lower() in d.get("line", "").lower())]
        st.session_state.filtered_dialogues = filtered

        st.caption(f"필터 결과: {len(filtered)}개")
        st.markdown("---")

        for i, d in enumerate(filtered):
            diff = d.get("difficulty", "Intermediate")
            badge_class = {"Beginner": "badge-beginner",
                           "Intermediate": "badge-intermediate",
                           "Advanced": "badge-advanced"}.get(diff, "badge-intermediate")
            with st.container():
                st.markdown(f"""
                <div class="dialogue-card">
                    <span class="speaker-name">🗣 {d.get('speaker','Unknown')}</span>
                    &nbsp;<span class="{badge_class}">{diff}</span>
                    <p class="dialogue-line">"{d.get('line','')}"</p>
                    <p class="modern-eq">💡 {d.get('modern_equivalent','')}</p>
                    <p style="font-size:0.82rem;color:#74b9ff;">
                        🌟 Key Expressions: {' · '.join(d.get('key_expressions', []))}
                    </p>
                    <p style="font-size:0.82rem;color:#b2bec3;">📍 {d.get('context','')}</p>
                </div>
                """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3: 섀도잉 모드
# ═══════════════════════════════════════════════════════════════════════════════
with tab_shadow:
    st.markdown("### 🎧 섀도잉 모드")
    st.markdown("원어민 음성을 듣고, 마이크로 따라 말한 뒤 AI 피드백을 받으세요.")

    if not st.session_state.dialogues:
        st.info("📖 먼저 원서에서 대화문을 추출해주세요.")
    else:
        dialogues = st.session_state.filtered_dialogues or st.session_state.dialogues
        idx = st.session_state.shadowing_idx

        col_nav1, col_info, col_nav2 = st.columns([1, 4, 1])
        with col_nav1:
            if st.button("⬅️ 이전") and idx > 0:
                st.session_state.shadowing_idx -= 1
                st.rerun()
        with col_info:
            st.markdown(f"**{idx+1} / {len(dialogues)}**")
        with col_nav2:
            if st.button("다음 ➡️") and idx < len(dialogues) - 1:
                st.session_state.shadowing_idx += 1
                st.rerun()

        d = dialogues[idx]
        diff = d.get("difficulty", "Intermediate")
        badge_class = {"Beginner":"badge-beginner","Intermediate":"badge-intermediate","Advanced":"badge-advanced"}.get(diff,"badge-intermediate")

        st.markdown(f"""
        <div class="dialogue-card">
            <span class="speaker-name">🗣 {d.get('speaker','Unknown')}</span>
            &nbsp;<span class="{badge_class}">{diff}</span>
            <p class="dialogue-line" style="font-size:1.3rem; font-weight:600;">"{d.get('line','')}"</p>
            <p class="modern-eq">💡 현대 표현: {d.get('modern_equivalent','')}</p>
            <p style="font-size:0.85rem;color:#74b9ff;">📍 {d.get('context','')}</p>
        </div>
        """, unsafe_allow_html=True)

        # TTS 재생
        col_tts1, col_tts2 = st.columns([1, 1])
        with col_tts1:
            if st.button("🔊 원어민 음성 듣기"):
                try:
                    import tts_handler as tts
                    audio = tts.text_to_speech(d["line"], voice_choice, speech_rate)
                    st.audio(audio, format="audio/mp3")
                except Exception as e:
                    st.warning(f"TTS 오류 (Google Credentials 확인): {e}")
                    st.info("💡 대화문을 보며 소리 내어 읽어보세요!")
        with col_tts2:
            slow_rate = max(0.5, speech_rate - 0.3)
            if st.button(f"🐢 천천히 듣기 ({slow_rate}x)"):
                try:
                    import tts_handler as tts
                    audio = tts.text_to_speech(d["line"], voice_choice, slow_rate)
                    st.audio(audio, format="audio/mp3")
                except Exception as e:
                    st.warning(f"TTS 오류: {e}")

        st.markdown("---")
        st.markdown("#### 🎤 따라 말하기")

        # 마이크 녹음
        audio_input = st.audio_input("마이크로 녹음하세요 (버튼 클릭 후 말하기)")

        if audio_input is not None:
            audio_bytes = audio_input.read()
            with st.spinner("음성 인식 중..."):
                try:
                    import stt_handler as stt
                    user_text = stt.transcribe_audio(audio_bytes, "wav")
                    st.success(f"🗣 인식된 텍스트: **{user_text}**")

                    # GPT 피드백
                    import dialogue_extractor as de
                    feedback = de.evaluate_response(d["line"], user_text)
                    st.session_state.feedback_history.append(feedback)

                    score = feedback.get("accuracy_score", 0)
                    col_s1, col_s2 = st.columns([1, 2])
                    with col_s1:
                        color = "#00b894" if score >= 80 else "#fdcb6e" if score >= 60 else "#e17055"
                        st.markdown(f"""
                        <div class="score-box" style="background:{color};">
                            <div class="score-num">{score}</div>
                            <div>/ 100</div>
                        </div>""", unsafe_allow_html=True)
                    with col_s2:
                        if feedback.get("pronunciation_issues"):
                            st.markdown("**🔤 발음 주의 단어:**")
                            st.markdown(", ".join(f"`{w}`" for w in feedback["pronunciation_issues"]))
                        st.markdown(f"**💬 피드백:** {feedback.get('fluency_feedback','')}")
                        if feedback.get("grammar_note"):
                            st.markdown(f"**📝 문법:** {feedback['grammar_note']}")
                        st.markdown(f"**🌟 {feedback.get('encouragement','')}**")
                except Exception as e:
                    st.error(f"음성 인식 실패: {e}")
                    st.info("💡 직접 텍스트로 입력해 연습할 수 있습니다.")

        # 텍스트 입력으로 연습 (STT 없을 때)
        with st.expander("⌨️ 텍스트로 연습 (STT 없을 때)"):
            manual_input = st.text_input("따라 말한 내용을 입력하세요", placeholder=d.get("line",""))
            if st.button("📊 피드백 받기") and manual_input and st.session_state.api_ready:
                with st.spinner("분석 중..."):
                    import dialogue_extractor as de
                    feedback = de.evaluate_response(d["line"], manual_input)
                    st.session_state.feedback_history.append(feedback)
                    st.json(feedback)

        # Key expressions 학습
        if d.get("key_expressions"):
            with st.expander("🌟 핵심 표현 보기"):
                for expr in d["key_expressions"]:
                    st.markdown(f"- **{expr}**")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4: 필사 모드
# ═══════════════════════════════════════════════════════════════════════════════
with tab_trans:
    st.markdown("### ✍️ 필사 모드")
    st.markdown("음성을 듣고 들리는 내용을 받아 적거나, 한국어 힌트를 보고 영어로 작성해 보세요.")

    if not st.session_state.dialogues:
        st.info("📖 먼저 원서에서 대화문을 추출해주세요.")
    else:
        dialogues = st.session_state.filtered_dialogues or st.session_state.dialogues
        idx = st.session_state.transcription_idx

        col1, col2 = st.columns([1, 1])
        with col1:
            mode_type = st.radio("필사 유형 선택", ["🎧 받아쓰기 (Dictation)", "🇰🇷 → 🇺🇸 영작 (Translation)"])
        with col2:
            t_idx_nav = st.selectbox("대화문 선택", range(len(dialogues)),
                                     format_func=lambda i: f"#{i+1} {dialogues[i].get('speaker',''[:15])}: {dialogues[i].get('line','')[:30]}...")
            st.session_state.transcription_idx = t_idx_nav

        d = dialogues[st.session_state.transcription_idx]
        st.markdown("---")

        if "받아쓰기" in mode_type:
            st.markdown("#### 🎧 음성을 듣고 받아 적으세요")
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("🔊 음성 재생"):
                    try:
                        import tts_handler as tts
                        audio = tts.text_to_speech(d["line"], voice_choice, speech_rate)
                        st.audio(audio, format="audio/mp3")
                    except Exception as e:
                        st.info(f"TTS 오류: {e}")
            with col_b:
                if st.button("🐢 느리게 재생"):
                    try:
                        import tts_handler as tts
                        audio = tts.text_to_speech(d["line"], voice_choice, max(0.5, speech_rate - 0.3))
                        st.audio(audio, format="audio/mp3")
                    except Exception as e:
                        st.info(f"TTS 오류: {e}")
        else:
            st.markdown("#### 🇰🇷 힌트를 보고 영어로 작성하세요")
            if st.session_state.api_ready:
                if st.button("💡 한국어 힌트 보기"):
                    import dialogue_extractor as de
                    with st.spinner("번역 중..."):
                        try:
                            resp = de._client.chat.completions.create(
                                model="gpt-4o-mini",
                                messages=[{"role":"user","content":f"Translate to Korean naturally: {d['line']}"}]
                            )
                            st.info(f"**한국어:** {resp.choices[0].message.content}")
                        except Exception as e:
                            st.warning(f"번역 실패: {e}")

        user_answer = st.text_area("📝 작성하세요", height=80, placeholder="영어로 작성하세요...",
                                   key=f"trans_{st.session_state.transcription_idx}")

        if st.button("✅ 정답 확인"):
            if user_answer.strip():
                correct = d["line"]
                st.markdown("**📋 정답:**")
                st.success(f'"{correct}"')

                # 간단한 단어 비교
                user_words = set(user_answer.lower().split())
                correct_words = set(correct.lower().split())
                accuracy = len(user_words & correct_words) / len(correct_words) * 100 if correct_words else 0
                st.metric("단어 일치율", f"{accuracy:.0f}%")

                # GPT 상세 피드백
                if st.session_state.api_ready:
                    with st.spinner("GPT 피드백 생성 중..."):
                        import dialogue_extractor as de
                        feedback = de.evaluate_response(correct, user_answer)
                        st.markdown(f"**💬 AI 피드백:** {feedback.get('fluency_feedback','')}")
                        if feedback.get("grammar_note"):
                            st.warning(f"📝 문법 교정: {feedback['grammar_note']}")
                        st.markdown(f"🌟 {feedback.get('encouragement','')}")
            else:
                st.warning("먼저 내용을 작성하세요.")

        with st.expander("👁️ 현대 영어 표현 보기"):
            st.markdown(f"**원문:** {d.get('line','')}")
            st.markdown(f"**현대 표현:** {d.get('modern_equivalent','')}")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5: 롤플레잉 모드
# ═══════════════════════════════════════════════════════════════════════════════
with tab_roleplay:
    st.markdown("### 🎭 롤플레잉 모드")
    st.markdown("원서의 장면을 바탕으로 AI와 실시간 영어 대화를 나눠보세요.")

    if not st.session_state.dialogues:
        st.info("📖 먼저 원서에서 대화문을 추출해주세요.")
    elif not st.session_state.api_ready:
        st.warning("⚠️ 사이드바에서 API 키를 먼저 연결해주세요.")
    else:
        if st.session_state.roleplay_setup is None:
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown("#### 롤플레잉 장면 설정")
                start_idx = st.slider("대화문 시작 위치", 0, max(0, len(st.session_state.dialogues)-5), 0)
                n_dialogues = st.slider("사용할 대화문 수", 3, 10, 5)

            with col2:
                st.markdown("#### 학습 목표")
                goal = st.multiselect("이번 롤플레잉 목표", [
                    "자연스러운 인사 표현", "감정 표현", "의견 제시",
                    "질문하기", "설득하기", "거절하기"
                ])

            if st.button("🎬 롤플레잉 시작", use_container_width=True):
                selected_dialogues = st.session_state.dialogues[start_idx:start_idx+n_dialogues]
                with st.spinner("AI가 롤플레잉 시나리오를 준비 중입니다..."):
                    import dialogue_extractor as de
                    try:
                        setup = de.generate_roleplay_setup(selected_dialogues)
                        st.session_state.roleplay_setup = setup
                        st.session_state.roleplay_messages = []
                        st.rerun()
                    except Exception as e:
                        st.error(f"시나리오 생성 실패: {e}")
        else:
            setup = st.session_state.roleplay_setup

            # 시나리오 표시
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#667eea,#764ba2);color:white;
                        border-radius:12px;padding:1.2rem;margin-bottom:1rem;">
                <h4 style="margin:0;">🎬 시나리오</h4>
                <p style="margin:0.5rem 0;">{setup.get('scenario','')}</p>
                <p style="margin:0;"><b>당신의 역할:</b> {setup.get('user_role','')}</p>
                <p style="margin:0;"><b>AI 역할:</b> {', '.join(setup.get('ai_roles',[]))}</p>
            </div>
            """, unsafe_allow_html=True)

            # 핵심 표현 힌트
            if setup.get("vocabulary_tips"):
                with st.expander("💡 이번 장면 핵심 표현"):
                    for tip in setup["vocabulary_tips"]:
                        st.markdown(f"- {tip}")

            # 대화 기록
            st.markdown("#### 💬 대화")
            chat_container = st.container()
            with chat_container:
                # 첫 AI 메시지
                if not st.session_state.roleplay_messages:
                    opening = setup.get("opening_line", "Let's begin our scene!")
                    ai_role = ', '.join(setup.get('ai_roles', ['AI']))
                    st.session_state.roleplay_messages.append({
                        "role": "assistant", "content": opening, "display_role": ai_role
                    })

                for msg in st.session_state.roleplay_messages:
                    if msg["role"] == "assistant":
                        with st.chat_message("assistant", avatar="🎭"):
                            st.markdown(f"**{msg.get('display_role','AI')}:** {msg['content']}")
                    else:
                        with st.chat_message("user", avatar="👤"):
                            st.markdown(f"**{setup.get('user_role','You')}:** {msg['content']}")

            # 입력 방식 선택
            input_method = st.radio("입력 방식", ["⌨️ 텍스트 입력", "🎤 음성 입력"], horizontal=True)

            if input_method == "⌨️ 텍스트 입력":
                user_msg = st.chat_input("영어로 대화해보세요...")
                if user_msg:
                    st.session_state.roleplay_messages.append({
                        "role": "user", "content": user_msg, "display_role": setup.get("user_role","You")
                    })
                    import dialogue_extractor as de
                    history = [{"role": m["role"], "content": m["content"]}
                               for m in st.session_state.roleplay_messages[:-1]]
                    with st.spinner("AI 응답 생성 중..."):
                        ai_resp = de.chat_roleplay(
                            history, user_msg,
                            setup.get("scenario",""),
                            setup.get("ai_roles",[])
                        )
                    ai_role = ', '.join(setup.get('ai_roles',['AI']))
                    st.session_state.roleplay_messages.append({
                        "role": "assistant", "content": ai_resp, "display_role": ai_role
                    })
                    st.rerun()
            else:
                audio_rp = st.audio_input("🎤 말하기 (클릭 후 녹음)")
                if audio_rp:
                    audio_bytes = audio_rp.read()
                    with st.spinner("음성 인식 중..."):
                        try:
                            import stt_handler as stt
                            user_msg = stt.transcribe_audio(audio_bytes, "wav")
                            st.info(f"🗣 인식: {user_msg}")
                            st.session_state.roleplay_messages.append({
                                "role": "user", "content": user_msg,
                                "display_role": setup.get("user_role","You")
                            })
                            import dialogue_extractor as de
                            history = [{"role": m["role"], "content": m["content"]}
                                       for m in st.session_state.roleplay_messages[:-1]]
                            ai_resp = de.chat_roleplay(
                                history, user_msg,
                                setup.get("scenario",""),
                                setup.get("ai_roles",[])
                            )
                            ai_role = ', '.join(setup.get('ai_roles',['AI']))
                            st.session_state.roleplay_messages.append({
                                "role": "assistant", "content": ai_resp, "display_role": ai_role
                            })
                            st.rerun()
                        except Exception as e:
                            st.error(f"음성 인식 실패: {e}")

            col_end1, col_end2 = st.columns(2)
            with col_end1:
                if st.button("🔄 새 시나리오 시작"):
                    st.session_state.roleplay_setup = None
                    st.session_state.roleplay_messages = []
                    st.rerun()
            with col_end2:
                if st.button("📊 대화 분석"):
                    if len(st.session_state.roleplay_messages) >= 2 and st.session_state.api_ready:
                        user_lines = [m["content"] for m in st.session_state.roleplay_messages if m["role"]=="user"]
                        import dialogue_extractor as de
                        with st.spinner("대화 분석 중..."):
                            try:
                                resp = de._client.chat.completions.create(
                                    model="gpt-4o-mini",
                                    messages=[{
                                        "role":"user",
                                        "content": f"Analyze this English conversation practice. "
                                                   f"Give feedback on: vocabulary usage, grammar, naturalness, "
                                                   f"and suggestions for improvement. "
                                                   f"User's lines: {json.dumps(user_lines)}"
                                    }]
                                )
                                st.markdown("#### 📊 대화 분석 결과")
                                st.markdown(resp.choices[0].message.content)
                            except Exception as e:
                                st.error(f"분석 실패: {e}")
