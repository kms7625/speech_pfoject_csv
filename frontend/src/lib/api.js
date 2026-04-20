// 백엔드 주소 - 모든 요청 여기로감
const BASE = 'http://localhost:8000/api';

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

// 아동 관련
export const getChildren = () => request('GET', '/children');
export const createChild = (name, age, gender) =>
    request('POST', '/children', { name, age, gender });
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