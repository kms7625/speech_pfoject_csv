<!--
    Admin.svelte
    관리자 전체 응답 조회 화면 컴포넌트
    - 응답 데이터 테이블 (session_id, response_id, 이름, 나이, 성별, 총점, 검사일시)
    - 문항별 답변 펼치기/접기 (▼/▲)
    - 체크박스로 선택 후 일괄 삭제
    - 전체 선택/해제
    - loadData(): 부모에서 호출해 데이터 새로고침
-->
<script>
    import { getAllResponses, deleteResponses } from '$lib/api.js';

    // props: 돌아가기 콜백
    let { onBack } = $props();

    let adminData    = $state([]);         // 전체 응답 데이터 배열
    let expandedRows = $state(new Set()); // 펼쳐진 행의 response_id 집합
    let selectedIds  = $state(new Set()); // 선택된 response_id 집합

    /**
     * 응답 데이터 로드 (부모에서 bind:this로 호출)
     * 관리자 페이지 진입 시 자동 호출됨
     */
    // Svelte 5에서 외부 호출 가능한 함수는 $state + onMount 방식으로 처리
    export async function loadData() {
        const res = await getAllResponses();
        adminData = res.data;
    }
    // 컴포넌트 마운트 시 자동 로드
    import { onMount } from 'svelte';
    onMount(async () => {
        await loadData();
    });

    // 행 펼치기/접기 토글
    function toggleRow(id) {
        const next = new Set(expandedRows);
        next.has(id) ? next.delete(id) : next.add(id);
        expandedRows = next;
    }

    // 개별 체크박스 토글
    function toggleSelect(id) {
        const next = new Set(selectedIds);
        next.has(id) ? next.delete(id) : next.add(id);
        selectedIds = next;
    }

    // 전체 선택/해제
    function toggleSelectAll() {
        // 현재 전체 선택 상태면 전체 해제, 아니면 전체 선택
        selectedIds = selectedIds.size === adminData.length
            ? new Set()
            : new Set(adminData.map(r => r.response_id));
    }

    // 선택된 항목 삭제
    async function deleteSelected() {
        if (selectedIds.size === 0) return;
        if (!confirm(`${selectedIds.size}건을 삭제하시겠습니까?`)) return;
        await deleteResponses([...selectedIds]);
        // 화면에서도 제거
        adminData   = adminData.filter(r => !selectedIds.has(r.response_id));
        selectedIds = new Set();
    }
</script>

<div class="card">
    <h2>🔧 전체 응답 조회</h2>

    {#if adminData.length === 0}
        <p>저장된 응답이 없습니다.</p>
    {:else}
        <!-- 가로 스크롤 가능한 테이블 컨테이너 -->
        <div style="overflow-x: auto;">
            <table class="admin-table">
                <thead>
                    <tr>
                        <!-- 전체 선택 체크박스 -->
                        <th>
                            <input type="checkbox"
                                checked={selectedIds.size === adminData.length && adminData.length > 0}
                                onclick={toggleSelectAll}
                            />
                        </th>
                        <th style="text-align: center;">문항별<br>답변</th>
                        <th>session_id</th>
                        <th>response_id</th>
                        <th>이름</th>
                        <th>나이</th>
                        <th>성별</th>
                        <th>총점</th>
                        <th>검사일시</th>
                    </tr>
                </thead>
                <tbody>
                    {#each adminData as row}
                        <!-- 기본 데이터 행: 선택 시 파란 배경 -->
                        <tr class={selectedIds.has(row.response_id) ? 'selected-row' : ''}>
                            <td>
                                <input type="checkbox"
                                    checked={selectedIds.has(row.response_id)}
                                    onclick={() => toggleSelect(row.response_id)}
                                />
                            </td>
                            <!-- 문항별 답변 펼치기/접기 버튼 -->
                            <td>
                                <button class="expand-btn" onclick={() => toggleRow(row.response_id)}>
                                    {expandedRows.has(row.response_id) ? '▲' : '▼'}
                                </button>
                            </td>
                            <td>{row.session_id}</td>
                            <td>{row.response_id}</td>
                            <td>{row.name}</td>
                            <td>{row.age}</td>
                            <td>{row.gender}</td>
                            <td>{row.total}</td>
                            <td>{row.recorded_at}</td>
                        </tr>

                        <!-- 펼쳐지는 문항별 답변 행 (Q1~Q20 그리드) -->
                        {#if expandedRows.has(row.response_id)}
                            <tr class="expand-row">
                                <td colspan="8">
                                    <div class="expand-grid">
                                        {#each Array.from({length: 20}, (_, i) => i + 1) as n}
                                            <div class="expand-cell">
                                                <span class="q-label">Q{n}</span>
                                                <!-- 해당 문항 답변값 표시, 없으면 '-' -->
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

    <!-- 선택 삭제 버튼: 선택된 항목 없으면 비활성화 -->
    <div style="margin-bottom: 12px;">
        <button class="btn-danger" onclick={deleteSelected} disabled={selectedIds.size === 0}>
            🗑 선택 삭제 ({selectedIds.size}건)
        </button>
    </div>
    <button onclick={onBack}>돌아가기</button>
</div>

<style>
.card {
    background: #fff; border-radius: 24px;
    padding: 40px 48px; max-width: 900px;
    margin: 0 auto; box-shadow: 0 24px 64px rgba(0,0,0,.28);
}
h2 { font-size: 1.6em; color: #3730a3; margin-bottom: 16px; }
/* 관리자 테이블 */
.admin-table {
    width: 100%; border-collapse: collapse;
    font-size: 0.9em; margin-bottom: 20px;
}
.admin-table th {
    background: #6366f1; color: #fff;
    padding: 10px 12px; text-align: left; white-space: nowrap;
}
.admin-table td {
    padding: 10px 12px; border-bottom: 1px solid #e2e8f0; white-space: nowrap;
}
/* 문항별 답변 펼치기 버튼 */
.expand-btn {
    padding: 4px 8px; font-size: 0.8em;
    background: #e2e8f0; color: #475569;
    border-radius: 6px; margin: 0;
}
.expand-btn:hover { background: #cbd5e1; transform: none; box-shadow: none; }
/* 펼쳐진 문항별 답변 행 */
.expand-row td { background: #f8fafc; padding: 16px 12px; }
/* Q1~Q20 그리드 (10열) */
.expand-grid {
    display: grid; grid-template-columns: repeat(10, 1fr); gap: 8px;
}
.expand-cell {
    display: flex; flex-direction: column;
    align-items: center; gap: 4px;
    background: #fff; border: 1px solid #e2e8f0;
    border-radius: 8px; padding: 8px;
}
.q-label { font-size: 0.75em; color: #94a3b8; font-weight: 600; } /* Q1, Q2... */
.q-value { font-size: 1.1em; font-weight: 700; color: #6366f1; } /* 답변값 */
/* 선택된 행 배경색 */
.selected-row td { background: #eef2ff; }
button {
    padding: 13px 28px; font-size: 1em; font-weight: 600;
    border: none; border-radius: 12px; cursor: pointer;
    transition: transform .1s, box-shadow .1s; margin: 5px;
    background: #6366f1; color: #fff;
}
button:hover  { transform: translateY(-2px); box-shadow: 0 6px 18px rgba(0,0,0,.18); }
button:disabled { background: #e2e8f0; color: #94a3b8; transform: none; cursor: not-allowed; }
.btn-danger { background: #ef4444; }
.btn-danger:hover { background: #dc2626; }
p { color: #475569; }
</style>