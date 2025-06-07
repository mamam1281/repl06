// app.js

document.addEventListener('DOMContentLoaded', () => {

    // --- 전역 상태 및 DOM 요소 ---
    const appState = {
        userId: null, totalPoints: 0, surveyStep: 0,
        cardIndex: 0, videoProgress: 0, spendAmount: 0,
    };

    const sections = {
        nickname: document.getElementById('section-nickname'),
        survey: document.getElementById('section-survey'),
        cardnews: document.getElementById('section-cardnews'),
        video: document.getElementById('section-video'),
        paychallenge: document.getElementById('section-paychallenge'),
    };

    const nicknameInput = document.getElementById('nickname-input');
    const btnStart = document.getElementById('btn-start');
    const surveyContainer = document.getElementById('survey-container');
    const cardSlider = document.getElementById('card-slider');
    const promoVideo = document.getElementById('promo-video');
    const payButton = document.getElementById('btn-pay');
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');


    // --- API 헬퍼 ---
    async function apiPost(path, data) {
        const res = await fetch(path, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (!res.ok) {
            const errorData = await res.json();
            throw new Error(errorData.detail || 'API 요청 실패');
        }
        return res.json();
    }

    // --- UI 전환 함수 ---
    function showSection(sectionName) {
        Object.values(sections).forEach(section => {
            if (section) section.classList.add('hidden');
        });
        if (sections[sectionName]) {
            sections[sectionName].classList.remove('hidden');
        }
    }

    function showToast(message) {
        alert(message);
    }

    // --- 기능별 로직 ---

    // 1. 닉네임 (이전과 동일)
    btnStart.addEventListener('click', async () => {
        const nickname = nicknameInput.value.trim();
        if (!nickname) { return showToast('코드를 입력해 주세요.'); }
        try {
            const res = await apiPost('/api/identify', { nickname });
            appState.userId = res.userId;
            appState.totalPoints = res.points;
            showToast(`환영합니다, ${res.userId}님! 🎉\n+${res.points}포인트가 입금됐어요.`);
            showSection('survey');
            loadSurveyQuestion();
        } catch (error) { showToast(error.message); }
    });

    // 2. 설문 (이전과 동일)
    const surveyQuestions = [
        { id: 1, text: '모델 사용시 가장 큰 불편함은 무엇이었나요?' },
        { id: 2, text: '가장 원하는 보상은 무엇인가요?' },
        { id: 3, text: '기타 의견을 자유롭게 적어주세요.' }
    ];

    function loadSurveyQuestion() {
        if (appState.surveyStep >= surveyQuestions.length) {
            showToast("설문 완료! 다음 단계로 이동합니다.");
            showSection('cardnews');
            return;
        }
        const currentQuestion = surveyQuestions[appState.surveyStep];
        surveyContainer.innerHTML = `
            <p class="survey-question">${currentQuestion.text}</p>
            <input id="survey-answer" class="input-form" type="text" placeholder="답변을 입력하세요">
            <button id="btn-submit-survey" class="button-primary">제출하고 포인트 받기</button>
        `;
        document.getElementById('btn-submit-survey').addEventListener('click', handleSurveySubmit);
    }

    async function handleSurveySubmit() {
        const answer = document.getElementById('survey-answer').value.trim();
        if (!answer) { return showToast("답변을 입력해주세요."); }
        try {
            const res = await apiPost('/api/survey', {
                userId: appState.userId,
                questionId: surveyQuestions[appState.surveyStep].id,
                response: answer
            });
            appState.totalPoints = res.total_points;
            appState.surveyStep++;
            showToast(`+${res.points_awarded} 포인트! (총 ${res.total_points}점)`);
            loadSurveyQuestion();
        } catch (error) { showToast(error.message); }
    }

    // 3. 카드뉴스 ([수정됨] 로직 개선)
    let cardScrollTimer;
    cardSlider.addEventListener('scroll', () => {
        clearTimeout(cardScrollTimer);
        cardScrollTimer = setTimeout(handleCardView, 300);
    });

    async function handleCardView() {
        // 총 카드 수와 카드 너비+간격
        const totalCards = 4;
        const cardWidth = 272;

        // 현재 스크롤 위치를 통해 인덱스 계산
        const currentIndex = Math.round(cardSlider.scrollLeft / cardWidth) + 1;

        // [디버깅용] 현재 계산된 인덱스를 콘솔에 출력
        console.log(`Current Index: ${currentIndex}, Last Rewarded Index: ${appState.cardIndex}`);

        // 새로운 카드를 봤는지 확인
        if (currentIndex > appState.cardIndex && currentIndex <= totalCards) {
            try {
                const res = await apiPost('/api/cardview', { userId: appState.userId, cardIndex: currentIndex });

                appState.cardIndex = currentIndex;
                if (res.points_awarded > 0) {
                    appState.totalPoints = res.total_points;
                    showToast(`+${res.points_awarded} 포인트!`);
                }

            } catch (error) { showToast(error.message); }
        }

        // [수정된 부분] 마지막 카드에 도달했는지 확인하는 로직 개선
        // 스크롤이 거의 끝까지 갔는지 확인 (전체 스크롤 가능 너비 - 현재 스크롤 위치 < 카드 하나의 너비)
        const scrollEndReached = (cardSlider.scrollWidth - cardSlider.scrollLeft - cardSlider.clientWidth) < cardWidth;
        if (appState.cardIndex < totalCards && scrollEndReached) {
            // 아직 마지막 카드 보상을 받지 않았고, 스크롤이 끝에 도달했다면
            // 강제로 마지막 카드 보상 로직을 실행
            try {
                const res = await apiPost('/api/cardview', { userId: appState.userId, cardIndex: totalCards });
                appState.cardIndex = totalCards;
                 if (res.points_awarded > 0) {
                    appState.totalPoints = res.total_points;
                    showToast(`+${res.points_awarded} 포인트! (마지막 카드)`);
                }
            } catch(error) { showToast(error.message); }
        }


        // 마지막 카드를 봤다면 다음 단계로 전환
        if (appState.cardIndex === totalCards) {
            setTimeout(() => { showSection('video'); }, 500);
        }
    }

    // 4. 영상 (이전과 동일)
    let videoThrottleTimer;
    promoVideo.addEventListener('timeupdate', () => {
        if (videoThrottleTimer) { return; }
        videoThrottleTimer = setTimeout(() => {
            handleVideoProgress();
            videoThrottleTimer = null;
        }, 1000);
    });

    async function handleVideoProgress() {
        const percent = (promoVideo.currentTime / promoVideo.duration) * 100;
        if (percent >= 50 && appState.videoProgress < 50) {
            appState.videoProgress = 50;
            const res = await apiPost('/api/video', { userId: appState.userId, progress: 50 });
            if (res.points_awarded > 0) showToast(`중간 보상! +${res.points_awarded} 포인트`);
        }
    }

    promoVideo.addEventListener('ended', async () => {
        if (appState.videoProgress < 100) {
            appState.videoProgress = 100;
            const res = await apiPost('/api/video', { userId: appState.userId, progress: 100 });
            if (res.points_awarded > 0) showToast(`완료 보상! +${res.points_awarded} 포인트`);
            showSection('paychallenge');
            refreshSpendUI();
        }
    });

    // 5. 결제 챌린지 (이전과 동일)
    payButton.addEventListener('click', () => handlePayment(50000));

    async function handlePayment(amount) {
        try {
            const res = await apiPost('/api/spend', { userId: appState.userId, amount });
            appState.spendAmount = res.total_spend;
            appState.totalPoints += res.points_awarded;
            showToast(`${amount.toLocaleString()}원 결제 성공! +${res.points_awarded} 포인트!`);
            refreshSpendUI();
        } catch(error) { showToast(error.message); }
    }

    function refreshSpendUI() {
        const maxAmount = 400000;
        const percent = Math.min((appState.spendAmount / maxAmount) * 100, 100);
        progressBar.style.width = percent + '%';
        progressText.textContent = `Current Spend: ${appState.spendAmount.toLocaleString()} | Total Points: ${appState.totalPoints.toLocaleString()}`;
    }
});