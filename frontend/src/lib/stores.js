/**
 * stores.js
 * 여러 컴포넌트에서 공통으로 사용하는 유틸리티 함수 모음
 * - 사운드 생성 (playSound)
 * - 한글 자모 분리 (splitJamo)
 * - 레벤슈타인 유사도 계산 (getSimilarity)
 * - STT 텍스트 → 점수 변환 (findBestMatch)
 */

// ── 사운드 생성 ────────────────────────────────────────────────
/**
 * Web Audio API로 비프음 생성
 * @param {number} frequency - 주파수(Hz). 높을수록 높은 음
 * @param {number} duration  - 재생 시간(초)
 * @param {string} type      - 파형 종류 ('sine' | 'square' | 'triangle')
 */
export function playSound(frequency, duration, type = 'sine') {
    const audioCtx = new AudioContext();
    const osc      = audioCtx.createOscillator(); // 소리 생성기
    const gain     = audioCtx.createGain();        // 볼륨 조절기

    osc.connect(gain);
    gain.connect(audioCtx.destination);

    osc.type            = type;
    osc.frequency.value = frequency;

    // 시작 볼륨 0.3 → 점점 줄어서 0에 가까워짐 (자연스러운 페이드아웃)
    gain.gain.setValueAtTime(0.3, audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + duration);

    osc.start(audioCtx.currentTime);
    osc.stop(audioCtx.currentTime + duration);
}

// ── 한글 자모 분리 상수 ────────────────────────────────────────
// 유니코드 한글 음절을 초성/중성/종성으로 분리할 때 사용하는 배열
const CHO  = ["ㄱ","ㄲ","ㄴ","ㄷ","ㄸ","ㄹ","ㅁ","ㅂ","ㅃ","ㅅ","ㅆ","ㅇ","ㅈ","ㅉ","ㅊ","ㅋ","ㅌ","ㅍ","ㅎ"]; // 초성 19개
const JUNG = ["ㅏ","ㅐ","ㅑ","ㅒ","ㅓ","ㅔ","ㅕ","ㅖ","ㅗ","ㅘ","ㅙ","ㅚ","ㅛ","ㅜ","ㅝ","ㅞ","ㅟ","ㅠ","ㅡ","ㅢ","ㅣ"]; // 중성 21개
const JONG = ["","ㄱ","ㄲ","ㄳ","ㄴ","ㄵ","ㄶ","ㄷ","ㄹ","ㄺ","ㄻ","ㄼ","ㄽ","ㄾ","ㄿ","ㅀ","ㅁ","ㅂ","ㅄ","ㅅ","ㅆ","ㅇ","ㅈ","ㅊ","ㅋ","ㅌ","ㅍ","ㅎ"]; // 종성 28개 (첫 번째는 빈 문자)

/**
 * 한글 문자열을 자모 단위로 분리
 * 예: "가끔" → "ㄱㅏㄲㅡㅁ"
 * STT 인식 결과가 조금 틀려도 유사도 비교가 가능하게 해줌
 * @param {string} str - 분리할 문자열
 * @returns {string} 자모가 분리된 문자열
 */
export function splitJamo(str) {
    let result = "";
    for (let i = 0; i < str.length; i++) {
        const code = str.charCodeAt(i) - 44032; // 한글 유니코드 시작값(가=44032) 기준 오프셋
        if (code > -1 && code < 11172) {
            // 한글 음절인 경우 초성/중성/종성 분리
            const cho  = Math.floor(code / 588);                // 초성 인덱스
            const jung = Math.floor((code - (cho * 588)) / 28); // 중성 인덱스
            const jong = code % 28;                             // 종성 인덱스
            result += CHO[cho] + JUNG[jung] + (JONG[jong] !== "" ? JONG[jong] : "");
        } else {
            // 한글이 아닌 경우 그대로 추가
            result += str.charAt(i);
        }
    }
    return result;
}

/**
 * 레벤슈타인 거리 기반 문자열 유사도 계산 (0~1)
 * 두 문자열이 얼마나 비슷한지 계산. 1에 가까울수록 유사
 * 예: "가끔"과 "까끔" → 약 0.8
 * @param {string} s1 - 비교할 문자열 1
 * @param {string} s2 - 비교할 문자열 2
 * @returns {number} 유사도 (0~1)
 */
export function getSimilarity(s1, s2) {
    if (!s1 || !s2) return 0;
    s1 = String(s1); s2 = String(s2);
    const len1 = s1.length, len2 = s2.length;

    // 동적 프로그래밍 행렬 초기화
    const matrix = Array.from({ length: len1 + 1 }, () => Array(len2 + 1).fill(0));
    for (let i = 0; i <= len1; i++) matrix[i][0] = i; // 삭제 비용
    for (let j = 0; j <= len2; j++) matrix[0][j] = j; // 삽입 비용

    // 편집 거리 계산
    for (let i = 1; i <= len1; i++) {
        for (let j = 1; j <= len2; j++) {
            const cost = s1[i-1] === s2[j-1] ? 0 : 1; // 같으면 0, 다르면 1
            matrix[i][j] = Math.min(
                matrix[i-1][j] + 1,       // 삭제
                matrix[i][j-1] + 1,       // 삽입
                matrix[i-1][j-1] + cost   // 대체
            );
        }
    }

    // 편집 거리 → 유사도 변환 (1 - 거리/최대길이)
    return 1 - matrix[len1][len2] / Math.max(len1, len2);
}

/**
 * STT 인식 텍스트를 0~3점 척도로 변환
 * 1단계: 키워드 정확 매칭 시도
 * 2단계: 자모 분리 후 유사도 0.4 이상이면 채택
 * @param {string} text - STT 인식 결과 텍스트
 * @returns {number|null} 0~3 점수, 매칭 실패 시 null
 */
export function findBestMatch(text) {
    const input     = text.replace(/[\s.,!?]/g, ""); // 공백/특수문자 제거
    const jamoInput = splitJamo(input);               // 자모 분리
    let bestMatch   = { value: -1, score: 0 };

    // 각 점수에 해당하는 키워드 목록
    const KEYWORDS = [
        { value: 0, keywords: ["전혀", "아니", "없", "1번", "하나", "일번"] },            // 0점: 전혀 그렇지 않다
        { value: 1, keywords: ["약간", "조금", "가끔", "2번", "둘", "이번"] },            // 1점: 약간 그렇다
        { value: 2, keywords: ["꽤", "종종", "자주", "많", "3번", "셋", "삼번"] },        // 2점: 꽤 그렇다
        { value: 3, keywords: ["매우", "항상", "심", "굉장", "4번", "넷", "사번", "매일"] } // 3점: 매우 그렇다
    ];

    KEYWORDS.forEach(opt => {
        opt.keywords.forEach(keyword => {
            // 1단계: 정확 매칭
            if (input.includes(keyword)) {
                bestMatch = { value: opt.value, score: 1.0 };
                return;
            }
            // 2단계: 자모 유사도 비교 (임계값 0.4 이상만 채택)
            const score = getSimilarity(jamoInput, splitJamo(keyword));
            if (score > bestMatch.score && score > 0.4) {
                bestMatch = { value: opt.value, score };
            }
        });
    });

    return bestMatch.value !== -1 ? bestMatch.value : null;
}