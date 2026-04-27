// 백엔드 주소 - 모든 요청 여기로감
const BASE = 'https://tweet-isolated-civil.ngrok-free.dev/api';

// 공통 요청 함수 - GET/POST 둘 다 여기서 처리
async function request(method, path, body = null) {
    const options = {
        method,
        headers: { 'Content-Type': 'application/json',
                   'ngrok-skip-browser-warning': 'true', // ngrok 경고 페이지 스킵
        },
    };
    if (body) {
        options.body = JSON.stringify(body);
    }
    const res = await fetch(`${BASE}${path}`, options);

    // 응답 상태 확인 후 JSON 반환
    const data = await res.json();
    console.log(`[${method} ${path}]`, res.status, data);
    return data;
}

// 아동 관련
export const getChildren = () => request('GET', '/children');
export const createChild = (name, age, gender) =>
    request('POST', '/children', { name, age, gender });
// 특정 아동의 가장 최근 검사 결과 조회
export async function getLatestResponse(childId) {
    return request('GET', `/score/latest/${childId}`);
}
// 삭제 관련
export const deleteChild = (childId) =>
    request('DELETE', `/children/${childId}`);

// 문항 관련
export const getQuestions = () => request('GET', '/questions');

// 점수 관련
export const submitAnswers = (child_id, answers, response_time) =>
    request('POST', '/score/submit', { child_id, answers, response_time });
export const getHistory = (child_id) =>
    request('GET', `/score/history/${child_id}`);

// TTS 관련
export const generateTTS = (text, speed = 1.0) =>
    request('POST',
        '/tts/generate',
        { text, speed });

// 임시저장
export const saveDraft = (child_id, answers) =>
    request('POST', '/score/draft/save', { child_id, answers });

// 불러오기
export const loadDraft = (child_id) =>
    request('GET', `/score/draft/${child_id}`);

// 삭제
export const deleteDraft = (child_id) =>
    request('DELETE', `/score/draft/${child_id}`);

// 관리자 전체 조회
export const getAllResponses = () =>
    request('GET', '/score/admin/all');

// 응답 일괄 삭제
export const deleteResponses = (response_ids) =>
    request('DELETE', '/score/admin/delete', { response_ids });