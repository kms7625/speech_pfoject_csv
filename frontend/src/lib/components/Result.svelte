<!--
    Result.svelte
    검사 완료 결과 화면 컴포넌트
    - 총점 표시 (점입니다 텍스트 포함)
    - 처음으로 버튼 → 아동 선택 화면으로 복귀
-->
<script>
    // props: 채점 결과, 돌아가기 콜백
    let {
        result,  // { scores: { total } }
        onBack   // () => void: 아동 선택 화면으로 복귀
    } = $props();
</script>

<div class="card">
    <h2>✅ 검사 완료!</h2>

    <!-- 총점 크게 표시 -->
    <div class="result-score">
        {result.scores.total}
        <span style="font-size: 0.4em; font-weight: 600; color: #475569;">점입니다.</span>
    </div>

    <!-- ✅ 구간별 메시지 -->
    {#if result.scores.total >= 19}
        <p style="margin-top: 16px; color: #ef4444; font-weight: 600;">
            ⚠️ 정확한 진단을 위해 전문가와 상담해보세요.
        </p>

    {:else if result.scores.total >= 10}
        <p style="margin-top: 16px; color: #f59e0b; font-weight: 600;">
            ⚠️ 일부 주의가 필요할 수 있습니다. 생활 습관을 점검해보세요.
        </p>

    {:else}
        <p style="margin-top: 16px; color: #10b981; font-weight: 600;">
            😊 현재 상태는 비교적 양호한 편입니다.
        </p>
    {/if}

    <button onclick={onBack}>처음으로</button>
</div>

<style>
.card {
    background: #fff; border-radius: 24px;
    padding: 40px 48px; max-width: 900px;
    margin: 0 auto; box-shadow: 0 24px 64px rgba(0,0,0,.28);
}
h2 { font-size: 1.6em; color: #3730a3; margin-bottom: 16px; }
.result-score {
    font-size: 3.2em; font-weight: 800;
    color: #6366f1; margin: 16px 0 4px;
}
button {
    padding: 13px 28px; font-size: 1em; font-weight: 600;
    border: none; border-radius: 12px; cursor: pointer;
    transition: transform .1s, box-shadow .1s; margin: 5px;
    background: #6366f1; color: #fff;
}
button:hover { transform: translateY(-2px); box-shadow: 0 6px 18px rgba(0,0,0,.18); }
</style>