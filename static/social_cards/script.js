document.addEventListener('DOMContentLoaded', () => {
    const userId = new URLSearchParams(window.location.search).get('user_id');
    const url = userId ? `/api/social-connections?user_id=${userId}` : '/api/social-connections';

    fetch(url)
        .then(response => response.json())
        .then(data => {
            console.log("Fetched data:", data); // Check F12 Console if it still fails
            const profile = Array.isArray(data) ? data[0] : data;

            if (profile && !profile.error) {
                populateProfile(profile);
            } else if (profile && profile.error) {
                console.error(profile.error);
            }
        })
        .catch(err => console.error("Error fetching social JSON data:", err));

    function populateProfile(data) {
        const avatarEl = document.getElementById('profileAvatar');
        if (avatarEl && data.avatar) avatarEl.src = data.avatar;

        const nameEl = document.getElementById('profileName');
        if (nameEl) nameEl.textContent = data.name || '--';

        const locationEl = document.getElementById('profileLocation');
        if (locationEl) {
            locationEl.innerHTML = `<i class="fa-solid fa-location-dot"></i> ${data.location || '--'}`;
        }

        // Direct mapping to match your main.py structure
        const boxStrength = document.getElementById('boxStrength');
        if (boxStrength) boxStrength.textContent = data.strength || data.prompts?.strength || '--';

        const boxDating = document.getElementById('boxDating');
        if (boxDating) boxDating.textContent = data.dating_me || data.prompts?.dating_me || '--';

        const boxGoal = document.getElementById('boxGoal');
        if (boxGoal) boxGoal.textContent = data.life_goal || data.prompts?.life_goal || '--';

        const boxHeart = document.getElementById('boxHeart');
        if (boxHeart) boxHeart.textContent = data.heart || data.prompts?.heart || '--';
    }
});