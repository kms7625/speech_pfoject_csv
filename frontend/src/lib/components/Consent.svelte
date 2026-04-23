<!--
    Consent.svelte
    개인정보 수집 및 이용 동의 화면 컴포넌트
    - 선택된 아동 정보 표시
    - 개인정보 수집 항목/목적/기간/거부권 안내
    - 동의 체크박스 체크 후 검사 시작 가능
-->
<script>
    // props: 선택된 아동 정보, 동의 완료 콜백, 취소 콜백
    let {
        selectedChild, // { name, age, gender }
        onAgree,       // () => void: 동의 후 검사 시작
        onCancel       // () => void: 취소 → 아동 선택 화면으로 복귀
    } = $props();

    // 동의 체크박스 상태 (false면 검사 시작 버튼 비활성화)
    let consentChecked = $state(false);
</script>

<div class="card">
    <h2>📋 개인정보 수집 및 이용 동의</h2>

    <!-- 선택된 아동 정보 표시 -->
    <p class="consent-name">
        {selectedChild.name} ({selectedChild.age}세 / {selectedChild.gender})
    </p>

    <!-- 개인정보 수집 안내 박스 -->
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

    <!-- 동의 체크박스: 체크해야 검사 시작 버튼 활성화 -->
    <label class="consent-check">
        <input type="checkbox" bind:checked={consentChecked} />
        위 개인정보 수집 및 이용에 동의합니다.
    </label>

    <div style="display: flex; gap: 12px; margin-top: 20px;">
        <button class="btn-outline" onclick={onCancel}>취소</button>
        <!-- disabled: 동의 체크 안 하면 버튼 비활성화 -->
        <button onclick={onAgree} disabled={!consentChecked}>
            동의 후 검사 시작
        </button>
    </div>
</div>

<style>
.card {
    background: #fff; border-radius: 24px;
    padding: 40px 48px; max-width: 900px;
    margin: 0 auto; box-shadow: 0 24px 64px rgba(0,0,0,.28);
}
h2 { font-size: 1.6em; color: #3730a3; margin-bottom: 16px; }
/* 선택된 아동 이름/나이/성별 표시 */
.consent-name {
    font-size: 1.1em; color: #475569;
    margin-bottom: 20px; padding: 10px 16px;
    background: #f1f5f9; border-radius: 10px;
}
/* 개인정보 안내 박스 */
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
/* 동의 체크박스 라벨 */
.consent-check {
    display: flex; align-items: center; gap: 10px;
    font-size: 1em; font-weight: 600; color: #1e293b;
    cursor: pointer; padding: 16px;
    border: 2px solid #e2e8f0; border-radius: 12px;
    transition: border .2s, background .2s;
}
/* 체크 시 파란 테두리/배경 */
.consent-check:has(input:checked) {
    border-color: #6366f1; background: #eef2ff;
}
.consent-check input[type="checkbox"] {
    width: 20px; height: 20px; accent-color: #6366f1; cursor: pointer;
}
button {
    padding: 13px 28px; font-size: 1em; font-weight: 600;
    border: none; border-radius: 12px; cursor: pointer;
    transition: transform .1s, box-shadow .1s; margin: 5px;
    background: #6366f1; color: #fff;
}
button:hover  { transform: translateY(-2px); box-shadow: 0 6px 18px rgba(0,0,0,.18); }
button:disabled { background: #e2e8f0; color: #94a3b8; transform: none; cursor: not-allowed; }
.btn-outline {
    background: #fff; color: #6366f1; border: 2px solid #6366f1;
}
.btn-outline:hover { background: #f0f0ff; }
p { color: #334155; }
</style>