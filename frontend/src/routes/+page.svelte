<!--
    +page.svelte (메인)
    전역 상태 관리 및 phase(화면 단계) 라우팅 담당
    - phase: select → consent → checklist → result
    -        select → (관리자 인증) → admin
    - TTS/STT 로직 전담 (컴포넌트에 콜백으로 전달)
    - 다크모드 body 클래스 관리
-->
<script>
    import { onMount }    from 'svelte';
    import { getSessions, getQuestions, submitAnswers, generateTTS,
             saveDraft, loadDraft, deleteDraft } from '$lib/api.js';
    import { findBestMatch, playSound } from '$lib/stores.js';

    // 컴포넌트 import
    import AdminModal  from '$lib/components/AdminModal.svelte';
    import SelectSession from '$lib/components/SelectSession.svelte';
    import Consent     from '$lib/components/Consent.svelte';
    import Checklist   from '$lib/components/Checklist.svelte';
    import Admin       from '$lib/components/Admin.svelte';
    import Result      from '$lib/components/Result.svelte';

    // ── 화면 단계 및 데이터 ────────────────────────────────
    let phase         = $state('select'); // 현재 화면 단계
    let sessions      = $state([]);       // 등록 사용자 목록
    let questions     = $state([]);       // 문항 목록
    let options       = $state([]);       // 선택지 목록
    let selectedSession = $state(null);   // 현재 검사 중인 아동
    let answers       = $state({});       // 문항별 답변 {question_id: value}
    let result        = $state(null);     // 채점 결과
    let darkMode      = $state(false);    // 다크모드 여부

    // ── STT 관련 ───────────────────────────────────────────
    let recognition     = $state(null);  // Web Speech API 인식기 객체
    let isRecording     = $state(false); // 현재 녹음 중 여부
    let isProcessing    = $state(false); // STT 처리 중 여부
    let transcript      = $state('');    // STT 인식 결과 텍스트
    let currentQuestion = $state(null);  // 현재 STT 대상 문항
    let silenceTimer    = $state(null);  // 무음 감지 타이머
    let sttTimer        = $state(null);  // STT 타임아웃 타이머

    // ── 카드형 문항 슬라이드 ───────────────────────────────
    let currentIdx = $state(0);      // 현재 보고 있는 문항 인덱스 (0~19)
    let slideDir   = $state('');     // 슬라이드 방향 ('left' | 'right' | '')
    let isSliding  = $state(false);  // 슬라이드 애니메이션 진행 중 여부

    // ── TTS 관련 ───────────────────────────────────────────
    let ttsSpeed     = $state(1.0);  // TTS 재생 속도 (0.5 ~ 2.0)
    let currentAudio = $state(null); // 현재 재생 중인 Audio 객체
    let isManuallyStopped = $state(false); //***/
    let ttsTimer;

    let isSpeaking = false;

    async function speakSafe(text, q) {
        if (isSpeaking && q?.manual) return;
        isSpeaking = true;

        try {
            await speak(text, q);
        } finally {
            isSpeaking = false;
        }
    }
    
    // ── 임시저장 ───────────────────────────────────────────
    let draftSavedAt  = $state(null); // 마지막 임시저장 시각
    let autoSaveTimer = $state(null); // 자동저장 타이머 (현재 미사용)

    // ── 관리자 ─────────────────────────────────────────────
    let showAdminModal  = $state(false); // 관리자 로그인 모달 표시 여부
    let isAdminLoggedIn = $state(false); // 관리자 로그인 상태 유지
    let adminRef        = $state(null);  // Admin 컴포넌트 참조 (loadData 호출용)

    // ── derived 상태 ───────────────────────────────────────
    // 미답변 문항 id 배열
    let unanswered = $derived(
        questions.filter(q => answers[q.id] === undefined).map(q => q.id)
    );
    // 모든 문항 답변 완료 여부
    let allAnswered = $derived(
        questions.length > 0 && questions.every(q => answers[q.id] !== undefined)
    );

    // ── 다크모드 ───────────────────────────────────────────
    // darkMode 변경 시 body에 'dark' 클래스 추가/제거
    $effect(() => {
        document.body.classList[darkMode ? 'add' : 'remove']('dark');
    });

    // ── TTS (문항 음성 재생) ───────────────────────────────
    /**
     * 텍스트를 TTS로 재생
     * @param {string} text     - 읽을 텍스트
     * @param {object} question - 재생 후 자동 녹음 시작할 문항 (없으면 null)
     */
    async function speak(text, question = null, onEnd = null) {
        try {
            // 재생 중인 오디오 먼저 중지
            if (currentAudio) {
                isManuallyStopped = true; //***/
                currentAudio.pause();
                currentAudio.currentTime = 0;
                currentAudio = null;
            }
            const res = await generateTTS(text, ttsSpeed);
            if (res && res.status === 'success') {
                const audio = new Audio(`http://localhost:8000/api/tts/file/${res.filename}`);
                audio.playbackRate = ttsSpeed;
                
                isManuallyStopped = false; //**새 재생 시작
                
                // TTS 재생 끝나면 자동으로 해당 문항 STT 녹음 시작
                audio.onended = async () => {
                    if (isManuallyStopped) return;

                    if (question) {
                        currentQuestion = question;
                        currentAudio = null;    // *** 추가: TTS 재생 끝나면 아이콘 🔊로 복귀
                        await startRecording();
                    }
                    if (onEnd) onEnd();
                };
                currentAudio = audio;
                audio.play();
            }
        } catch (e) {
            console.log('TTS 오류:', e);
        }
    }
    
    //***/
    function stopTTS() {
        if (currentAudio) {
            isManuallyStopped = true;
            currentAudio.pause();
            currentAudio.currentTime = 0;
            currentAudio = null;
        }
    }
    // ── STT (음성 인식 녹음) ───────────────────────────────
    /**
     * 녹음 시작
     * - 시작 비프음 재생
     * - Web Speech API 녹음 시작
     * - 5초 무음 시 '말씀해 주세요' 안내
     */
    async function startRecording() {
        if (!recognition || isRecording) return; // 미지원 브라우저 or 이미 녹음 중이면 중단
        playSound(880, 0.3); // 녹음 시작 비프음
        await new Promise(r => setTimeout(r, 350)); // 비프음 재생 대기

        // 현재 문항 기존 답변 초기화 (재녹음 시 이전 답변 지움)
        if (currentQuestion) answers[currentQuestion.id] = undefined;

        try {
            recognition.start();
            isRecording = true;

            // 5초 동안 아무 말 없으면 안내 TTS 재생
            silenceTimer = setTimeout(async () => {
                if (isRecording) {
                    recognition.stop();
                    speak('말씀해 주세요', null, async () => {
                        // 🔥 TTS 끝난 뒤 자동 녹음
                        await startRecording();
                    });
                }
            }, 5000);
        } catch(e) {
            console.log('녹음 시작 오류:', e);
            isRecording = false;
        }
    }

    /**
     * 녹음 토글 (Checklist의 🎤 버튼에서 호출)
     * @param {object} q - 녹음 대상 문항
     */
    async function toggleRecording(q) {
        if (isRecording) {
            // 녹음 중이면 중지
            clearTimeout(silenceTimer);
            recognition.stop();
            isRecording = false;
        } else {
            // 녹음 시작
            currentQuestion = q;
            await startRecording();
        }
    }

    /**
     * 🔊 버튼 클릭: TTS 재생 (녹음 자동 시작 포함)
     * @param {object} q - 재생할 문항
     */
    async function speakQuestion(q) {
        stopAll(); // 기존 TTS/STT 중지 후 새로 시작
        await speak(q.text, q);
    }

    /**
     * TTS/STT 강제 중지
     * - 뒤로가기, 다음/이전 이동, 제출 시 호출
     */
    function stopAll() {
        if (currentAudio) {
            currentAudio.pause();
            currentAudio.currentTime = 0;
            currentAudio = null;
        }
        speechSynthesis.cancel(); // 잔여 음성 제거
        if (isRecording && recognition) recognition.stop();
        isRecording  = false;
        isProcessing = false;
        clearTimeout(silenceTimer);
        clearTimeout(sttTimer);
        clearTimeout(ttsTimer);
    }

    // ── 카드 이동 ──────────────────────────────────────────
    /**
     * 다음 문항으로 이동
     * 1. 현재 TTS/STT 중지
     * 2. 왼쪽 슬라이드 애니메이션 (0.35초)
     * 3. 인덱스 증가
     * 4. 새 문항 TTS 재생 + 자동 STT 시작
     */
    async function goNext() {
        if (currentIdx >= questions.length - 1 || isSliding) return;
        stopAll();
        isSliding = true; slideDir = 'left';
        await new Promise(r => setTimeout(r, 350)); // 애니메이션 대기
        currentIdx++;
        currentQuestion = questions[currentIdx];
        slideDir = ''; isSliding = false; transcript = '';
        await speak(questions[currentIdx].text, questions[currentIdx]);
    }

    /**
     * 이전 문항으로 이동
     * 1. 현재 TTS/STT 중지
     * 2. 오른쪽 슬라이드 애니메이션 (0.35초)
     * 3. 인덱스 감소
     */
    async function goPrev() {
        if (currentIdx <= 0 || isSliding) return;
        stopAll();
        isSliding = true; slideDir = 'right';
        await new Promise(r => setTimeout(r, 350));
        currentIdx--;
        currentQuestion = questions[currentIdx];
        slideDir = ''; isSliding = false; transcript = '';
    }

    // 원하는 항목 이동
    async function goToIndex(targetIdx) {
    if (
        targetIdx < 0 ||
        targetIdx >= questions.length ||
        targetIdx === currentIdx ||
        isSliding
    ) return;

    stopAll();

    // 방향 결정 (애니메이션용)
    slideDir = targetIdx > currentIdx ? 'left' : 'right';
    isSliding = true;

    await new Promise(r => setTimeout(r, 350));

    currentIdx = targetIdx;
    currentQuestion = questions[currentIdx];

    slideDir = '';
    isSliding = false;
    transcript = '';

    //TTS 자동 실행
    await speak(questions[currentIdx].text, questions[currentIdx]);
}


    // ── 임시저장 ───────────────────────────────────────────
    /**
     * 현재까지의 답변을 서버 drafts.csv에 임시저장
     * - STT 인식 성공 시, 선택지 클릭 시 자동 호출
     */
    async function saveCurrentDraft() {
        const answerList = Object.entries(answers)
            .filter(([, val]) => val !== undefined)
            .map(([qid, val]) => ({ question_id: parseInt(qid), value: val }));
        if (answerList.length === 0) return;
        const res = await saveDraft(selectedSession.id, answerList);
        if (res.status === 'success') draftSavedAt = res.saved_at;
    }

    // ── 검사 시작 ──────────────────────────────────────────
    /**
     * 동의 완료 후 검사 시작
     * 1. 상태 초기화
     * 2. 임시저장 있으면 불러와서 마지막 답변 문항부터 시작
     * 3. 첫 문항 TTS 재생
     */
    async function startChecklist() {
        // 이전 TTS / 타이머 완전 정리
        stopAll(); // speechSynthesis.cancel()
        clearTimeout(ttsTimer);

        // 상태 초기화
        answers   = {}; 
        result = null;
        currentIdx = 0;
        currentQuestion = null;
        draftSavedAt = null;

        // 체크리스트 진입
        phase     = 'checklist';

        // 이전 임시저장 데이터 복원
        const res = await loadDraft(selectedSession.id);
        if (res && res.draft && res.draft.answers?.length > 0) {
            res.draft.answers.forEach(a => { 
                answers[a.question_id] = a.value; 
            });
            draftSavedAt = res.draft.saved_at;
            // 마지막으로 답변한 문항으로 이동
            const lastAnswered = Math.max(...res.draft.answers.map(a => a.question_id));
            const idx = questions.findIndex(q => q.id === lastAnswered);
            
            if (idx >= 0) {
                currentIdx = idx + 1 < questions.length ? idx + 1 : idx;
            }
        }

        // 첫 질문 세팅
        currentQuestion = questions[currentIdx];

        if (!currentQuestion) return;

        // TTS 안전 실행 (setTimeout 제거)
        await tick?.();

        ttsTimer = setTimeout(() => {
            speakSafe(currentQuestion.text, currentQuestion);
        }, 500);
    }

       

    // ── 답변 제출 ──────────────────────────────────────────
    /**
     * 모든 문항 답변 완료 후 제출
     * 1. TTS/STT 중지
     * 2. 백엔드에 답변 전송 + 채점
     * 3. 임시저장 삭제
     * 4. 결과 화면으로 이동
     */
    async function submit() {
        stopAll(); // 제출 시 TTS/STT 중지
        const answerList = questions.map(q => ({
            question_id: q.id,
            value: answers[q.id] ?? 0, // 미답변은 0으로 처리
        }));
        const res = await submitAnswers(selectedSession.id, answerList);
        clearInterval(autoSaveTimer);
        await deleteDraft(selectedSession.id); // 임시저장 삭제
        result = res;
        phase  = 'result';
    }

    // ── 관리자 ─────────────────────────────────────────────
    /**
     * 관리자 로그인 성공 콜백 (AdminModal에서 호출)
     * 로그인 상태 저장 후 관리자 화면으로 이동 + 데이터 로드
     */
    async function handleAdminLogin() {
        isAdminLoggedIn = true;
        phase = 'admin';
    }

    /**
     * 관리자 버튼 클릭 (SelectSession에서 호출)
     * 이미 로그인했으면 바로 이동, 아니면 모달 표시
     */
    async function goToAdmin() {
        if (isAdminLoggedIn) {
            phase = 'admin';
        } else {
            showAdminModal = true;
        }
    }

    // ── onMount: 초기 데이터 로드 + STT 초기화 ────────────
    onMount(async () => {
        // 사용자 목록 + 문항/선택지 불러오기
        const sessionRes = await getSessions();
        sessions = sessionRes.sessions;
        const qRes = await getQuestions();
        questions  = qRes.questions;
        options    = qRes.options;

        // Web Speech API 초기화 (크롬 권장)
        const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (Recognition) {
            recognition                = new Recognition();
            recognition.lang           = 'ko-KR';        // 한국어 인식
            recognition.interimResults = false;           // 최종 결과만 사용
            recognition.continuous     = false;           // 한 번 말하면 자동 종료

            // STT 인식 결과 처리
            recognition.onresult = (e) => {
                const text  = e.results[0][0].transcript;
                console.log('STT 결과:', text);
                transcript  = text;

                // 자모 분리 + 유사도 기반 키워드 매칭
                const value = findBestMatch(text);
                const q     = questions[currentIdx]; // 현재 문항

                if (value !== null && q) {
                    // 인식 성공: 답변 저장 + 성공 사운드 + 다음 문항 이동
                    answers[q.id]   = value;
                    currentQuestion = q;
                    saveCurrentDraft();

                    // 인식 성공 확인 사운드 (3음 상승)
                    playSound(660, 0.15);
                    setTimeout(() => playSound(880, 0.2),   160);
                    setTimeout(() => playSound(1100, 0.25), 320);

                    // 1.5초 후 다음 문항으로 자동 이동
                    if (currentIdx < questions.length - 1) {
                        setTimeout(async () => { await goNext(); }, 1500);
                    }
                } else {
                    // 인식 실패: 재시도 안내
                    speak('다시 한번 말씀해 주세요');
                }
            };

            // 녹음 종료 시 상태 초기화
            recognition.onend   = () => { isRecording = false; isProcessing = false; };

            // 오류 처리
            recognition.onerror = (e) => {
                console.log('STT 오류:', e.error);
                isRecording = false; isProcessing = false;
            };
        }
    });
</script>

<!-- 다크모드 클래스를 최상위 div에 적용하여 하위 컴포넌트에 전파 -->
<div class={darkMode ? 'dark' : ''}>

    <!-- 관리자 로그인 모달 (showAdminModal=true일 때 표시) -->
    <AdminModal bind:showAdminModal onLogin={handleAdminLogin} />

    <!-- 사용자 선택 화면 -->
    {#if phase === 'select'}
        <SelectSession
            bind:sessions
            bind:darkMode
            onSelect={(session) => { selectedSession = session; phase = 'consent'; }}
            onAdminClick={goToAdmin}
        />

    <!-- 개인정보 동의 화면 -->
    {:else if phase === 'consent'}
        <Consent
            {selectedSession}
            onAgree={startChecklist}
            onCancel={() => phase = 'select'}
        />

    <!-- 체크리스트 화면 (카드형) -->
    {:else if phase === 'checklist'}
        <Checklist
            {selectedSession} 
            {questions}
            {options}
            {currentAudio} //***/
            {speak}        //***/
            {stopTTS}      //***/
            bind:answers
            bind:currentIdx
            bind:ttsSpeed
            {isRecording}
            bind:isSliding
            bind:slideDir
            bind:currentQuestion
            {transcript}
            {unanswered}
            {allAnswered}
            onToggleRecording={(q, isTTS) => isTTS ? speakQuestion(q) : toggleRecording(q)}
            onGoNext={goNext}
            onGoPrev={goPrev}
            onGoToIndex={goToIndex}
            onSubmit={submit}
            onBack={() => { stopAll(); phase = 'select'; }}
            onSaveDraft={saveCurrentDraft}
        />

    <!-- 관리자 화면 -->
    {:else if phase === 'admin'}
        <!-- bind:this로 Admin 컴포넌트 참조 저장 (loadData 호출용) -->
        <Admin onBack={() => phase = 'select'} />

    <!-- 결과 화면 -->
    {:else if phase === 'result'}
        <Result {result} onBack={() => phase = 'select'} />
    {/if}

</div>

<style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    /* 기본 배경 (보라색 그라디언트) */
    :global(body) {
        font-family: 'Apple SD Gothic Neo', 'Malgun Gothic', Arial, sans-serif;
        background: linear-gradient(135deg, #5b6ef5 0%, #7c3aed 100%);
        min-height: 100vh;
        padding: 40px;
    }

    /* 다크모드 배경 (어두운 남색) */
    :global(body.dark) {
        background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%);
    }

    /* ── 다크모드: 하위 컴포넌트에 전파 ── */
    /* :global()을 사용해 scoped CSS 외부(하위 컴포넌트)에 적용 */
    :global(body.dark .card)  { background: #1e293b; box-shadow: 0 24px 64px rgba(0,0,0,.5); }
    :global(body.dark h1),
    :global(body.dark h2)     { color: #a5b4fc; }
    :global(body.dark p)      { color: #cbd5e1; }
    :global(body.dark input[type="text"]),
    :global(body.dark input[type="number"]),
    :global(body.dark input[type="password"]) {
        background: #0f172a; border-color: #334155; color: #e2e8f0;
    }
    :global(body.dark select) { background-color: #0f172a; border-color: #334155; color: #e2e8f0; }
    :global(body.dark .question-box)  { background: #0f172a; color: #e2e8f0; }
    :global(body.dark .opt-label)     { background: #1e293b; border-color: #334155; color: #e2e8f0; }
    :global(body.dark .opt-label:has(input:checked)) { background: #6366f1; border-color: #6366f1; color: #fff; }
    :global(body.dark .consent-box)   { background: #0f172a; border-color: #334155; color: #cbd5e1; }
    :global(body.dark .consent-name)  { background: #0f172a; color: #94a3b8; }
    :global(body.dark .consent-check) { border-color: #334155; color: #e2e8f0; }
    :global(body.dark .consent-check:has(input:checked)) { background: #1e1b4b; border-color: #6366f1; }
    :global(body.dark .admin-table th)  { background: #4338ca; }
    :global(body.dark .admin-table td)  { border-color: #334155; color: #cbd5e1; }
    :global(body.dark .expand-row td)   { background: #0f172a; }
    :global(body.dark .expand-cell)     { background: #1e293b; border-color: #334155; }
    :global(body.dark .selected-row td) { background: #1e1b4b; }
    :global(body.dark .modal-box)       { background: #1e293b; }
    :global(body.dark .progress-bar)    { background: #334155; }
    :global(body.dark .btn-outline)     { background: #1e293b; color: #a5b4fc; border-color: #6366f1; }
    :global(body.dark .btn-mode)        { background: #334155; color: #cbd5e1; }
</style>