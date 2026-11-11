document.addEventListener('DOMContentLoaded', () => {
    let currentCategory = '';
    const searchInput = document.getElementById('opp-search');

    async function loadOpportunities() {
        const container = document.getElementById('opportunities-container');
        container.innerHTML = '<div style="color: #94a3b8;">Loading opportunities...</div>';

        const queryParams = new URLSearchParams();
        if (currentCategory) queryParams.append('category', currentCategory);
        if (searchInput.value.trim()) queryParams.append('search', searchInput.value.trim());

        try {
            const res = await fetch(`/api/opportunities/list?${queryParams.toString()}`);
            if (!res.ok) return;

            const items = await res.json();
            if (items.length === 0) {
                container.innerHTML = '<div style="color: #64748b;">No matching opportunities found. Ingest records via `/api/opportunities/ingest` to populate.</div>';
                return;
            }

            container.innerHTML = '';
            items.forEach(item => {
                const card = document.createElement('div');
                card.className = 'opp-card';

                const categoryTagClass = `tag-${item.category}`.toLowerCase();
                const deadlineText = item.deadline ? `Deadline: ${item.deadline}` : 'Rolling Application';

                card.innerHTML = `
                    <div>
                        <span class="opp-tag ${categoryTagClass}">${item.category.replace('_', ' ')}</span>
                        <h3 class="opp-title" style="margin-top:0.5rem;">${item.title}</h3>
                        <div class="opp-org">${item.organisation} • ${item.location}</div>
                        ${item.eligibility ? `<div style="font-size:0.8rem; color:#cbd5e1; margin-top:0.5rem;">${item.eligibility}</div>` : ''}
                    </div>
                    <div class="opp-meta">
                        <span>📅 ${deadlineText}</span>
                        <a href="${item.application_url}" target="_blank" style="color:#38bdf8; text-decoration:none; font-weight:600;">Apply ↗</a>
                    </div>
                `;
                container.appendChild(card);
            });
        } catch (err) {
            console.error('Error fetching opportunities:', err);
        }
    }

    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            currentCategory = e.target.getAttribute('data-category');
            loadOpportunities();
        });
    });

    let debounceTimer;
    searchInput.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(loadOpportunities, 300);
    });

    loadOpportunities();
});