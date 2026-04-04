document.addEventListener('DOMContentLoaded', async () => {
    const resultsGrid = document.getElementById('search-results-grid');
    const urlParams = new URLSearchParams(window.location.search);
    const query = urlParams.get('q');
    const sidebarItems = document.querySelectorAll('.sidebar-item');
    
    // Almacén global para filtrado por sidebar
    window.currentSearchResults = { movie: [], series: [], program: [], person: [], keyword: [] };
    window.activeFilter = 'movie';
    window.isStreaming = true;

    // --- 1. ACTIVAR SIDEBAR AL INSTANTE (Máxima Prioridad) ---
    sidebarItems.forEach(item => {
        item.onclick = (e) => {
            sidebarItems.forEach(i => i.classList.remove('active'));
            item.classList.add('active');
            window.activeFilter = item.dataset.target;
            console.log("Cambiando a filtro:", window.activeFilter);
            
            // Re-renderizar lo que ya tenemos
            resultsGrid.innerHTML = '';
            renderAllKnown();
            
            // Si el stream sigue vivo y el grid está vacío para esta categoría, poner un mini-loader
            if (window.isStreaming && resultsGrid.innerHTML === '') {
                resultsGrid.innerHTML = `<div class="streaming-loader animate__animated animate__fadeIn">
                    <i class="fas fa-satellite-dish fa-spin"></i> Buscando resultados de ${item.innerText.trim()}...
                </div>`;
            }
        };
    });

    if (!query) {
        if (resultsGrid) resultsGrid.innerHTML = '<div class="search-loader"><p>Escribe algo en el buscador de la Home para empezar...</p></div>';
        return;
    }

    // Inicializar grid
    resultsGrid.innerHTML = '<div class="streaming-loader animate__animated animate__fadeIn"><i class="fas fa-satellite-dish fa-spin"></i> Explorando catálogo asiático...</div>';

    // --- 2. INICIAR STREAMING ---
    try {
        const response = await fetch(`/api/search/unified?q=${encodeURIComponent(query)}`);
        if (!response.body) throw new Error("Flujo no soportado");

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) {
                window.isStreaming = false;
                finalizeSearch();
                break;
            }

            buffer += decoder.decode(value, { stream: true });
            let lines = buffer.split('\n');
            buffer = lines.pop(); 

            for (let line of lines) {
                if (!line.trim()) continue;
                try {
                    const data = JSON.parse(line);
                    if (data.done) {
                        window.isStreaming = false;
                        finalizeSearch();
                        continue;
                    }
                    handleIncomingItem(data);
                } catch (e) {}
            }
        }
        
    } catch (err) {
        console.error("Search streaming error:", err);
        if (resultsGrid) resultsGrid.innerHTML = '<div class="search-loader"><p>Error de conexión con el servidor asiático.</p></div>';
    }

    function handleIncomingItem(item) {
        const cat = item.category;
        if (!window.currentSearchResults[cat]) return;
        window.currentSearchResults[cat].push(item);
        updateSidebarCounters();

        // Si lo que llega coincide con lo que el usuario está viendo ahora, pintarlo
        if (window.activeFilter === cat) {
            // Quitar loader específico si existía
            const loader = resultsGrid.querySelector('.streaming-loader');
            if (loader) loader.remove();

            if (cat === 'movie' || cat === 'series' || cat === 'program') {
                resultsGrid.appendChild(createMediaCard(item, cat));
            } else if (cat === 'person') {
                resultsGrid.appendChild(createPersonCard(item));
            } else if (cat === 'keyword') {
                resultsGrid.appendChild(createKeywordItem(item));
            }
        }
    }

    function finalizeSearch() {
        const loader = resultsGrid.querySelector('.streaming-loader');
        if (loader) loader.remove();

        const totalFound = Object.values(window.currentSearchResults).reduce((acc, arr) => acc + arr.length, 0);
        if (totalFound === 0) {
            resultsGrid.innerHTML = '<div class="search-loader"><p>No se han encontrado resultados asiáticos.</p></div>';
        }
    }

    function updateSidebarCounters() {
        if (document.getElementById('count-movie')) document.getElementById('count-movie').textContent = window.currentSearchResults.movie.length;
        if (document.getElementById('count-series')) document.getElementById('count-series').textContent = window.currentSearchResults.series.length;
        if (document.getElementById('count-program')) document.getElementById('count-program').textContent = window.currentSearchResults.program.length;
        if (document.getElementById('count-person')) document.getElementById('count-person').textContent = window.currentSearchResults.person.length;
        if (document.getElementById('count-keyword')) document.getElementById('count-keyword').textContent = window.currentSearchResults.keyword.length;
    }

    function renderAllKnown() {
        const filter = window.activeFilter;
        // Solo renderizar la categoría activa
        const items = window.currentSearchResults[filter] || [];
        items.forEach(item => {
            if (filter === 'movie' || filter === 'series' || filter === 'program') {
                resultsGrid.appendChild(createMediaCard(item, filter));
            } else if (filter === 'person') {
                resultsGrid.appendChild(createPersonCard(item));
            } else if (filter === 'keyword') {
                resultsGrid.appendChild(createKeywordItem(item));
            }
        });
    }

    // --- HELPERS DE RENDERIZACIÓN ---

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
        let avatarHTML = '';
        if (person.image && !person.image.includes('null')) {
            avatarHTML = `<img src="${person.image}" alt="${person.title}" onerror="this.parentElement.innerHTML='<div class=\\'person-placeholder\\'><i class=\\'fas fa-user\\'></i></div>';">`;
        } else {
            avatarHTML = `<div class="person-placeholder"><i class="fas fa-user"></i></div>`;
        }

        link.innerHTML = `
            <div class="person-row-card">
                <div class="person-avatar-mini">${avatarHTML}</div>
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
