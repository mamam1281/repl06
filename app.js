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

    const cardNewsContent = {
        3: {
            title: "첫 번째 비밀",
            description: "VIP를 위한 첫 번째 비밀 카드를 뒤집어보세요.",
            front: `<div class="card-icon">🔑</div><div class="card-title-front">첫 번째 비밀</div><div class="card-desc-small">(탭하여 뒷면 확인)</div>`,
            back: `<div class="card-title-back">[꿀팁] 빠른 포인트 적립!</div><div class="card-divider"></div><div class="card-desc">7일차 영상 미션은 50%만 봐도 첫 보상이 지급됩니다.</div>`
        },
        4: {
            title: "포인트 해킹",
            description: "포인트를 2배로 불릴 수 있는 비밀 정보!",
            front: `<div class="card-icon">💰</div><div class="card-title-front">Point Hacking</div><div class="card-desc-small">(탭하여 뒷면 확인)</div>`,
            back: `<div class="card-title-back">[독점 정보] 랜덤 보너스!</div><div class="card-divider"></div><div class="card-desc">8~10일차 입금 챌린지에서 최대 <strong>30,000 포인트</strong> 보너스가 숨어있습니다.</div>`
        },
        5: {
            title: "챌린지 스포일러",
            description: "미리 알면 더 유리한 다음 챌린지 힌트.",
            front: `<div class="card-icon">🤫</div><div class="card-title-front">챌린지 스포일러</div><div class="card-desc-small">(탭하여 뒷면 확인)</div>`,
            back: `<div class="card-title-back">[중요] 10만원 이상!</div><div class="card-divider"></div><div class="card-desc">11일차부터는 <strong>10만원 이상</strong> 입금해야 특별 보상을 받을 수 있습니다.</div>`
        },
        6: {
            title: "최종 보상 공개",
            description: "D-8: 마지막까지 포기하지 마세요!",
            front: `<div class="card-icon">🎁</div><div class="card-title-front">최종 보상은 과연?</div><div class="card-desc-small">(탭하여 뒷면 확인)</div>`,
            back: `<div class="card-title-back">[최종 보상 공개]</div><div class="card-divider"></div><div class="card-desc">14일차 미션 완료 시 <strong>'배민 상품권 3만원권'</strong>이 기다립니다!</div>`
        }
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

    function showToast(message) { 
        alert(message); 
    }

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

    function updateChallengeMap(currentDay) {
        const challengeMap = document.querySelector('.challenge-map');
        if (!challengeMap) return;
        const dayNodes = challengeMap.querySelectorAll('.day-node');
        dayNodes.forEach(node => {
            const day = parseInt(node.dataset.day, 10);
            const icon = node.querySelector('.day-icon');
            icon.className = 'day-icon';
            icon.textContent = '';
            if (day < currentDay) { icon.classList.add('is-complete'); } 
            else if (day === currentDay) { icon.classList.add('is-active'); icon.textContent = day; } 
            else { icon.classList.add('is-locked'); }
        });
        challengeMap.classList.remove('hidden');
    }

    function updateNextDayButtonVisibility() {
        if (appState.isTestUser) { btnNextDay.classList.remove('hidden'); } 
        else { btnNextDay.classList.add('hidden'); }
    }

    function renderCurrentDayMission() {
        updateUserStatus();
        updateChallengeMap(appState.progressionDay);
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
                const dayContent = cardNewsContent[appState.progressionDay];
                missionTemplate.querySelector('.mission-title').textContent = `DAY ${appState.progressionDay}: ${dayContent.title}`;
                missionTemplate.querySelector('.mission-description').textContent = dayContent.description;
                missionTemplate.querySelector('.card-face--front').innerHTML = dayContent.front;
                missionTemplate.querySelector('.card-face--back').innerHTML = dayContent.back;
                missionBoard.appendChild(missionTemplate);
                const cardScene = missionBoard.querySelector('.card-scene');
                const rewardButton = missionBoard.querySelector('#btn-view-card');
                cardScene.addEventListener('click', () => {
                    cardScene.classList.add('is-flipped');
                    rewardButton.classList.remove('hidden');
                }, { once: true });
                rewardButton.addEventListener('click', handleCardViewButtonClick);
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
            case 8: case 9: case 10:
            case 11: case 12: case 13: case 14:
                missionTemplate = templates.querySelector('#template-paychallenge').cloneNode(true);
                missionTemplate.querySelector('.mission-title').textContent = `DAY ${appState.progressionDay}: 입금 챌린지`;
                const challengeDesc = missionTemplate.querySelector('#challenge-description');
                if (challengeDesc) {
                    let descText = "";
                    if (appState.progressionDay <= 10) { descText = "10만원 이상 입금 시, 랜덤 포인트가 지급됩니다."; } 
                    else { descText = "20만원 이상 입금 시, 더 큰 랜덤 포인트가 지급됩니다!"; }
                    challengeDesc.innerHTML = descText;
                }
                missionTemplate.querySelector('#btn-pay').textContent = "입금 활동 기록하기";
                missionTemplate.querySelector('#payment-input').placeholder = "입금 금액 입력";
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
            if (res.is_new) { showToast(`환영합니다, ${res.userId}님! 🎉\n+${res.points.toLocaleString()}포인트가 입금됐어요.`); } 
            else { showToast(`${res.userId}님, 다시 오신 것을 환영해요!`); }
            document.getElementById('section-nickname').classList.add('hidden');
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
                <div class="input-group">
                    <p class="survey-question">${currentQuestion.text}</p>
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
                updateUserStatus();
            }
            appState.surveyStep++;
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
                showToast(`오늘의 카드 보상! +${res.points_awarded.toLocaleString()} 포인트`);
                updateUserStatus();
            } else {
                showToast("이미 오늘의 보상을 받으셨습니다.");
            }
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
        if (isNaN(amount) || amount <= 0) { return showToast("올바른 금액을 입력하세요.");}

        if (appState.progressionDay >= 11 && amount < 200000) {
            return showToast("200,000원 이상 입금해야 챌린지에 참여할 수 있습니다.");
        }
        if (appState.progressionDay >= 8 && appState.progressionDay <= 10 && amount < 100000) {
            return showToast("100,000원 이상 입금해야 챌린지에 참여할 수 있습니다.");
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