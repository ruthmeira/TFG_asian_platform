/**
 * SEARCH RESULTS LOGIC
 * Fetches unified results and renders them using the platform's standard card system.
 */
document.addEventListener('DOMContentLoaded', async () => {
    const resultsGrid = document.getElementById('search-results-grid');
    const urlParams = new URLSearchParams(window.location.search);
    const query = urlParams.get('q');

    if (!query) {
        if (resultsGrid) resultsGrid.innerHTML = '<div class="search-loader"><p>Escribe algo en el buscador de la Home para empezar...</p></div>';
        return;
    }

    try {
        const res = await fetch(`/api/search/unified?q=${encodeURIComponent(query)}`);
        const data = await res.json();

        // Actualizar contadores
        updateSidebar(data.counts);

        // Guardar datos globales para filtrar
        window.currentSearchResults = data.results;

        renderResults(data.results, 'all');
        setupSidebarFiltering();

    } catch (err) {
        console.error("Search error:", err);
        if (resultsGrid) resultsGrid.innerHTML = '<div class="search-loader"><p>Error de conexión con el servidor asiático.</p></div>';
    }

    function updateSidebar(counts) {
        document.getElementById('count-movie').textContent = counts.movie || 0;
        document.getElementById('count-series').textContent = counts.series || 0;
        document.getElementById('count-program').textContent = counts.program || 0;
        document.getElementById('count-person').textContent = counts.person || 0;
        document.getElementById('count-keyword').textContent = counts.keyword || 0;
    }

    function setupSidebarFiltering() {
        const items = document.querySelectorAll('.sidebar-item');
        items.forEach(item => {
            item.onclick = () => {
                items.forEach(i => i.classList.remove('active'));
                item.classList.add('active');
                renderResults(window.currentSearchResults, item.dataset.target);
            };
        });
    }

    function renderResults(results, filter = 'all') {
        if (!resultsGrid) return;
        resultsGrid.innerHTML = '';

        let totalItems = 0;

        // Determinar qué categorías mostrar
        const catsToShow = filter === 'all' ? ['movie', 'series', 'program', 'person', 'keyword'] : [filter];

        catsToShow.forEach(cat => {
            const items = results[cat] || [];
            items.forEach(item => {
                if (cat === 'movie' || cat === 'series' || cat === 'program') {
                    resultsGrid.appendChild(createMediaCard(item, cat));
                } else if (cat === 'person') {
                    resultsGrid.appendChild(createPersonCard(item));
                } else if (cat === 'keyword') {
                    resultsGrid.appendChild(createKeywordItem(item));
                }
                totalItems++;
            });
        });

        if (totalItems === 0) {
            resultsGrid.innerHTML = '<div class="search-loader"><p>No se han encontrado resultados en esta categoría.</p></div>';
        }
    }

    function createMediaCard(item, cat) {
        const link = document.createElement('a');
        link.href = `/media/${item.type}/${item.id}`;
        link.className = 'card-link animate__animated animate__fadeInUp';

        const label = cat === 'movie' ? 'Película' : (cat === 'program' ? 'Programa' : 'Serie');
        const poster = item.image || '/static/img/no-poster.png';

        link.innerHTML = `
            <div class="card">
                <div class="badge">${label.toUpperCase()}</div>
                <img src="${poster}" alt="${item.title}" loading="lazy">
                <div class="card-body">
                    <h4>${item.title}</h4>
                    <h6>${item.original_title || ''}</h6>
                    <div class="card-meta">
                        <span class="rating">⭐ ${item.rating ? item.rating.toFixed(1) : '0.0'}</span>
                        ${item.flag ? `<span class="lang">${item.flag}</span>` : ''}
                    </div>
                </div>
            </div>
        `;
        return link;
    }

    function createPersonCard(person) {
        const link = document.createElement('a');
        link.href = `/person/${person.id}`;
        link.className = 'person-row-link animate__animated animate__fadeInUp';

        const department = person.department || 'Talento';

        // REPLICAR COMPORTAMIENTO DE CAST (de base.html / cast section)
        let avatarHTML = '';
        if (person.image && !person.image.includes('null')) {
            avatarHTML = `<img src="${person.image}" alt="${person.title}" onerror="this.parentElement.innerHTML='<div class=\\'person-placeholder\\'><i class=\\'fas fa-user\\'></i></div>';">`;
        } else {
            avatarHTML = `<div class="person-placeholder"><i class="fas fa-user"></i></div>`;
        }

        link.innerHTML = `
            <div class="person-row-card">
                <div class="person-avatar-mini">
                    ${avatarHTML}
                </div>
                <div class="person-info-main">
                    <h4>${person.title}</h4>
                    <p>${department}</p>
                </div>
                <i class="fas fa-chevron-right person-arrow"></i>
            </div>
        `;
        return link;
    }

    function createKeywordItem(kw) {
        const link = document.createElement('a');
        link.href = `/explore?keywords=${kw.id}_${kw.title.toLowerCase()}`;
        link.className = 'keyword-row animate__animated animate__fadeIn';
        link.innerHTML = `
            <i class="fas fa-hashtag" style="color: var(--primary); margin-right: 15px"></i>
            <span style="font-weight: 600">${kw.title}</span>
            <span style="margin-left: auto; font-size: 0.75rem; opacity: 0.5">Explorar etiqueta</span>
        `;
        return link;
    }
});
