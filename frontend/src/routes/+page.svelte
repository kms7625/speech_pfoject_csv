<script>
    import { onMount } from 'svelte';
    import { getChildren,
             createChild,
             getQuestions,
             submitAnswers,
             generateTTS,
             deleteChild} from '$lib/api.js'

    // 상태 변수들
    let children = $state([]);        // 등록 아동 목록
    let questions = $state([]);       // 문항 목록
    let options = $state([]);         // 선택지 목록
    let selectedChild = $state(null); // 현재 선택된 아동
    let answers = $state({});         // 각 문항 답변 저장 {question_id: value}
    let result = $state(null);        // 채점 결과
    let phase = $state('select');     // 화면 단계: select -> checklist -> result
    let newName = $state('');         // 신규 아동 이름 입력값
    let newAge = $state('');          // 신규 아동 나이 입력값
    // STT 관련 변수
    let isRecording = $state(false);
    let isProcessing = $state(false);
    let mediaRecorder = $state(null);
    let chunks = $state([]);
    // STT인식 결과 텍스트
    let transcript = $state('');
    // 성별선택
    let newGender = $state('');
    // 현제 보고 있는 문항 추적 변수
    let currentQuestion = $state(null);
    // 녹음 시작 시간 기록
    let startTime = $state(null);
    // 녹음 시작 후 일정시간 무응답시 안내
    let silenceTimer = $state(null);
    // 녹음 처리 시간 초과 관련
    let sttTimer = $state(null)
    // 미답변 문항 번호 관련
    let unanswered = $derived(
        questions
            .filter(q => answers[q.id] === undefined)
            .map(q => q.id)
    );


    // 녹음 시작/중지 토글
    async function toggleRecording() {
        if (isRecording) {
            clearTimeout(silenceTimer);
            mediaRecorder.stop();
        } else {
            await startRecording();
        }
    }

    // 녹음 시작
    async function startRecording() {

        // 녹음 시작 삐 소리
        playSound(880, 0.3);
        await new Promise(resolve => setTimeout(resolve, 350));

        const stream = await navigator.mediaDevices.getUserMedia({ audio: true});
        chunks = [];

        // 녹음 시작 시 현재 문항 답변 초기화
        if (currentQuestion) {
            answers[currentQuestion.id] = undefined;
        }

        // 10초 무음 타이머 시작
        silenceTimer = setTimeout(async () => {
            if (isRecording) {
                // 녹음 중지
                mediaRecorder.stop();
                // 재안내 TTS
                await speak('말씀해 주세요')
            }
        }, 10000);

        mediaRecorder = new MediaRecorder(stream);
        mediaRecorder.ondataavailable = (e) => {
            if (e.data.size > 0) chunks.push(e.data);
        };
        mediaRecorder.onstop = async () => {
            clearTimeout(silenceTimer); // 타이머 취소
            stream.getTracks().forEach(t => t.stop());
            await processRecording();
        };

        mediaRecorder.start();
        isRecording = true;
    }

    // 녹음 완료 후 STT 처리
    async function processRecording() {
        isProcessing = true;

        // 10초 타임아웃 시작
        sttTimer = setTimeout(async () => {
            if (isProcessing) {
                isProcessing = false;
                isRecording = false;
                console.log('STT 타임아웃');
                await speak('잠시 후 다시 시도해 주세요');
            }
        }, 10000);

        try {
            const blob = new Blob(chunks, { type: 'audio/webm'});
            const formData = new FormData();
            formData.append('file', blob, 'recording.webm');

            const res = await fetch('http://localhost:8000/api/stt/transcribe', {
                method: 'POST',
                body: formData,
            });
            const data = await res.json();
            const text = data.text;
            console.log('STT 결과:', text);
            transcript = text;

            // 음성 텍스트를 점수로 변환
            const value = mapTextToValue(text);
            if (value !== null && currentQuestion) {
                answers[currentQuestion.id] = value;
                // 인식 성공 확인 사운드(높은 음 두번)
                playSound(660, 0.15);
                setTimeout(() => playSound(880, 0.2), 160);
                setTimeout(() => playSound(1100, 0.25), 320);
            }
        } catch(e) {
            console.log('STT 오류:', e);
        } finally {
            isProcessing = false;
            isRecording = false;
        }
    }

    // 음성 인식 결과를 0~3 점수로 변환
    function mapTextToValue(text) {
        if (text.includes('전혀') || text.includes('없')) return 0;
        if (text.includes('약간') || text.includes('가끔') || text.includes('조금')) return 1;
        if (text.includes('꽤') || text.includes('자주') || text.includes('많')) return 2;
        if (text.includes('매우') || text.includes('항상') || text.includes('심')) return 3;
        return null;
    }

   /*문항 텍스트를 소리로 읽어주는 함수
function speak(text) {
    // 이전에 읽던 거 있으면 멈춤
    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'ko-KR';  // 한국어 설정
    utterance.rate = 0.9;      // 속도 (1.0이 기본, 낮을수록 느림)

    window.speechSynthesis.speak(utterance);
}
*/
    async function speak(text, question = null) {
    try {
        const res = await generateTTS(text);
        if (res && res.status === 'success') {
            const audio = new Audio(`http://localhost:8000/api/tts/file/${res.filename}`);

            // 음성 재생 끝나면 자동 녹음 시작
            audio.onended = async () => {
                if (question) {
                    currentQuestion = question;
                    await startRecording();
                }
            };

            audio.play();
        } else {
            console.log('TTS 응답 실패:', res);
        }
    } catch (e) {
        console.log('TTS 오류:', e);
    }
}


    // 페이지 로드 시 아동 목록 + 문항 불러오기
    onMount(async () => {
        const childRes = await getChildren();
        children = childRes.children;

        const qRes = await getQuestions();
        questions = qRes.questions;
        options = qRes.options;
    });

    //아동 등록
    async function addChild() {
        if (!newName || !newAge || !newGender) return;
        const res = await createChild(newName, parseInt(newAge), newGender);
        children = [...children, res.child];
        newName = '';
        newAge = '';
        newGender = '';
    }

    // 아동 삭제
    async function removeChild(childId) {
        await deleteChild(childId)
        children = children.filter(c => c.id !== childId);
    }

    // 검사 시작
    function startChecklist(child) {
        selectedChild = child;
        answers = {};
        result = null;
        startTime = Date.now(); // 검사 시작 시간 기록
        phase = 'checklist';
    }

    // 답변 제출
    async function submit() {
        // answers 객체를 배열로 변환
        const answerList = questions.map(q => ({
            question_id: q.id,
            value: answers[q.id] ?? 0,
        }));

        // 응답시간 계산(초단위)
        const responseTime = (Date.now() - startTime) / 1000;

        const res = await submitAnswers(selectedChild.id, answerList, responseTime);
        result = res;
        phase = 'result';
    }

    // 모든 문항에 답변했는지 확인
    let allAnswered = $derived(
    questions.length > 0 &&
        questions.every(q => answers[q.id] !== undefined)
    );

    // 사운드 생성 함수
    function playSound(frequency, duration, type = 'sine') {
        const audioCtx = new AudioContext();
        const oscillator = audioCtx.createOscillator();
        const gainNode = audioCtx.createGain();

        oscillator.connect(gainNode);
        gainNode.connect(audioCtx.destination);

        oscillator.type = type;
        oscillator.frequency.value = frequency;
        gainNode.gain.setValueAtTime(0.3, audioCtx.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + duration);

        oscillator.start(audioCtx.currentTime);
        oscillator.stop(audioCtx.currentTime + duration);
    }
</script>



<!-- 아동 선택 화면 -->
{#if phase === 'select'}
    <div class="card">
        <h1>🧠 ADHD 체크리스트</h1>

        <h2>아동 등록</h2>
        <input bind:value={newName} placeholder="이름" type="text" />
        <input bind:value={newAge} placeholder="나이" type="number" />
        <!--성별선택기능-->
        <select bind:value={newGender}>
            <option value="">성별 선택</option>
            <option value="남">남</option>
            <option value="여">여</option>
        </select>
        <button onclick={addChild}>등록</button>

        <h2>아동 선택</h2>
        {#if children.length === 0}
            <p>등록된 아동이 없습니다.</p>
        {:else}
            {#each children as child}
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                    <button onclick={() => startChecklist(child)}>
                        {child.name} ({child.age}세 / {child.gender})
                    </button>
                    <button onclick={() => removeChild(child.id)}>삭제</button>
                </div>
            {/each}
        {/if}
    </div>

<!-- 체크리스트 화면 -->
{:else if phase === 'checklist'}
    <div class="card">
        <h2>{selectedChild.name} 검사</h2>

        <div class="progress-bar">
            <div class="progress-fill"
                 style="width: {(Object.keys(answers).length / questions.length) * 100}%">
            </div>
        </div>

        {#each questions as q}
            <div class="question-box">
                <p>{q.id}. {q.text}
                    <button onclick={() => speak(q.text, q)}>🔊</button>
                </p>
                <div class="options-grid">
                    {#each options as opt}
                        <label class="opt-label">
                            <input
                                type="radio"
                                name="q{q.id}"
                                value={opt.value}
                                checked={answers[q.id] === opt.value}
                                onchange={() => answers[q.id] = Number(opt.value)}
                            />
                            {opt.text}
                        </label>
                    {/each}
                </div>
                <button
                    class="mic-btn {isRecording && currentQuestion?.id === q.id ? 'recording' : ''}"
                    onclick={() => { currentQuestion = q; toggleRecording(); }}>
                    🎤
                </button>

                <!-- 인식 결과 표시 -->
                {#if currentQuestion?.id === q.id && transcript}
                    <p style="font-size: 0.9em; color: #6366f1; margin-top: 8px;">
                        인식된 텍스트: {transcript}
                    </p>
                {/if}
            </div>
        {/each}
            <!-- 마이크 버튼 -->
        <button onclick={submit} disabled={!allAnswered}>제출</button>
        <!--  미답변 문항 번호 계산 -->
        {#if unanswered.length > 0}
            <p style="color: #ef4444; font-size: 0.9em; margin-top: 8px;">
                미답변 문항: {unanswered.join(', ')}번
            </p>
        {/if}
        <button onclick={() => phase = 'select'}>돌아가기</button>
    </div>

<!-- 결과 화면 -->
{:else if phase === 'result'}
    <div class="card">
        <h2>✅ 검사 완료!</h2>
        <div class="result-score">{result.scores.total}</div>
        <p>총점</p>
        <p>부주의: {result.scores.inattention}</p>
        <p>과잉행동/충동성: {result.scores.hyperactivity}</p>
        <button onclick={() => phase = 'select'}>처음으로</button>
    </div>
{/if}

<style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :global(body) {
        font-family: 'Apple SD Gothic Neo', 'Malgun Gothic', Arial, sans-serif;
        background: linear-gradient(135deg, #5b6ef5 0%, #7c3aed 100%);
        min-height: 100vh;
        padding: 40px;
    }

    .card {
        background: #fff;
        border-radius: 24px;
        padding: 40px 48px;
        max-width: 900px;      /* 기존보다 넓게 */
        margin: 0 auto;        /* 중앙 정렬 */
        box-shadow: 0 24px 64px rgba(0,0,0,.28);
    }

    h1 { font-size: 1.9em; color: #3730a3; margin-bottom: 8px; }
    h2 { font-size: 1.6em; color: #3730a3; margin-bottom: 16px; }

    input[type="text"], input[type="number"] {
        width: 100%; padding: 14px 16px; font-size: 1.1em;
        border: 2px solid #e2e8f0; border-radius: 12px;
        margin-bottom: 16px; outline: none; transition: border .2s;
    }
    input[type="text"]:focus,
    input[type="number"]:focus { border-color: #6366f1; }

    button {
        padding: 13px 28px; font-size: 1em; font-weight: 600;
        border: none; border-radius: 12px; cursor: pointer;
        transition: transform .1s, box-shadow .1s; margin: 5px;
        background: #6366f1; color: #fff;
    }
    button:hover  { transform: translateY(-2px); box-shadow: 0 6px 18px rgba(0,0,0,.18); }
    button:active { transform: translateY(0); }
    button:disabled { background: #e2e8f0; color: #94a3b8; transform: none; cursor: not-allowed; }

    .question-box {
        font-size: 1.15em; color: #1e293b; line-height: 1.7;
        background: #f8fafc; border-radius: 14px; padding: 20px 22px;
        margin-bottom: 20px; text-align: left;
    }

    .options-grid {
        display: grid; grid-template-columns: 1fr 1fr;
        gap: 10px; margin-bottom: 20px;
    }

    .opt-label {
        padding: 14px 10px; font-size: .95em; font-weight: 500;
        border: 2px solid #e2e8f0; border-radius: 12px;
        background: #fff; cursor: pointer; transition: all .2s;
        display: flex; align-items: center; gap: 8px;
    }
    .opt-label:has(input:checked) {
        border-color: #6366f1; background: #6366f1; color: #fff;
    }
    .opt-label input { display: none; }

    .mic-btn {
        width: 72px; height: 72px; border-radius: 50%;
        font-size: 1.8em; cursor: pointer;
        display: block; margin: 0 auto 12px;
        background: #6366f1; color: #fff;
        box-shadow: 0 4px 16px rgba(99,102,241,.4);
        padding: 0;
    }
    .mic-btn.recording {
        background: #ef4444;
        animation: pulse 1s infinite;
    }
    @keyframes pulse {
        0%   { box-shadow: 0 0 0 0 rgba(239,68,68,.7); }
        70%  { box-shadow: 0 0 0 12px rgba(239,68,68,0); }
        100% { box-shadow: 0 0 0 0 rgba(239,68,68,0); }
    }

    .progress-bar {
        background: #e2e8f0; border-radius: 99px;
        height: 8px; margin-bottom: 24px; overflow: hidden;
    }
    .progress-fill {
        background: linear-gradient(90deg, #6366f1, #7c3aed);
        height: 100%; border-radius: 99px; transition: width .35s ease;
    }

    .result-score {
        font-size: 3.2em; font-weight: 800;
        color: #6366f1; margin: 16px 0 4px;
    }
    /* 모바일 대응 */
    /*@media (max-width: 420px) {
        .card { padding: 28px 20px; }
        .options-grid { grid-template-columns: 1fr; }
        h1 { font-size: 1.5em; }
    }
     */
    /* 성별선택 */
    select {
    width: 100%; padding: 14px 16px; font-size: 1.1em;
    border: 2px solid #e2e8f0; border-radius: 12px;
    margin-bottom: 16px; outline: none; transition: border .2s;
    background: #fff; cursor: pointer;
    appearance: none;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%2364748b' d='M6 8L1 3h10z'/%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: right 16px center;
}

select:focus { border-color: #6366f1; }
</style>