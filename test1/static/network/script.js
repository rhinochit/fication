// Expanded JSON Dataset of Connections
const connectionsData = [
    {
        name: "MATEO VANCE",
        title: "Founder & Principal Architect",
        category: "formal",
        tagLabel: "✌️ FORMAL",
        time: "14:02 PM",
        image: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=150&q=80",
        location: "Awwwards Conference, Zurich"
    },
    {
        name: "ZURI AMANI",
        title: "Sound Designer & DJ",
        category: "social",
        tagLabel: "✋ SOCIAL",
        time: "11:45 AM",
        image: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=150&q=80",
        location: "Berghain Kantine, Berlin"
    },
    {
        name: "DR. KENJI SATO",
        title: "Head of Quantum Robotics",
        category: "formal",
        tagLabel: "✌️ FORMAL",
        time: "Yesterday",
        image: "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=150&q=80",
        location: "MIT Robotics Symposium, Boston"
    },
    {
        name: "ELENA ROSTOVA",
        title: "Printmaker & Risograph Curator",
        category: "social",
        tagLabel: "✋ SOCIAL",
        time: "2 days ago",
        image: "https://images.unsplash.com/photo-1580489944761-15a19d654956?auto=format&fit=crop&w=150&q=80",
        location: "Type & Print Expo, Amsterdam"
    },
    {
        name: "MARCUS CHEN",
        title: "Senior AI Researcher",
        category: "formal",
        tagLabel: "✌️ FORMAL",
        time: "3 days ago",
        image: "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=150&q=80",
        location: "NeurIPS Summit, New Orleans"
    },
    {
        name: "CHLOE SAINT LAURENT",
        title: "Fashion Tech Innovator",
        category: "social",
        tagLabel: "✋ SOCIAL",
        time: "4 days ago",
        image: "https://images.unsplash.com/photo-1544005313-94ddf0286df2?auto=format&fit=crop&w=150&q=80",
        location: "Paris Design Week, Paris"
    },
    {
        name: "LIAM O'CONNOR",
        title: "Venture Capital Partner",
        category: "formal",
        tagLabel: "✌️ FORMAL",
        time: "5 days ago",
        image: "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?auto=format&fit=crop&w=150&q=80",
        location: "TechCrunch Disrupt, San Francisco"
    },
    {
        name: "AMARA DUBIS",
        title: "Visual Artist & Creative Director",
        category: "social",
        tagLabel: "✋ SOCIAL",
        time: "Last week",
        image: "https://images.unsplash.com/photo-1531746020798-e6953c6e8e04?auto=format&fit=crop&w=150&q=80",
        location: "Art Basel, Miami"
    }
];

// Maps a real connections_log.json entry (formal/social card shape, from
// main.py's /api/connections-log) onto the fields this page's cards render.
function mapLogEntry(entry) {
    return {
        name: entry.name || 'UNKNOWN',
        title: entry.type === 'formal' ? (entry.title || entry.company || 'Formal contact') : 'Social contact',
        category: entry.type === 'formal' ? 'formal' : 'social',
        tagLabel: entry.type === 'formal' ? '✌️ FORMAL' : '✋ SOCIAL',
        time: entry.time || 'JUST NOW',
        image: entry.avatar || 'https://images.unsplash.com/photo-1607746882042-944635dfe10e?auto=format&fit=crop&w=150&q=80',
        location: entry.type === 'formal' ? (entry.email || 'Fication scan') : (entry.location || 'Fication scan')
    };
}

document.addEventListener('DOMContentLoaded', () => {
    const directoryList = document.getElementById('directoryList');
    const countAll = document.getElementById('countAll');
    const countFormal = document.getElementById('countFormal');
    const countSocial = document.getElementById('countSocial');

    // Function to render cards using a for loop
    function renderCards(dataToRender) {
        directoryList.innerHTML = ''; // Clear container

        for (let i = 0; i < dataToRender.length; i++) {
            const item = dataToRender[i];
            const tagClass = item.category === 'formal' ? 'formal-tag' : 'social-tag';

            const cardHTML = `
                <div class="connection-card" data-category="${item.category}">
                    <div class="card-header-tag ${tagClass}">
                        <span>${item.tagLabel}</span>
                        <span class="card-time">${item.time}</span>
                    </div>
                    <div class="card-body">
                        <img src="${item.image}" alt="${item.name}" class="profile-thumb">
                        <div class="profile-info">
                            <h3>${item.name}</h3>
                            <p class="profile-title">${item.title}</p>
                            <p class="profile-location"><i class="fa-solid fa-location-dot"></i> Last met: ${item.location}</p>
                        </div>
                    </div>
                </div>
            `;
            directoryList.innerHTML += cardHTML;
        }
    }

    // Real scans (from connections_log.json, via /api/connections-log) go on
    // top of the hardcoded demo list below rather than replacing it, so the
    // page still looks populated before anyone's actually been scanned.
    let allConnections = connectionsData;

    function refreshCountsAndRender() {
        countAll.textContent = allConnections.length;
        countFormal.textContent = allConnections.filter(item => item.category === 'formal').length;
        countSocial.textContent = allConnections.filter(item => item.category === 'social').length;

        const activeFilter = document.querySelector('.tab-btn.active')?.getAttribute('data-filter') || 'all';
        renderCards(activeFilter === 'all' ? allConnections : allConnections.filter(item => item.category === activeFilter));
    }

    // Initial render of all cards (demo data only, until the fetch below resolves)
    refreshCountsAndRender();

    fetch('/api/connections-log')
        .then(response => response.json())
        .then(logEntries => {
            if (Array.isArray(logEntries) && logEntries.length > 0) {
                allConnections = logEntries.map(mapLogEntry).concat(connectionsData);
                refreshCountsAndRender();
            }
        })
        .catch(err => console.error('Error fetching connections log:', err));

    // Filter Tab Interactivity
    const tabButtons = document.querySelectorAll('.tab-btn');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            tabButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            refreshCountsAndRender();
        });
    });

    // Search Bar Interactivity
    const searchInput = document.getElementById('searchInput');

    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase();

        const searchedData = allConnections.filter(item => {
            return item.name.toLowerCase().includes(query) ||
                   item.title.toLowerCase().includes(query) ||
                   item.location.toLowerCase().includes(query);
        });

        renderCards(searchedData);
    });

    // Bottom Navigation Interactivity
    const navItems = document.querySelectorAll('.bottom-nav .nav-item');
    
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');
        });
    });
});