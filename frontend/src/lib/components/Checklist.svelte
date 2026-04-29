<!--
    Checklist.svelte
    체크리스트 카드형 화면 컴포넌트
    - 상단: 진행률 바 + 문항 번호 (n/20)
    - TTS 재생 속도 슬라이더
    - 문항 카드 (슬라이드 애니메이션)
    - 선택지 4개 (라디오 버튼)
    - 마이크 버튼 (STT 녹음)
    - 이전/다음 버튼
    - 미답변 문항 번호 표시
    - 돌아가기 / 제출 버튼
-->
<script>
    // props: 부모(+page.svelte)에서 전달받는 데이터와 콜백
    let {
        selectedSession,           // 현재 검사 중인 아동 정보
        questions,               // 전체 문항 배열
        currentAudio,           //***/
        speak,                  //***/
        stopTTS,                //***/
        options,                 // 선택지 배열 [{value, text}, ...]
        answers      = $bindable({}),    // 각 문항 답변 {question_id: value}
        currentIdx   = $bindable(0),     // 현재 보고 있는 문항 인덱스 (0~19)
        ttsSpeed     = $bindable(1.0),   // TTS 재생 속도
        isSpeaking   = $bindable(false),
        isRecording,             // 현재 녹음 중 여부
        isSliding    = $bindable(false), // 슬라이드 애니메이션 중 여부
        slideDir     = $bindable(''),    // 슬라이드 방향 ('left' | 'right' | '')
        currentQuestion = $bindable(null), // 현재 STT 대상 문항
        transcript,              // STT 인식 결과 텍스트
        unanswered,              // 미답변 문항 id 배열
        allAnswered,             // 모든 문항 답변 여부
        onToggleRecording,       // (question, isTTS) => void: 마이크/스피커 버튼
        onGoNext,                // () => void: 다음 문항으로 이동
        onGoPrev,                // () => void: 이전 문항으로 이동
        onSubmit,                // () => void: 제출
        onBack,                  // () => void: 돌아가기 (TTS/STT 중지 후 select 화면으로)
        onSaveDraft,              // () => void: 임시저장
        onGoToIndex
    } = $props();
    
    // 🔹 id → index 빠르게 찾기 (성능 최적화)
    let questionIndexMap = $derived(
        Object.fromEntries(questions.map((q, i) => [q.id, i]))
    );

    // 자동 이동 플래그 추가
    let autoMoving = $state(false); // 자동 이동 중 여부

    // 🔹 문항 상태 판단 (색상용)
    function getQuestionState(qid) {
        if (questions[currentIdx]?.id === qid) return 'current';
        if (answers[qid] !== undefined) return 'answered';
        return 'unanswered';
    }
</script>

<div class="card">
    <h2>{selectedSession.name} 검사</h2>

    <!-- 진행률 바 + 문항 번호 -->
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;">
        <div class="progress-bar" style="flex: 1; margin-bottom: 0;">
            <!-- 현재 문항 / 전체 문항 비율로 너비 계산 -->
            <div class="progress-fill"
                 style="width: {((currentIdx + 1) / questions.length) * 100}%">
            </div>
        </div>
        <span style="font-size: 0.9em; color: #6366f1; font-weight: 700; white-space: nowrap;">
            {currentIdx + 1} / {questions.length}
        </span>
    </div>

    <!-- TTS 재생 속도 슬라이더 (0.5x ~ 2.0x) -->
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 20px;">
        <span style="font-size: 0.95em; color: #475569; white-space: nowrap;">🔊 재생 속도</span>
        <input type="range" min="0.5" max="2.0" step="0.1" bind:value={ttsSpeed} style="flex: 1;" />
        <span style="font-size: 0.95em; color: #6366f1; font-weight: 700; width: 36px;">
            {ttsSpeed}x
        </span>
    </div>

    <!-- 문항 카드: 슬라이드 방향에 따라 CSS 클래스 적용 -->
    {#if questions[currentIdx]}
        <div class="question-card {slideDir === 'left' ? 'slide-out-left' : slideDir === 'right' ? 'slide-out-right' : ''}">
            <div class="question-box">

                <!-- 문항 텍스트 + 🔊 버튼 (TTS 재생) -->
                <p style="margin-bottom: 16px;">
                    {questions[currentIdx].id}. {questions[currentIdx].text}
                    <!-- isTTS=true: TTS 재생만, STT 자동 시작 포함 -->
                    <button onclick={() => {
                        if (currentAudio) {
                            stopTTS(); // 🔴 정지
                        } else {
                            speak(questions[currentIdx].text, questions[currentIdx]); // 🟢 재생
                        }
                    }}>
                        {currentAudio ? '⏹️' : '🔊'}
                    </button>
                </p>

                <!-- 선택지 4개 (2열 그리드) -->
                <div class="options-grid">
                    {#each options as opt}
                        <label class="opt-label">
                            <input
                                type="radio"
                                name="q{questions[currentIdx].id}"
                                value={opt.value}
                                checked={answers[questions[currentIdx].id] === opt.value}
                                onclick={async () => {
                                    const qid = questions[currentIdx].id;

                                    // 이미 선택된 항목 클릭 시 선택 해제
                                    if (answers[qid] === Number(opt.value)) {
                                        answers[qid] = undefined;
                                        return;     // 해제 시에는 이동 안 함
                                    } else {
                                        answers[qid] = Number(opt.value);
                                    }
                                    await onSaveDraft(); // 선택 즉시 임시저장

                                    // 자동 다음 이동 (STT 녹음 중이면 이동 안함 - 중복 이동 방지)
                                    autoMoving = true;
                                    await new Promise(r => setTimeout(r, 1000))
                                    if (!isRecording) await onGoNext();
                                    autoMoving = false;
                                }}
                            />
                            {opt.text}
                        </label>
                    {/each}
                </div>

                <!-- 마이크 버튼: 녹음 중이면 빨간색 + 펄스 애니메이션 -->
                <!-- isTTS=false: STT 녹음 토글 -->
                <button
                    class="mic-btn {isRecording && currentQuestion?.id === questions[currentIdx].id ? 'recording' : ''}"
                    onclick={() => onToggleRecording(questions[currentIdx], false)}>
                    🎤
                </button>

                <!-- STT 인식 결과 텍스트 표시 -->
                {#if currentQuestion?.id === questions[currentIdx].id && transcript}
                    <p style="font-size: 0.9em; color: #6366f1; margin-top: 8px; text-align: center;">
                        인식된 텍스트: {transcript}
                    </p>
                {/if}
            </div>
        </div>
    {/if}

    <!-- 이전/다음 수동 이동 버튼 -->
    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 16px;">
        <!-- 첫 번째 문항이거나 슬라이딩 중이면 비활성화 -->
        <button onclick={onGoPrev} disabled={currentIdx === 0 || isSliding}>← 이전</button>
        <!-- 마지막 문항이거나 슬라이딩 중이면 비활성화 -->
        <button onclick={() => { if (!autoMoving) onGoNext(); }} disabled={currentIdx === questions.length - 1 || isSliding || autoMoving}>다음 →</button>
    </div>

    <!-- 📍 문항 네비게이션 (상태별 색상 표시) -->
    <div style="margin-top: 16px; text-align: center;">
        <span style="font-size: 0.85em; color: #94a3b8;">문항:</span>

        {#each questions as q}
            <button
                class="q-btn {getQuestionState(q.id)}"
                onclick={() => {
                    const idx = questionIndexMap[q.id];
                    if (idx !== undefined) onGoToIndex?.(idx);
                }}
            >
                {q.id}
            </button>
        {/each}
    </div>

    <div style="display: flex; gap: 12px; margin-top: 16px;">
        <!-- 돌아가기: TTS/STT 중지 후 사용자 선택 화면으로 -->
        <button onclick={onBack}>돌아가기</button>
        <!-- 제출: 모든 문항 답변 완료 시에만 활성화 -->
        <button onclick={onSubmit} disabled={!allAnswered}>제출</button>
    </div>
</div>

<style>
.card {
    background: #fff; border-radius: 24px;
    padding: 40px 48px; max-width: 900px;
    margin: 0 auto; box-shadow: 0 24px 64px rgba(0,0,0,.28);
}
h2 { font-size: 1.6em; color: #3730a3; margin-bottom: 16px; }
/* 진행률 바 트랙 */
.progress-bar {
    background: #e2e8f0; border-radius: 99px;
    height: 8px; overflow: hidden;
}
/* 진행률 바 채워지는 부분 */
.progress-fill {
    background: linear-gradient(90deg, #6366f1, #7c3aed);
    height: 100%; border-radius: 99px; transition: width .35s ease;
}
/* 문항 박스 */
.question-box {
    font-size: 1.15em; color: #1e293b; line-height: 1.7;
    background: #f8fafc; border-radius: 14px; padding: 20px 22px;
    margin-bottom: 20px; text-align: left;
}
/* 선택지 2열 그리드 */
.options-grid {
    display: grid; grid-template-columns: 1fr 1fr;
    gap: 10px; margin-bottom: 20px;
}
/* 선택지 라벨 */
.opt-label {
    padding: 14px 10px; font-size: .95em; font-weight: 500;
    border: 2px solid #e2e8f0; border-radius: 12px;
    background: #fff; cursor: pointer; transition: all .2s;
    display: flex; align-items: center; gap: 8px;
}
/* 선택된 선택지 강조 */
.opt-label:has(input:checked) {
    border-color: #6366f1; background: #6366f1; color: #fff;
}
.opt-label input { display: none; } /* 라디오 버튼 숨김 */
/* 마이크 버튼 (원형) */
.mic-btn {
    width: 72px; height: 72px; border-radius: 50%;
    font-size: 1.8em; cursor: pointer;
    display: block; margin: 0 auto 12px;
    background: #6366f1; color: #fff;
    box-shadow: 0 4px 16px rgba(99,102,241,.4);
    padding: 0;
}
/* 녹음 중: 빨간색 + 펄스 애니메이션 */
.mic-btn.recording {
    background: #ef4444;
    animation: pulse 1s infinite;
}
@keyframes pulse {
    0%   { box-shadow: 0 0 0 0 rgba(239,68,68,.7); }
    70%  { box-shadow: 0 0 0 12px rgba(239,68,68,0); }
    100% { box-shadow: 0 0 0 0 rgba(239,68,68,0); }
}
/* 카드 슬라이드 애니메이션 */
.question-card {
    transition: transform 0.35s ease, opacity 0.35s ease;
}
/* 다음 문항으로 이동 시: 왼쪽으로 사라짐 */
.question-card.slide-out-left {
    transform: translateX(-60px); opacity: 0;
}
/* 이전 문항으로 이동 시: 오른쪽으로 사라짐 */
.question-card.slide-out-right {
    transform: translateX(60px); opacity: 0;
}
button {
    padding: 13px 28px; font-size: 1em; font-weight: 600;
    border: none; border-radius: 12px; cursor: pointer;
    transition: transform .1s, box-shadow .1s; margin: 5px;
    background: #6366f1; color: #fff;
}
button:hover  { transform: translateY(-2px); box-shadow: 0 6px 18px rgba(0,0,0,.18); }
button:active { transform: translateY(0); }
button:disabled { background: #e2e8f0; color: #94a3b8; transform: none; cursor: not-allowed; }
p { color: #475569; }

/* 🔢 문항 네비게이션 버튼 */
.q-btn {
    margin: 4px;
    width: 32px;
    height: 32px;
    border-radius: 8px;
    border: none;
    font-size: 0.85em;
    cursor: pointer;
    transition: all 0.2s ease;
    padding: 0;
}

/* 🔵 현재 문항 */
.q-btn.current {
    background-color: #3b82f6;
    color: white;
    font-weight: bold;
}

/* ⚪ 답변 완료 */
.q-btn.answered {
    background-color: #e5e7eb;
    color: #374151;
}

/* 🔴 미답변 */
.q-btn.unanswered {
    background-color: #fee2e2;
    color: #dc2626;
}

/* hover 효과 */
.q-btn:hover {
    transform: scale(1.1);
}

</style>