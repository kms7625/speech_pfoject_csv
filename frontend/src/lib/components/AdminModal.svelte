<!--
    AdminModal.svelte
    관리자 로그인 모달 컴포넌트
    - 아이디/비밀번호 입력 후 확인 버튼 or 엔터키로 인증
    - 인증 성공 시 부모로부터 전달받은 onLogin 콜백 실행
    - 인증 실패 시 오류 메시지 표시..
-->
<script>
    // props: 모달 표시 여부(양방향), 로그인 성공 콜백
    let { showAdminModal = $bindable(), onLogin } = $props();

    // 관리자 계정 정보 (하드코딩 방식의 단순 인증)
    const ADMIN_ID       = 'admin';
    const ADMIN_PASSWORD = 'admin1234';

    let adminIdInput = $state(''); // 입력한 아이디
    let adminPwInput = $state(''); // 입력한 비밀번호
    let adminError   = $state(''); // 오류 메시지

    // 로그인 확인
    async function confirm() {
        if (adminIdInput === ADMIN_ID && adminPwInput === ADMIN_PASSWORD) {
            adminError     = '';
            showAdminModal = false;
            await onLogin(); // 부모에서 전달받은 로그인 성공 콜백 실행
        } else {
            adminError = '아이디 또는 비밀번호가 틀렸습니다.';
        }
    }

    // 모달 닫기
    function close() {
        showAdminModal = false;
        adminError     = '';
    }
</script>

{#if showAdminModal}
    <!-- 배경 오버레이 클릭 시 모달 닫기 -->
    <div class="modal-overlay"
        role="button"
        tabindex="0"
        onclick={close}
        onkeydown={(e) => e.key === 'Escape' && close()}>

        <!-- 모달 박스: 클릭 이벤트 버블링 차단 -->
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
            <!-- 엔터키로도 로그인 가능 -->
            <input
                type="password"
                placeholder="비밀번호"
                bind:value={adminPwInput}
                onkeydown={async (e) => { if (e.key === 'Enter') await confirm(); }}
            />

            <!-- 오류 메시지 -->
            {#if adminError}
                <p style="color: #ef4444; font-size: 0.9em; margin-top: 8px;">{adminError}</p>
            {/if}

            <div style="display: flex; gap: 12px; margin-top: 20px;">
                <button class="btn-outline" onclick={close}>취소</button>
                <button onclick={confirm}>확인</button>
            </div>
        </div>
    </div>
{/if}

<style>
/* 화면 전체를 덮는 반투명 배경 */
.modal-overlay {
    position: fixed; inset: 0;
    background: rgba(0,0,0,0.5);
    display: flex; align-items: center; justify-content: center;
    z-index: 100;
}
/* 모달 박스 */
.modal-box {
    background: #fff; border-radius: 20px;
    padding: 36px 40px; width: 100%; max-width: 400px;
    box-shadow: 0 24px 64px rgba(0,0,0,.3);
}
h2 { font-size: 1.6em; color: #3730a3; margin-bottom: 16px; }
input[type="text"], input[type="password"] {
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
button:hover { transform: translateY(-2px); box-shadow: 0 6px 18px rgba(0,0,0,.18); }
/* 테두리만 있는 버튼 스타일 */
.btn-outline {
    background: #fff; color: #6366f1; border: 2px solid #6366f1;
}
.btn-outline:hover { background: #f0f0ff; }
</style>