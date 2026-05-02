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

            if (window.activeFilter === 'person' || window.activeFilter === 'keyword') {
                resultsGrid.classList.add('list-layout');
            } else {
                resultsGrid.classList.remove('list-layout');
            }
            
            // Re-renderizar lo que ya tenemos
            resultsGrid.innerHTML = '';
            renderAllKnown();
            
            // Si el stream sigue vivo y el grid está vacío para esta categoría, poner un mini-loader
            if (window.isStreaming && resultsGrid.innerHTML === '') {
                resultsGrid.innerHTML = getMatrixLoader(`Buscando ${item.innerText.replace(/[0-9]/g, '').trim()}...`);
            }
        };
    });

    if (!query) {
        if (resultsGrid) resultsGrid.innerHTML = '<div class="search-loader"><p>Escribe algo en el buscador de la Home para empezar...</p></div>';
        return;
    }

    // Inicializar grid
    resultsGrid.innerHTML = getMatrixLoader('Explorando catálogo asiático...');

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
            const loader = resultsGrid.querySelector('.search-loader');
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
        const loader = resultsGrid.querySelector('.search-loader');
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
        link.target = '_blank';
        link.className = 'card-link animate__animated animate__fadeInUp';

        const label = cat === 'movie' ? 'Película' : (cat === 'program' ? 'Programa' : 'Serie');
        
        // Optimización Shiori: Calidad w342 para nitidez total
        let poster = item.image || '/static/img/no-poster.png';
        if (poster.includes('/w185/')) {
            poster = poster.replace('/w185/', '/w342/');
        }

        const sRating = (item.shiori_rating || 0).toFixed(1);

        link.innerHTML = `
            <div class="card">
                <div class="badge">${label.toUpperCase()}</div>
                <img src="${poster}" alt="${item.title}" loading="lazy">
                <div class="card-body">
                    <h4>${item.title}</h4>
                    <h6>${item.original_title || ''}</h6>
                    <div class="card-meta">
                        <div class="ratings-group">
                            <span class="rating">⭐ ${item.rating ? item.rating.toFixed(1) : '0.0'}</span>
                            <span class="shiori-rating"><i class="fas fa-heart"></i> ${sRating}</span>
                        </div>
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
        link.target = '_blank';
        link.className = 'person-row-link animate__animated animate__fadeInUp';

        const department = person.department || 'Talento';
        let avatarHTML = '';
        if (person.image && !person.image.includes('null')) {
            avatarHTML = `<img src="${person.image}" alt="${person.title}">`;
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
        
        const img = link.querySelector('.person-avatar-mini img');
        if (img) {
            img.onerror = function() {
                this.parentElement.innerHTML = '<div class="person-placeholder"><i class="fas fa-user"></i></div>';
            };
        }
        
        return link;
    }

    function createKeywordItem(kw) {
        const link = document.createElement('a');
        link.href = `/explore?keywords=${kw.id}_${kw.title.toLowerCase()}`;
        link.target = '_blank';
        link.className = 'keyword-row animate__animated animate__fadeIn';
        link.innerHTML = `
            <i class="fas fa-hashtag keyword-icon"></i>
            <span class="keyword-text">${kw.title}</span>
            <span class="keyword-hint">Explorar etiqueta</span>
        `;
        return link;
    }

    function getMatrixLoader(text) {
        return `
            <div class="search-loader animate__animated animate__fadeIn">
                <div class="matrix-container">
                    <div class="matrix-column" style="animation-duration: 2.1s;">あいうえおかきくけこ</div>
                    <div class="matrix-column" style="animation-duration: 4.5s;">你好龙爱美平和</div>
                    <div class="matrix-column" style="animation-duration: 3.2s;">ㄱㄴㄷㄹㅁㅂㅅㅇ</div>
                    <div class="matrix-column" style="animation-duration: 5.1s;">SHIORIシステム</div>
                    <div class="matrix-column" style="animation-duration: 2.8s;">さしすせそたちつてと</div>
                    <div class="matrix-column" style="animation-duration: 6.4s;">アイウエオカキクケコ</div>
                    <div class="matrix-column" style="animation-duration: 3.8s;">0101SHIORI</div>
                    <div class="matrix-column" style="animation-duration: 4.2s;">旭日東昇</div>
                    <div class="matrix-column" style="animation-duration: 2.5s;">シオリ開発</div>
                    <div class="matrix-column" style="animation-duration: 5.7s;">한국드라마</div>
                    <div class="matrix-column" style="animation-duration: 3.5s;">映画アニメ</div>
                    <div class="matrix-column" style="animation-duration: 4.8s;">こんにちは</div>
                </div>
                <div class="loading-content">
                    <div class="shimmer-text">${text}</div>
                    <div class="loading-dots-glow"><span>.</span><span>.</span><span>.</span></div>
                </div>
            </div>`;
    }
});
