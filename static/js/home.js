/**
 * HOME PAGE MODULE
 * Handles Trending Carousels, Window Switching (day/week), and AJAX loading.
 */

window.HomeApp = (() => {
    let currentWindow = 'day';
    const trendingCache = { 'day': null, 'week': null };

    function init(config) {
        currentWindow = config.activeWindow || 'day';
        const serverData = config.serverData;
        
        // Initialize cache if server data is present
        const hasData = serverData && (serverData.series.length > 0 || serverData.movies.length > 0 || serverData.shows.length > 0);
        if (hasData) {
            trendingCache[currentWindow] = serverData;
        } else {
            console.log("⚠️ No server data. Loading via AJAX...");
            loadAllCarousels(currentWindow);
        }

        // Background pre-fetch of the other window
        const otherWindow = currentWindow === 'day' ? 'week' : 'day';
        if (!trendingCache[otherWindow]) {
            loadAllCarousels(otherWindow, true);
        }

        setupEventListeners();
        setupPopState();
    }

    function setupEventListeners() {
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.onclick = (e) => {
                const url = new URL(btn.href);
                const newWindow = url.searchParams.get('window') || 'day';
                if (newWindow === currentWindow) {
                    e.preventDefault();
                    return;
                }
                e.preventDefault();
                switchWindow(newWindow, btn.href);
            };
        });
    }

    function setupPopState() {
        window.addEventListener('popstate', e => {
            if (e.state && e.state.window) switchWindow(e.state.window, location.href, false);
        });
    }

    function switchWindow(windowType, url, push = true) {
        currentWindow = windowType;
        
        // Update UI buttons
        document.querySelectorAll('.filter-btn').forEach(btn => {
            const btnWindow = new URL(btn.href).searchParams.get('window') || 'day';
            btn.classList.toggle('active', btnWindow === windowType);
        });

        if (push) history.pushState({ window: windowType }, '', url);

        if (trendingCache[windowType]) {
            renderFromCache(trendingCache[windowType]);
        } else {
            showLoaders();
            loadAllCarousels(windowType);
        }
    }

    function loadAllCarousels(windowType, silent = false) {
        if (!trendingCache[windowType]) {
            trendingCache[windowType] = { series: [], movies: [], shows: [] };
        }
        loadType(windowType, 'series', 'tv', 'Serie', silent);
        loadType(windowType, 'movies', 'movie', 'Película', silent);
        loadType(windowType, 'shows', 'tv', 'Programa', silent);
    }

    function loadType(windowType, type, apiType, label, silent) {
        fetch(`/api/trending?window=${windowType}&type=${type}`)
            .then(r => r.json())
            .then(data => {
                const items = data[type] || [];
                if (items.length > 0) {
                    trendingCache[windowType][type] = items;
                    if (windowType === currentWindow && !silent) {
                        renderItems(document.getElementById(`carousel-${type}`), items, apiType, label);
                    }
                } else if (!silent && windowType === currentWindow) {
                    // Retry if empty (TMDB sometimes throttles)
                    setTimeout(() => loadType(windowType, type, apiType, label, silent), 2000);
                }
            })
            .catch(err => console.error(`[HomeApp] Error loading ${type}:`, err));
    }

    function renderFromCache(data) {
        if (data.series?.length > 0) renderItems(document.getElementById('carousel-series'), data.series, 'tv', 'Serie');
        if (data.movies?.length > 0) renderItems(document.getElementById('carousel-movies'), data.movies, 'movie', 'Película');
        if (data.shows?.length > 0) renderItems(document.getElementById('carousel-shows'), data.shows, 'tv', 'Programa');
    }

    function renderItems(container, items, type, label) {
        if (!container || !items || items.length === 0) return;
        
        container.innerHTML = items.map(item => `
            <a href="/media/${type}/${item.id}" class="card-link">
                <div class="card">
                    <div class="badge">${label}</div>
                    <img src="https://image.tmdb.org/t/p/w342${item.poster_path}" alt="${item.name || item.title}">
                    <div class="card-body">
                        <h4>${item.name || item.title}</h4>
                        <h6>${item.original_name || item.original_title}</h6>
                        <div class="card-meta">
                            <div class="ratings-group">
                                <span class="rating">⭐ ${parseFloat(item.vote_average || 0).toFixed(1)}</span>
                                <span class="shiori-rating"><i class="fas fa-heart"></i> ${parseFloat(item.shiori_rating || 0).toFixed(1)}</span>
                            </div>
                            <span class="lang">${item.flag || '🌏'}</span>
                        </div>
                    </div>
                </div>
            </a>
        `).join('');
    }

    function showLoaders() {
        const labels = {
            'carousel-series': 'Cargando Series...',
            'carousel-movies': 'Cargando Películas...',
            'carousel-shows': 'Cargando Programas...'
        };
        ['carousel-series', 'carousel-movies', 'carousel-shows'].forEach(id => {
            const container = document.getElementById(id);
            if (!container) return;
            container.innerHTML = `
                <div class="carousel-loader">
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
                        <div class="shimmer-text">${labels[id]}</div>
                        <div class="loading-dots-glow"><span>.</span><span>.</span><span>.</span></div>
                    </div>
                </div>
            `;
        });
    }

    return { init };
})();

// Auto-initialization if data element is present
document.addEventListener('DOMContentLoaded', () => {
    const dataEl = document.getElementById('home-data');
    if (dataEl && window.HomeApp) {
        try {
            const config = JSON.parse(dataEl.textContent);
            window.HomeApp.init(config);
        } catch (e) {
            console.error("Error initializing HomeApp:", e);
        }
    }
});
