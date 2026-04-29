// 백엔드 주소 - 모든 요청 여기로감
const BASE = '/api';

// 공통 요청 함수 - GET/POST 둘 다 여기서 처리
async function request(method, path, body = null) {
    const options = {
        method,
        headers: { 'Content-Type': 'application/json' },
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

// 사용자 관련
export const getSessions = () => request('GET', '/sessions');
export const createSession = (name, age, gender) =>
    request('POST', '/sessions', { name, age, gender });
// 특정 사용자의 가장 최근 검사 결과 조회
export async function getLatestResponse(sessionId) {
    return request('GET', `/score/latest/${sessionId}`);
}
// 삭제 관련
export const deleteSession = (sessionId) =>
    request('DELETE', `/sessions/${sessionId}`);

// 문항 관련
export const getQuestions = () => request('GET', '/questions');

// 점수 관련
export const submitAnswers = (session_id, answers, response_time) =>
    request('POST', '/score/submit', { session_id, answers, response_time });
export const getHistory = (session_id) =>
    request('GET', `/score/history/${session_id}`);

// TTS 관련
export const generateTTS = (text, speed = 1.0) =>
    request('POST',
        '/tts/generate',
        { text, speed });

// 임시저장
export const saveDraft = (session_id, answers) =>
    request('POST', '/score/draft/save', { session_id, answers });

// 불러오기
export const loadDraft = (session_id) =>
    request('GET', `/score/draft/${session_id}`);

// 삭제
export const deleteDraft = (session_id) =>
    request('DELETE', `/score/draft/${session_id}`);

// 관리자 전체 조회
export const getAllResponses = () =>
    request('GET', '/score/admin/all');

// 응답 일괄 삭제
export const deleteResponses = (response_ids) =>
    request('DELETE', '/score/admin/delete', { response_ids });