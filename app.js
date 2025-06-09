// app.js

document.addEventListener('DOMContentLoaded', () => {

    const appState = {
        userId: null,
        totalPoints: 0,
        progressionDay: 0,
        surveyStep: 0,
        videoProgress: 0,
        isTestUser: false,
    };

    const missionBoard = document.getElementById('mission-board');
    const templates = document.getElementById('templates');
    const btnStart = document.getElementById('btn-start');
    const btnNextDay = document.getElementById('btn-next-day');

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
    function showToast(message) { alert(message); }

    function updateUserStatus() {
        const userStatus = document.getElementById('user-status');
        const userIdDisplay = document.getElementById('user-id-display');
        const dayDisplay = document.getElementById('progression-day-display');
        const pointsDisplay = document.getElementById('total-points-display');

        if (userIdDisplay) userIdDisplay.textContent = `${appState.userId}`;
        if (dayDisplay) dayDisplay.textContent = `DAY ${appState.progressionDay}`;
        if (pointsDisplay) pointsDisplay.textContent = `💰 ${appState.totalPoints.toLocaleString()} P`;
        if (userStatus) userStatus.classList.remove('hidden');
    }

    // [추가] 챌린지 맵 UI 업데이트 함수
    function updateChallengeMap(currentDay) {
        const challengeMap = document.querySelector('.challenge-map');
        if (!challengeMap) return;

        const dayNodes = challengeMap.querySelectorAll('.day-node');
        dayNodes.forEach(node => {
            const day = parseInt(node.dataset.day, 10);
            const icon = node.querySelector('.day-icon');
            icon.className = 'day-icon'; // 클래스 초기화
            icon.textContent = ''; // 텍스트 초기화

            if (day < currentDay) {
                icon.classList.add('is-complete');
            } else if (day === currentDay) {
                icon.classList.add('is-active');
                icon.textContent = day;
            } else {
                icon.classList.add('is-locked');
            }
        });
        challengeMap.classList.remove('hidden');
    }


    function updateNextDayButtonVisibility() {
        if (appState.isTestUser) {
            btnNextDay.classList.remove('hidden');
        } else {
            btnNextDay.classList.add('hidden');
        }
    }

    function renderCurrentDayMission() {
        updateUserStatus();
        updateChallengeMap(appState.progressionDay); // [추가] 챌린지 맵 업데이트
        missionBoard.innerHTML = '';
        let missionTemplate;

        appState.surveyStep = 0;
        appState.videoProgress = 0;

        switch (appState.progressionDay) {
            case 1:
                missionTemplate = templates.querySelector('#template-mission-complete').cloneNode(true);
                missionTemplate.querySelector('.mission-title').textContent = "챌린지 시작!";
                missionTemplate.querySelector('.mission-description').innerHTML = "환영합니다! 내일부터 본격적인 미션이 시작됩니다.";
                missionBoard.appendChild(missionTemplate);
                break;
            case 2:
                missionTemplate = templates.querySelector('#template-survey').cloneNode(true);
                missionBoard.appendChild(missionTemplate);
                loadSurveyQuestion();
                break;
            case 3: case 4: case 5: case 6:
                missionTemplate = templates.querySelector('#template-cardnews-button').cloneNode(true);
                missionTemplate.querySelector('.mission-title').textContent = `DAY ${appState.progressionDay}: Card News`;
                missionBoard.appendChild(missionTemplate);
                document.getElementById('btn-view-card').addEventListener('click', handleCardViewButtonClick);
                break;
            case 7:
                missionTemplate = templates.querySelector('#template-video').cloneNode(true);
                missionBoard.appendChild(missionTemplate);
                const promoVideo = document.getElementById('promo-video');
                if (promoVideo) {
                    let videoThrottleTimer;
                    promoVideo.addEventListener('timeupdate', () => {
                        if (videoThrottleTimer) return;
                        videoThrottleTimer = setTimeout(() => {
                            handleVideoProgress(promoVideo);
                            videoThrottleTimer = null;
                        }, 1000);
                    });
                    promoVideo.addEventListener('ended', () => handleVideoEnd(promoVideo));
                }
                break;
            case 8: case 9: case 10: case 11: case 12: case 13: case 14:
                missionTemplate = templates.querySelector('#template-paychallenge').cloneNode(true);
                missionTemplate.querySelector('.mission-title').textContent = `DAY ${appState.progressionDay}: Payment Challenge`;
                const challengeDesc = missionTemplate.querySelector('#challenge-description');
                if (challengeDesc) {
                    challengeDesc.textContent = appState.progressionDay >= 11 ? "10만원 이상 결제 기록하기" : "결제 활동 기록하기";
                }
                missionBoard.appendChild(missionTemplate);
                document.getElementById('btn-pay').addEventListener('click', handlePayment);
                break;
            default:
                missionTemplate = templates.querySelector('#template-complete').cloneNode(true);
                missionBoard.appendChild(missionTemplate);
        }

        updateNextDayButtonVisibility();
    }

    function showMissionComplete() {
        missionBoard.innerHTML = '';
        const missionTemplate = templates.querySelector('#template-mission-complete').cloneNode(true);
        missionBoard.appendChild(missionTemplate);
        updateNextDayButtonVisibility();
    }

    btnStart.addEventListener('click', async () => {
        const nicknameInput = document.getElementById('nickname-input');
        const nickname = nicknameInput.value.trim();
        if (!nickname) { return showToast('코드를 입력해 주세요.'); }
        try {
            const res = await apiPost('/api/identify', { nickname });
            appState.userId = res.userId;
            appState.totalPoints = res.points;
            appState.progressionDay = res.progression_day;
            appState.isTestUser = res.is_test_user;

            if (res.is_new) {
                showToast(`환영합니다, ${res.userId}님! 🎉\n+${res.points.toLocaleString()}포인트가 입금됐어요.`);
            } else {
                showToast(`${res.userId}님, 다시 오신 것을 환영해요!`);
            }
            renderCurrentDayMission();
        } catch (error) { showToast(error.message); }
    });

    const surveyQuestions = [
        { id: 1, text: '모델 사용시 가장 큰 불편함은 무엇이었나요?' },
        { id: 2, text: '가장 원하는 보상은 무엇인가요?' },
        { id: 3, text: '기타 의견을 자유롭게 적어주세요.' }
    ];

    function loadSurveyQuestion() {
        if (appState.surveyStep >= surveyQuestions.length) {
            showMissionComplete();
            return;
        }
        const currentQuestion = surveyQuestions[appState.surveyStep];
        const surveyContainer = document.getElementById('survey-container');
        if (surveyContainer) {
            surveyContainer.innerHTML = `
                <p class="survey-question">${currentQuestion.text}</p>
                <div class="input-group">
                    <input id="survey-answer" class="input-form" type="text" placeholder="답변을 입력하세요">
                    <button id="btn-submit-survey" class="button-primary">제출하고 포인트 받기</button>
                </div>
            `;
            document.getElementById('btn-submit-survey').addEventListener('click', handleSurveySubmit);
        }
    }

    async function handleSurveySubmit() {
        const answerInput = document.getElementById('survey-answer');
        if (!answerInput) return;
        const answer = answerInput.value.trim();
        if (!answer) { return showToast("답변을 입력해주세요."); }
        try {
            const res = await apiPost('/api/survey', {
                userId: appState.userId,
                questionId: surveyQuestions[appState.surveyStep].id,
                response: answer
            });
            if (res.points_awarded > 0) {
                appState.totalPoints = res.total_points;
                showToast(`+${res.points_awarded.toLocaleString()} 포인트! (총 ${res.total_points.toLocaleString()}점)`);
            }
            appState.surveyStep++;
            updateUserStatus();
            loadSurveyQuestion();
        } catch (error) { showToast(error.message); }
    }

    async function handleCardViewButtonClick() {
        try {
            const res = await apiPost('/api/cardview', {
                userId: appState.userId,
                day: appState.progressionDay
            });

            if (res.points_awarded > 0) {
                appState.totalPoints = res.total_points;
                // [수정] 사용자에게 명확한 피드백을 먼저 제공
                showToast(`오늘의 카드 보상! +${res.points_awarded.toLocaleString()} 포인트`);
                updateUserStatus();
            } else {
                showToast("이미 오늘의 보상을 받으셨습니다.");
            }

            // [수정] 피드백을 보여준 후, 1.5초 뒤에 완료 화면으로 전환하여 인지할 시간을 줌
            setTimeout(() => {
                showMissionComplete();
            }, 1500);

        } catch(error) { showToast(error.message); }
    }

    async function handleVideoProgress(promoVideo) {
        const percent = (promoVideo.currentTime / promoVideo.duration) * 100;
        if (percent >= 50 && appState.videoProgress < 50) {
            appState.videoProgress = 50;
            try {
                const res = await apiPost('/api/video', { userId: appState.userId, progress: 50 });
                if (res.points_awarded > 0) {
                    appState.totalPoints = res.total_points;
                    showToast(`영상 50% 시청! 중간 보상! +${res.points_awarded.toLocaleString()} 포인트`);
                    updateUserStatus();
                }
            } catch(error) { showToast(error.message); }
        }
    }

    async function handleVideoEnd(promoVideo) {
        if (appState.videoProgress < 100) {
            appState.videoProgress = 100;
            try {
                const res = await apiPost('/api/video', { userId: appState.userId, progress: 100 });
                if (res.points_awarded > 0) {
                    appState.totalPoints = res.total_points;
                    showToast(`영상 시청 완료! +${res.points_awarded.toLocaleString()} 포인트`);
                    updateUserStatus();
                }
                showMissionComplete();
            } catch(error) { showToast(error.message); }
        }
    }

    async function handlePayment() {
        const paymentInput = document.getElementById('payment-input');
        if (!paymentInput) return;
        const amount = parseInt(paymentInput.value, 10);

        if (isNaN(amount) || amount <= 0) {
            return showToast("올바른 금액을 입력하세요.");
        }
        if (appState.progressionDay >= 11 && amount < 100000) {
            return showToast("100,000원 이상 충전해야 챌린지에 참여할 수 있습니다.");
        }
        try {
            const res = await apiPost('/api/spend', { 
                userId: appState.userId,
                day: appState.progressionDay,
                amount: amount
            });

            showToast(res.message);
            if(res.points_awarded > 0) {
                appState.totalPoints = res.total_points;
                showToast(`+${res.points_awarded.toLocaleString()} 포인트 획득!`);
            }
            if(res.special_reward) {
                showToast(`특별 보상 [${res.special_reward}] 획득!`);
            }
            updateUserStatus();
            showMissionComplete();
        } catch(error) { showToast(error.message); }
    }

    btnNextDay.addEventListener('click', async () => {
        try {
            const res = await apiPost('/api/nextday', { userId: appState.userId });
            appState.progressionDay = res.new_day;
            renderCurrentDayMission();
        } catch (error) { showToast(error.message); }
    });
});