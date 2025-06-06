// 전역 상태 객체
const appState = {
    userId: null,
    totalPoints: 0,
    stageState: 0,
};

// --- DOM 요소 참조 ---
const sectionNickname = document.getElementById('section-nickname');
const sectionSurvey = document.getElementById('section-survey');
const nicknameInput = document.getElementById('nickname-input');
const btnStart = document.getElementById('btn-start');

// --- 유틸리티 함수 ---

// API POST 요청 헬퍼
async function apiPost(path, data) {
    const res = await fetch(path, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    // 응답이 성공이 아닐 경우, 에러 메시지를 포함하여 예외 발생
    if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || 'API 요청에 실패했습니다.');
    }
    return res.json();
}

// --- 이벤트 리스너 ---

// '시작하기' 버튼 클릭 이벤트
btnStart.addEventListener('click', async () => {
    const nickname = nicknameInput.value.trim();
    if (!nickname) {
        alert('닉네임을 입력해 주세요.');
        return;
    }

    try {
        const res = await apiPost('/api/identify', { nickname });

        // 1. 상태 업데이트
        appState.userId = res.userId;
        appState.totalPoints = res.points;
        appState.stageState = res.stage_state;

        // 2. UI 피드백
        alert(`환영합니다, ${res.userId}님! 🎉\n+${res.points}포인트가 입금됐어요.`);

        // 3. 다음 단계로 화면 전환
        sectionNickname.classList.add('hidden');
        sectionSurvey.classList.remove('hidden');

    } catch (error) {
        // 백엔드에서 받은 에러 메시지를 사용자에게 표시
        alert(error.message);
    }
});