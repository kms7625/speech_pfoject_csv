<!--
    SelectChild.svelte
    아동 선택 화면 컴포넌트
    - 아동 등록 (이름/나이/성별 입력)
    - 아동 목록 표시 및 선택
    - 아동 삭제
    - 다크모드 토글 버튼
    - 관리자 버튼
-->
<script>
    import { createChild, deleteChild, getLatestResponse } from '$lib/api.js';

    // props: 아동 목록(양방향), 다크모드(양방향), 선택 콜백, 관리자 클릭 콜백
    let {
        children      = $bindable([]),
        darkMode      = $bindable(false),
        onSelect,       // (child) => void: 아동 선택 시 호출
        onAdminClick    // () => void: 관리자 버튼 클릭 시 호출
    } = $props();

    // 이전 검사 결과 팝업 관련
    let showHistoryPopup = $state(false); // 팝업 표시 여부
    let historyData      = $state(null);  // 최근 검사 결과 데이터
    let historyChild     = $state(null);  // 팝업 대상 아동


    // 아동 등록 입력 상태
    let newName   = $state('');
    let newAge    = $state('');
    let newGender = $state('');

    // 아동 등록: 이름/나이/성별 모두 입력했을 때만 실행
    async function addChild() {
        if (!newName || !newAge || !newGender) return;
        const res = await createChild(newName, parseInt(newAge), newGender);
        children  = [...children, res.child]; // 목록에 추가
        // 입력 초기화
        newName = ''; newAge = ''; newGender = '';
    }

    // 아동 삭제: 백엔드에서 삭제 후 목록에서 제거
    // children.py에서 drafts.csv 임시저장도 함께 삭제됨
    async function removeChild(childId) {
        await deleteChild(childId);
        children = children.filter(c => c.id !== childId);
    }
</script>

<div class="card">
    <h1>🧠 ADHD 체크리스트</h1>

    <!-- 상단 우측: 다크모드 토글 + 관리자 버튼 -->
    <div style="display: flex; justify-content: flex-end; align-items: center; gap: 8px; margin-bottom: 16px;">
        <button class="btn-mode" onclick={() => darkMode = !darkMode}>
            {darkMode ? '☀️ 라이트' : '🌙 다크'}
        </button>
        <button onclick={onAdminClick}>🔧 관리자</button>
    </div>

    <!-- 아동 등록 섹션 -->
    <h2>아동 등록</h2>
    <input bind:value={newName} placeholder="이름" type="text" />
    <input bind:value={newAge}  placeholder="나이" type="number" />
    <!-- 성별 선택 드롭다운 -->
    <select bind:value={newGender}>
        <option value="">성별 선택</option>
        <option value="남">남</option>
        <option value="여">여</option>
    </select>
    <button onclick={addChild}>등록</button>

    <!-- 아동 선택 섹션 -->
    <h2>아동 선택</h2>
    {#if children.length === 0}
        <p>등록된 아동이 없습니다.</p>
    {:else}
        {#each children as child}
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                <!-- 아동 선택 시 consent(개인정보 동의) 화면으로 이동 -->
                <button onclick={async () => {
                    const res = await getLatestResponse(child.id);
                    if (res.status === 'found') {
                        // 이전 검사 기록 있으면 팝업 표시
                        historyChild = child;
                        historyData  = res.data;
                        showHistoryPopup = true;
                    } else {
                        // 없으면 바로 검사 시작
                        onSelect(child);
                    }
                }}>
                    {child.name} ({child.age}세 / {child.gender})
                </button>
                <button class="btn-danger" onclick={() => removeChild(child.id)}>삭제</button>
            </div>
        {/each}
    {/if}
    <!-- 이전 검사 결과 팝업 -->
    {#if showHistoryPopup && historyData}
        <div class="popup-overlay"
            role="button"
            tabindex="0"
            onclick={() => showHistoryPopup = false}
            onkeydown={(e) => e.key === 'Escape' && (showHistoryPopup = false)}>
            <div class="popup-box"
                role="dialog"
                tabindex="0"
                onclick={(e) => e.stopPropagation()}
                onkeydown={(e) => e.stopPropagation()}>

                <h3>📋 이전 검사 기록</h3>
                <p class="popup-name">{historyChild.name} ({historyChild.age}세 / {historyChild.gender})</p>

                <div class="popup-score">{historyData.total}<span style="font-size:0.4em; color:#475569;">점</span></div>
                <p class="popup-date">검사일시: {historyData.recorded_at}</p>

                <div style="display: flex; gap: 12px; margin-top: 24px;">
                    <button class="btn-outline" onclick={() => showHistoryPopup = false}>닫기</button>
                    <button onclick={() => { showHistoryPopup = false; onSelect(historyChild); }}>
                        재검사
                    </button>
                </div>
            </div>
        </div>
    {/if}
</div>

<style>
.card {
    background: #fff; border-radius: 24px;
    padding: 40px 48px; max-width: 900px;
    margin: 0 auto; box-shadow: 0 24px 64px rgba(0,0,0,.28);
}
h1 { font-size: 1.9em; color: #3730a3; margin-bottom: 8px; }
h2 { font-size: 1.6em; color: #3730a3; margin-bottom: 16px; }
input[type="text"], input[type="number"] {
    width: 100%; padding: 14px 16px; font-size: 1.1em;
    border: 2px solid #e2e8f0; border-radius: 12px;
    margin-bottom: 16px; outline: none; transition: border .2s;
    box-sizing: border-box;
}
input:focus { border-color: #6366f1; }
button {
    padding: 13px 28px; font-size: 1em; font-weight: 600;
    border: none; border-radius: 12px; cursor: pointer;
    transition: transform .1s, box-shadow .1s; margin: 5px;
    background: #6366f1; color: #fff;
}
button:hover  { transform: translateY(-2px); box-shadow: 0 6px 18px rgba(0,0,0,.18); }
button:active { transform: translateY(0); }
/* 삭제 버튼 */
.btn-danger { background: #ef4444; }
.btn-danger:hover { background: #dc2626; }
/* 다크모드 토글 버튼 */
.btn-mode {
    padding: 8px 16px; font-size: 0.85em;
    background: #e2e8f0; color: #475569; border-radius: 20px;
}
/* 성별 선택 드롭다운 */
select {
    width: 100%; padding: 14px 16px; font-size: 1.1em;
    border: 2px solid #e2e8f0; border-radius: 12px;
    margin-bottom: 16px; outline: none; transition: border .2s;
    background: #fff; cursor: pointer; appearance: none;
    /* 커스텀 드롭다운 화살표 */
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%2364748b' d='M6 8L1 3h10z'/%3E%3C/svg%3E");
    background-repeat: no-repeat; background-position: right 16px center;
    box-sizing: border-box;
}
select:focus { border-color: #6366f1; }
p { color: #475569; }

/* 이전 검사 결과 팝업 */
.popup-overlay {
    position: fixed; inset: 0;
    background: rgba(0,0,0,0.5);
    display: flex; align-items: center; justify-content: center;
    z-index: 100;
}
.popup-box {
    background: #fff; border-radius: 20px;
    padding: 36px 40px; width: 100%; max-width: 380px;
    box-shadow: 0 24px 64px rgba(0,0,0,.3);
    text-align: center;
}
.popup-box h3 { font-size: 1.3em; color: #3730a3; margin-bottom: 12px; }
.popup-name {
    font-size: 1em; color: #475569;
    padding: 8px 14px; background: #f1f5f9;
    border-radius: 8px; margin-bottom: 20px;
    display: inline-block;
}
.popup-score {
    font-size: 3em; font-weight: 800;
    color: #6366f1; margin: 8px 0;
}
.popup-date { font-size: 0.85em; color: #94a3b8; margin-top: 4px; }
</style>