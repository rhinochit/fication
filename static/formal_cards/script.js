document.addEventListener('DOMContentLoaded', () => {
    // A user_id in the URL means this card is showing the real person who
    // was just scanned; without one, it falls back to the placeholder demo data.
    const userId = new URLSearchParams(window.location.search).get('user_id');
    const url = userId ? `/api/connections?user_id=${userId}` : '/api/connections';

    fetch(url)
        .then(response => response.json())
        .then(data => {
            const profile = Array.isArray(data) ? data[0] : data;
            if (profile && !profile.error) {
                populateProfile(profile);
            } else if (profile && profile.error) {
                console.error(profile.error);
            }
        })
        .catch(err => console.error("Error fetching JSON data:", err));

    function populateProfile(data) {
        // Top Card Elements
        const avatarEl = document.getElementById('profileAvatar');
        if (avatarEl) avatarEl.src = data.avatar || '';

        const nameEl = document.getElementById('profileName');
        if (nameEl) nameEl.textContent = data.name || '--';

        const titleEl = document.getElementById('profileTitle');
        if (titleEl) titleEl.textContent = data.title || '--';

        const companyEl = document.getElementById('profileCompany');
        if (companyEl) companyEl.textContent = data.company || '--';

        const emailEl = document.getElementById('profileEmail');
        if (emailEl) emailEl.innerHTML = `<i class="fa-regular fa-envelope"></i> ${data.email || '--'}`;

        const phoneEl = document.getElementById('profilePhone');
        if (phoneEl) phoneEl.innerHTML = `<i class="fa-solid fa-phone"></i> ${data.phone || '--'}`;

        const backIdEl = document.getElementById('backId');
        if (backIdEl) backIdEl.textContent = data.id || '0928';

        // Populate Info Boxes from the JSON structure
        if (data.info_boxes) {
            const boxWorking = document.getElementById('boxWorkingOn');
            if (boxWorking) boxWorking.textContent = data.info_boxes.working_on || '';

            const boxStack = document.getElementById('boxStack');
            if (boxStack) boxStack.textContent = data.info_boxes.stack || '';

            const boxProud = document.getElementById('boxProudOf');
            if (boxProud) boxProud.textContent = data.info_boxes.proud_of || '';

            const boxPhil = document.getElementById('boxPhilosophy');
            if (boxPhil) boxPhil.textContent = data.info_boxes.philosophy || '';
        }
    }

    // Flip Card Interactivity (Double-Tap & Flip Button)
    const card = document.getElementById('flipCard');
    const flipBtn = document.getElementById('flipBtn');
    let lastTap = 0;

    function toggleFlip() {
        card.classList.toggle('flipped');
    }

    if (flipBtn) {
        flipBtn.addEventListener('click', toggleFlip);
    }

    if (card) {
        card.addEventListener('click', (e) => {
            const currentTime = new Date().getTime();
            const tapLength = currentTime - lastTap;
            
            if (tapLength < 300 && tapLength > 0) {
                toggleFlip();
                e.preventDefault();
            }
            lastTap = currentTime;
        });
    }
});