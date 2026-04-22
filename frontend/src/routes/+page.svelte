<script>
    import { onMount } from 'svelte';
    import { getChildren,
             createChild,
             getQuestions,
             submitAnswers,
             generateTTS,
             deleteChild,
             saveDraft,
             loadDraft,
             deleteDraft,
             getAllResponses,
             deleteResponses} from '$lib/api.js'

    // 관리자 로그인 정보(하드코딩)
    const ADMIN_ID = 'admin'
    const ADMIN_PASSWORD = 'admin1234';

    // 관리자 관련
    let showAdminModal  = $state(false); // 모달 표시 여부
    let adminIdInput    = $state('');    // 입력한 아이디
    let adminPwInput    = $state('');    // 입력한 비밀번호
    let adminError      = $state('');    // 오류 메시지
    let isAdminLoggedIn = $state(false); // 로그인 상태 유지

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
    // 임시저장 관련
    let draftSavedAt = $state(null);  // 마지막 저장 시각 표시
    let autoSaveTimer = $state(null); // 자동저장 타이머
    // 미답변 문항 번호 관련
    let unanswered = $derived(
        questions
            .filter(q => answers[q.id] === undefined)
            .map(q => q.id)
    );
    // 개인정보 동의 체크박스 상태
    let consentChecked = $state(false);
    // tts 재생 속도(0.5 ~ 2.0)
    let ttsSpeed = $state(1.0);
    // 현재 재생 중인 tts 오디오 추적
    let currentAudio = $state(null);
    // 관리자 조회
    let adminData = $state([]);
    // 펼쳐진 행 추적(response_id 저장)
    let expandedRows = $state(new Set());
    // 선택된 response_id 목록
    let selectedIds = $state(new Set());

    // 행 펼치기/접기
    function toggleRow(id) {
        const next = new Set(expandedRows);
        if (next.has(id)) {
            next.delete(id);
        } else {
            next.add(id);
        }
        expandedRows = next;
    }

    // 체크박스 토글
function toggleSelect(id) {
    const next = new Set(selectedIds);
    if (next.has(id)) {
        next.delete(id);
    } else {
        next.add(id);
    }
    selectedIds = next;
}

// 전체 선택/해제
function toggleSelectAll() {
    if (selectedIds.size === adminData.length) {
        selectedIds = new Set(); // 전체 해제
    } else {
        selectedIds = new Set(adminData.map(r => r.response_id)); // 전체 선택
    }
}

// 선택 항목 삭제
async function deleteSelected() {
    if (selectedIds.size === 0) return;
    if (!confirm(`${selectedIds.size}건을 삭제하시겠습니까?`)) return;

    await deleteResponses([...selectedIds]);
    // 화면에서 제거
    adminData = adminData.filter(r => !selectedIds.has(r.response_id));
    selectedIds = new Set();
}


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

        const stream = await navigator.mediaDevices.getUserMedia({audio: true});
        chunks = [];

        // 녹음 시작 시 현재 문항 답변 초기화
        if (currentQuestion) {
            answers[currentQuestion.id] = undefined;
        }

        // 5초 무음 타이머 시작
        const audioCtx2  = new AudioContext();
        const src2       = audioCtx2.createMediaStreamSource(stream);
        const analyser2  = audioCtx2.createAnalyser();
        analyser2.fftSize = 512;
        src2.connect(analyser2);
        const dataArr2 = new Uint8Array(analyser2.frequencyBinCount);

        let speechDetected = false; // 한 번이라도 말했는지
        let quietStart     = null;  // 조용해진 시작 시각

        const SPEECH_THRESHOLD = 15;  // 말소리 감지 임계값 (높이면 덜 민감)
        const QUIET_DURATION   = 800; // 말 끊긴 후 몇 ms 뒤에 종료 (짧을수록 빠름)
        const MAX_WAIT         = 5000; // 아무 말 없을 때 최대 대기 (ms)

        // 아무 말 없을 때 최대 대기 타이머
        silenceTimer = setTimeout(async () => {
            if (isRecording && !isProcessing) {
                mediaRecorder.stop();
                await new Promise(r => setTimeout(r, 100));
                if (!isProcessing) await speak('말씀해 주세요');
            }
        }, MAX_WAIT);

        const voiceInterval = setInterval(() => {
            if (!isRecording) {
                clearInterval(voiceInterval);
                audioCtx2.close();
                return;
            }
            analyser2.getByteFrequencyData(dataArr2);
            const avg = dataArr2.reduce((s, v) => s + v, 0) / dataArr2.length;

            if (avg > SPEECH_THRESHOLD) {
                // 말소리 감지 — 최대 대기 타이머 취소
                clearTimeout(silenceTimer);
                silenceTimer = null;
                speechDetected = true;
                quietStart = null;
            } else if (speechDetected) {
                // 말하다가 조용해진 경우
                if (!quietStart) quietStart = Date.now();
                if (Date.now() - quietStart > QUIET_DURATION) {
                    // QUIET_DURATION 동안 조용하면 즉시 종료
                    clearInterval(voiceInterval);
                    if (isRecording) mediaRecorder.stop();
                }
            }
        }, 100);

        mediaRecorder = new MediaRecorder(stream);
        mediaRecorder.ondataavailable = (e) => {
            if (e.data.size > 0) chunks.push(e.data);
        };
        mediaRecorder.onstop = async () => {
            clearTimeout(silenceTimer); // 타이머 취소
            clearInterval(voiceInterval); // 볼륨 감지 루프 정리
            audioCtx2.close();
            isProcessing = true; // stt처리 시작 즉시 표시
            stream.getTracks().forEach(t => t.stop());
            await processRecording();
        };

        mediaRecorder.start();
        isRecording = true;
    }


    // 녹음 완료 후 STT 처리
    async function processRecording() {
        // 혹시 남아있는 silenceTimer 확실히 취소
        clearTimeout(silenceTimer);
        silenceTimer = null;
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
                await saveCurrentDraft(); // 인식 성공 시 즉시 저장
                // 인식 성공 확인 사운드(높은 음 두번)
                playSound(660, 0.15);
                setTimeout(() => playSound(880, 0.2), 160);
                setTimeout(() => playSound(1100, 0.25), 320);

                // 다음 문항 자동 이동
                const curIdx = questions.findIndex(q => q.id === currentQuestion.id);
                const nextQ  = questions[curIdx + 1];
                if (nextQ) {
                    // 1.5초 후 다음 문항 tts 재생 + 자동 녹음
                    setTimeout(async () => {
                        // 다음 문항으로 스크롤
                        document.getElementById(`question-${nextQ.id}`)
                            ?.scrollIntoView({ behavior: 'smooth', block: 'center'});
                        await speak(nextQ.text, nextQ);
                    }, 1500);
                }
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
        // 번호로 답변
        if (text.includes('1번') || text.includes('일번') || text.includes('하나')) return 0;
        if (text.includes('2번') || text.includes('이번') || text.includes('둘') || text.includes('두번')) return 1;
        if (text.includes('3번') || text.includes('삼번') || text.includes('셋') || text.includes('세번')) return 2;
        if (text.includes('4번') || text.includes('사번') || text.includes('넷') || text.includes('네번')) return 3;

        // 0점 키워드
        if (text.includes('전혀') || text.includes('없') || text.includes('아니') ||
            text.includes('안') || text.includes('절대')) return 0;

        // 1점 키워드
        if (text.includes('약간') || text.includes('가끔') || text.includes('조금') ||
            text.includes('드물') || text.includes('별로') || text.includes('稀')) return 1;

        // 2점 키워드
        if (text.includes('꽤') || text.includes('자주') || text.includes('많') ||
            text.includes('종종') || text.includes('보통') || text.includes('그렇')) return 2;

        // 3점 키워드
        if (text.includes('매우') || text.includes('항상') || text.includes('심') ||
            text.includes('굉장') || text.includes('엄청') || text.includes('늘') ||
            text.includes('언제나') || text.includes('매일')) return 3;
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
        // 재생 중인 오디오 있으면 중지
        if (currentAudio) {
            currentAudio.pause();
            currentAudio.currentTime = 0;
            currentAudio = null;
        }
        const res = await generateTTS(text, ttsSpeed);
        if (res && res.status === 'success') {
            const audio = new Audio(`http://localhost:8000/api/tts/file/${res.filename}`);
            // 재생 속도 적용
            audio.playbackRate = ttsSpeed;
            // 음성 재생 끝나면 자동 녹음 시작
            audio.onended = async () => {
                if (question) {
                    currentQuestion = question;
                    await startRecording();
                }
            };
            currentAudio = audio;
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

    // 아동 선택 시 동의화면으로 이동
    function goToConsent(child) {
        selectedChild = child;
        consentChecked = false;
        phase = 'consent';
    }

    // 동의 완료 후 검사 시작
    async function startChecklist() {
        answers = {};
        result = null;
        startTime = Date.now(); // 검사 시작 시간 기록
        phase = 'checklist';

        // 기존 임시저장 있으면 불러오기
        const res = await loadDraft(selectedChild.id);
        if (res.draft) {
            res.draft.answers.forEach(a => {
                answers[a.question_id] = a.value;
            });
            draftSavedAt = res.draft.saved_at;
        }
    }

    // 현재 답변 임시저장
    async function saveCurrentDraft() {
        const answerList = Object.entries(answers)
            .filter(([qid, val]) => val !== undefined)
            .map(([qid, val]) => ({
                question_id: parseInt(qid),
                value: val
            }));
        if (answerList.length === 0) return;

        const res = await saveDraft(selectedChild.id, answerList);
        if (res.status === 'success') {
            draftSavedAt = res.saved_at;
        }
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
        // 제출 완료 시 임시저장 삭제 + 타이머 정리
        clearInterval(autoSaveTimer);
        await deleteDraft(selectedChild.id);

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

<!-- 관리자 로그인 모달 -->
{#if showAdminModal}
    <div class="modal-overlay"
    role="button"
    tabindex="0"
    onclick={() => showAdminModal = false}
    onkeydown={(e) => e.key === 'Escape' && (showAdminModal = false)}>
    <div class="modal-box"
        role="dialog"
         tabindex="0"
        onclick={(e) => e.stopPropagation()}
        onkeydown={(e) => e.stopPropagation()}>
            <h2>🔒 관리자 로그인</h2>

            <input
                type="text"
                placeholder="아이디"
                bind:value={adminIdInput}
                style="margin-bottom: 12px;"
            />
            <input
                type="password"
                placeholder="비밀번호"
                bind:value={adminPwInput}
                onkeydown={async (e) => {
                    if (e.key !== 'Enter') return;
                    if (adminIdInput === ADMIN_ID && adminPwInput === ADMIN_PASSWORD) {
                        isAdminLoggedIn = true;
                        showAdminModal = false;
                        const res = await getAllResponses();
                        adminData = res.data;
                        phase = 'admin';
                    } else {
                        adminError = '아이디 또는 비밀번호가 틀렸습니다.';
                    }
                }}
            />

            {#if adminError}
                <p style="color: #ef4444; font-size: 0.9em; margin-top: 8px;">
                    {adminError}
                </p>
            {/if}

            <div style="display: flex; gap: 12px; margin-top: 20px;">
                <button class="btn-outline" onclick={() => showAdminModal = false}>
                    취소
                </button>
                <button onclick={async () => {
                    if (adminIdInput === ADMIN_ID && adminPwInput === ADMIN_PASSWORD) {
                        isAdminLoggedIn = true;
                        showAdminModal = false;
                        const res = await getAllResponses();
                        adminData = res.data;
                        phase = 'admin';
                    } else {
                        adminError = '아이디 또는 비밀번호가 틀렸습니다.';
                    }
                }}>확인</button>
            </div>
        </div>
    </div>
{/if}



<!-- 아동 선택 화면 -->
{#if phase === 'select'}
    <div class="card">
        <h1>🧠 ADHD 체크리스트</h1>
        <div style="display: flex; justify-content: flex-end; margin-bottom: 16px;">
            <button onclick={async () => {
                if (isAdminLoggedIn) {
                    getAllResponses().then(res => {
                        adminData = res.data;
                        phase = 'admin';
                    });
                } else {
                    adminIdInput   = '';
                    adminPwInput   = '';
                    adminError     = '';
                    showAdminModal = true;
                }
            }}>🔧 관리자</button>
        </div>

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
                    <button onclick={() => goToConsent(child)}>
                        {child.name} ({child.age}세 / {child.gender})
                    </button>
                    <button onclick={() => removeChild(child.id)}>삭제</button>
                </div>
            {/each}
        {/if}
    </div>

<!-- 개인정보 동의 화면 -->
{:else if phase === 'consent'}
    <div class="card">
        <h2>📋 개인정보 수집 및 이용 동의</h2>
        <p class="consent-name">{selectedChild.name} ({selectedChild.age}세 / {selectedChild.gender})</p>

        <div class="consent-box">
            <p class="consent-title">수집하는 개인정보 항목</p>
            <p>이름, 나이, 성별, ADHD 체크리스트 응답 결과, 응답 시간</p>

            <p class="consent-title">수집 및 이용 목적</p>
            <p>ADHD 증상 선별 검사 및 결과 분석</p>

            <p class="consent-title">보유 및 이용 기간</p>
            <p>검사 완료 후 연구 목적으로 보관되며, 요청 시 즉시 삭제합니다.</p>

            <p class="consent-title">동의 거부 권리</p>
            <p>개인정보 수집에 동의하지 않을 권리가 있으며, 동의 거부 시 검사 진행이 불가합니다.</p>
        </div>

        <label class="consent-check">
            <input type="checkbox" bind:checked={consentChecked} />
            위 개인정보 수집 및 이용에 동의합니다.
        </label>

        <div style="display: flex; gap: 12px; margin-top: 20px;">
            <button onclick={() => phase = 'select'}>취소</button>
            <button onclick={startChecklist} disabled={!consentChecked}>
                동의 후 검사 시작
            </button>
        </div>
    </div>

<!-- 체크리스트 화면 -->
{:else if phase === 'checklist'}
    <div class="card">
        <h2>{selectedChild.name} 검사</h2>

        <!-- TTS 속도 조절 -->
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;">
            <span style="font-size: 0.95em; color: #475569; white-space: nowrap;">
                🔊 재생 속도
            </span>
            <input
                type="range"
                min="0.5"
                max="2.0"
                step="0.1"
                bind:value={ttsSpeed}
                style="flex: 1;"
            />
            <span style="font-size: 0.95em; color: #6366f1; font-weight: 700; width: 36px;">
                {ttsSpeed}x
            </span>
        </div>

        {#each questions as q}
            <div class="question-box" id="question-{q.id}">
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
                                onclick={async () => {
                                    if (answers[q.id] === Number(opt.value)) {
                                        // 이미 선택된 항목 클릭 시 해제
                                        answers[q.id] = undefined;
                                    } else {
                                        answers[q.id] = Number(opt.value);
                                    }
                                    await saveCurrentDraft();
                                }}
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

<!-- 관리자 화면 -->
{:else if phase === 'admin'}
    <div class="card">
        <h2>🔧 전체 응답 조회</h2>

        {#if adminData.length === 0}
            <p>저장된 응답이 없습니다.</p>
        {:else}
            <div style="overflow-x: auto;">
                <table class="admin-table">
                    <thead>
                        <tr>
                            <th>
                                <!-- 전체선택 체크박스 -->
                                <input type="checkbox"
                                    checked={selectedIds.size === adminData.length && adminData.length > 0}
                                    onclick={toggleSelectAll}
                                />
                            </th>
                            <th style="text-align: center;">문항별<br>답변</th>
                            <th>response_id</th>
                            <th>이름</th>
                            <th>나이</th>
                            <th>성별</th>
                            <th>부주의</th>
                            <th>과잉행동</th>
                            <th>총점</th>
                            <th>응답시간(초)</th>
                            <th>검사일시</th>
                        </tr>
                    </thead>
                    <tbody>
                        {#each adminData as row}
                            <!-- 기본 행 -->
                            <tr class={selectedIds.has(row.response_id) ? 'selected-row' : ''}>
                                <td>
                                    <input type="checkbox"
                                           checked={selectedIds.has(row.response_id)}
                                           onclick={() => toggleSelect(row.response_id)}
                                   />
                                </td>
                                <td>
                                    <button class="expand-btn"
                                        onclick={() => toggleRow(row.response_id)}>
                                        {expandedRows.has(row.response_id) ? '▲' : '▼'}
                                    </button>
                                </td>
                                <td>{row.response_id}</td>
                                <td>{row.name}</td>
                                <td>{row.age}</td>
                                <td>{row.gender}</td>
                                <td>{row.inattention}</td>
                                <td>{row.hyperactivity}</td>
                                <td>{row.total}</td>
                                <td>{row.response_time}</td>
                                <td>{row.recorded_at}</td>
                            </tr>
                            <!-- 펼쳐지는 문항별 응답 행 -->
                            {#if expandedRows.has(row.response_id)}
                                <tr class="expand-row">
                                    <td colspan="10">
                                        <div class="expand-grid">
                                            {#each Array.from({length: 20}, (_, i) => i + 1) as n}
                                                <div class="expand-cell">
                                                    <span class="q-label">Q{n}</span>
                                                    <span class="q-value">{row[`q${n}`] ?? '-'}</span>
                                                </div>
                                            {/each}
                                        </div>
                                    </td>
                                </tr>
                            {/if}
                        {/each}
                    </tbody>
                </table>
            </div>
        {/if}
        <div style="margin-bottom: 12px;">
            <button class="btn-danger"
                onclick={deleteSelected}
                disabled={selectedIds.size === 0}>
                🗑 선택 삭제 ({selectedIds.size}건)
            </button>
        </div>
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

    input[type="text"], input[type="number"] , input[type="password"]{
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

.consent-name {
    font-size: 1.1em; color: #475569;
    margin-bottom: 20px; padding: 10px 16px;
    background: #f1f5f9; border-radius: 10px;
}
.consent-box {
    background: #f8fafc; border: 1px solid #e2e8f0;
    border-radius: 14px; padding: 24px; margin-bottom: 24px;
    font-size: 0.95em; color: #334155; line-height: 1.8;
}
.consent-title {
    font-weight: 700; color: #1e293b;
    margin-top: 16px; margin-bottom: 4px;
}
.consent-title:first-child { margin-top: 0; }
.consent-check {
    display: flex; align-items: center; gap: 10px;
    font-size: 1em; font-weight: 600; color: #1e293b;
    cursor: pointer; padding: 16px;
    border: 2px solid #e2e8f0; border-radius: 12px;
    transition: border .2s, background .2s;
}
.consent-check:has(input:checked) {
    border-color: #6366f1; background: #eef2ff;
}
.consent-check input[type="checkbox"] {
    width: 20px; height: 20px;
    accent-color: #6366f1; cursor: pointer;
}

/* 관리자 */
.admin-table {
    width: 100%; border-collapse: collapse;
    font-size: 0.9em; margin-bottom: 20px;
}
.admin-table th {
    background: #6366f1; color: #fff;
    padding: 10px 12px; text-align: left;
    white-space: nowrap;
}
.admin-table td {
    padding: 10px 12px; border-bottom: 1px solid #e2e8f0;
    white-space: nowrap;
}


/* 펼쳐지는 문항별 응답 행 */
.expand-btn {
    padding: 4px 8px; font-size: 0.8em;
    background: #e2e8f0; color: #475569;
    border-radius: 6px; margin: 0;
}
.expand-btn:hover { background: #cbd5e1; transform: none; box-shadow: none; }

.expand-row td { background: #f8fafc; padding: 16px 12px; }

.expand-grid {
    display: grid;
    grid-template-columns: repeat(10, 1fr);
    gap: 8px;
}
.expand-cell {
    display: flex; flex-direction: column;
    align-items: center; gap: 4px;
    background: #fff; border: 1px solid #e2e8f0;
    border-radius: 8px; padding: 8px;
}
.q-label {
    font-size: 0.75em; color: #94a3b8; font-weight: 600;
}
.q-value {
    font-size: 1.1em; font-weight: 700; color: #6366f1;
}

.selected-row td {
    background: #eef2ff;
}

.btn-danger {
    background: #ef4444;
}
.btn-danger:hover { background: #dc2626; }

/* 관리자 로그인 */
    .modal-overlay {
    position: fixed; inset: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex; align-items: center; justify-content: center;
    z-index: 100;
}
.modal-box {
    background: #fff; border-radius: 20px;
    padding: 36px 40px; width: 100%; max-width: 400px;
    box-shadow: 0 24px 64px rgba(0,0,0,.3);
}
.btn-outline {
    background: #fff; color: #6366f1;
    border: 2px solid #6366f1;
}
.btn-outline:hover { background: #f0f0ff; }

</style>

