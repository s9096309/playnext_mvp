// static/js/recommendations.js

document.addEventListener('DOMContentLoaded', () => {
    fetchAndDisplayRecommendations(false);
    fetchAndDisplayUserInfo();

    const generateButton = document.getElementById('generateRecommendationsButton');
    if (generateButton) {
        generateButton.addEventListener('click', () => {
            fetchAndDisplayRecommendations(true);
        });
    }
});

async function fetchAndDisplayRecommendations(forceNewGeneration = false) {
    const recommendationsContainer = document.getElementById('recommendations-container');
    const recommendationsStatus = document.getElementById('recommendations-status');
    const generateButton = document.getElementById('generateRecommendationsButton');

    recommendationsContainer.innerHTML = '<p class="empty-list">Loading recommendations...</p>';
    recommendationsStatus.textContent = '';
    recommendationsStatus.classList.add('hidden');

    if (generateButton) {
        generateButton.disabled = true;
        generateButton.textContent = 'Generating...';
    }

    const token = getAccessToken();
    if (!token) {
        recommendationsContainer.innerHTML = '';
        recommendationsStatus.textContent = 'Please log in to view recommendations.';
        recommendationsStatus.classList.remove('hidden');
        if (generateButton) {
            generateButton.disabled = false;
            generateButton.textContent = 'Generate New Recommendations';
        }
        return;
    }

    try {
        let fetchUrl = `${API_BASE_URL}/users/me/recommendations/`;
        if (forceNewGeneration) {
            fetchUrl += '?force_generate=true';
        }

        const response = await fetch(fetchUrl, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `HTTP error! Status: ${response.status}`);
        }

        const data = await response.json();
        const structuredRecommendations = data.structured_recommendations;

        if (structuredRecommendations && structuredRecommendations.length > 0) {
            recommendationsContainer.innerHTML = '';

            const successMessage = document.createElement('p');
            successMessage.textContent = 'Recommendations generated successfully.';
            successMessage.classList.add('message', 'success');
            recommendationsContainer.appendChild(successMessage);

            structuredRecommendations.forEach(rec => {
                const gameCard = document.createElement('div');
                gameCard.classList.add('game-card');

                const gameName = document.createElement('h3');
                gameName.textContent = rec.name;
                gameCard.appendChild(gameName);

                const genre = document.createElement('p');
                genre.textContent = `Genre: ${rec.genre}`;
                gameCard.appendChild(genre);

                if (rec.igdb_link && rec.igdb_link !== "N/A") {
                    const igdbLink = document.createElement('a');
                    igdbLink.href = rec.igdb_link;
                    igdbLink.textContent = 'View on IGDB';
                    igdbLink.target = '_blank';
                    gameCard.appendChild(igdbLink);
                }

                const reasoning = document.createElement('p');
                reasoning.textContent = `Reasoning: ${rec.reasoning}`;
                reasoning.style.fontStyle = 'italic';
                reasoning.style.fontSize = '0.9em';
                reasoning.style.color = '#bbb';
                gameCard.appendChild(reasoning);

                recommendationsContainer.appendChild(gameCard);
            });
            recommendationsStatus.classList.add('hidden');
        } else {
            recommendationsContainer.innerHTML = '';
            recommendationsStatus.textContent = 'No recommendations available at the moment. Rate more games to get personalized suggestions!';
            recommendationsStatus.classList.remove('hidden');
            recommendationsStatus.classList.add('empty-list');
        }

    } catch (error) {
        console.error('Error fetching recommendations:', error);
        recommendationsContainer.innerHTML = '';
        recommendationsStatus.textContent = `Failed to load recommendations: ${error.message}`;
        recommendationsStatus.classList.remove('hidden');
        recommendationsStatus.classList.add('error');
    } finally {
        if (generateButton) {
            generateButton.disabled = false;
            generateButton.textContent = 'Generate New Recommendations';
        }
    }
}

async function fetchAndDisplayUserInfo() {
    const token = getAccessToken();
    if (!token) {
        console.log("Not logged in, cannot fetch user info for profile page.");
        document.getElementById('profile-username').textContent = 'N/A';
        document.getElementById('profile-email').textContent = 'N/A';
        document.getElementById('profile-age').textContent = 'N/A';
        document.getElementById('profile-registration-date').textContent = 'N/A';
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/users/me`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            if (response.status === 401 || response.status === 403) {
                console.warn("User info fetch failed: Token invalid or unauthorized. Logging out.");
                logout();
                return;
            }
            const errorData = await response.json();
            throw new Error(errorData.detail || `HTTP error! Status: ${response.status}`);
        }

        const userData = await response.json();

        document.getElementById('profile-username').textContent = userData.username;
        document.getElementById('profile-email').textContent = userData.email;
        document.getElementById('profile-age').textContent = userData.user_age || 'N/A';
        document.getElementById('profile-registration-date').textContent = new Date(userData.registration_date).toLocaleDateString();

    } catch (error) {
        console.error('Error fetching user info:', error);
        document.getElementById('profile-username').textContent = 'Error loading';
        document.getElementById('profile-email').textContent = 'Error loading';
        document.getElementById('profile-age').textContent = 'Error loading';
        document.getElementById('profile-registration-date').textContent = 'Error loading';
    }
}