/**
 * AJAX COLLECTION RADAR 🧠🚀
 * Gestiona la carga de tarjetas y paginación sin recargas de página.
 */

let currentColumns = -1;
let resizeTimeout;

/**
 * Función principal para cargar contenido por AJAX
 */
async function loadCollectionPage(page = 1, perPage = null, useAnimation = true, replaceHistory = false) {
    const gridContainer = document.getElementById('ajax-collection-container');
    if (!gridContainer) return;

    if (!perPage) {
        perPage = calculateIdealPerPage();
    }

    if (useAnimation) {
        gridContainer.classList.remove('ajax-update');
    } else {
        gridContainer.classList.add('ajax-update');
    }

    gridContainer.style.pointerEvents = 'none';
    const status = window.location.pathname.split('/').filter(p => p).pop();

    try {
        const response = await fetch(`/collections/${status}?page=${page}&per_page=${perPage}&ajax=1`);
        const html = await response.text();

        gridContainer.innerHTML = html;

        const newUrl = `/collections/${status}?page=${page}&per_page=${perPage}`;

        // GESTIÓN DE HISTORIAL PROFESIONAL
        if (replaceHistory) {
            window.history.replaceState({ path: newUrl }, '', newUrl);
        } else {
            window.history.pushState({ path: newUrl }, '', newUrl);
        }

    } catch (error) {
        console.error("Error cargando colección por AJAX:", error);
    } finally {
        gridContainer.style.pointerEvents = 'auto';
    }
}

/**
 * Calcula el número ideal de tarjetas basándose en el grid real
 */
function calculateIdealPerPage() {
    const grid = document.querySelector('.collection-grid-premium');
    if (!grid) return 18;

    const computedStyle = window.getComputedStyle(grid);
    const gridTemplateColumns = computedStyle.getPropertyValue('grid-template-columns');
    const columns = gridTemplateColumns.trim().split(/\s+/).length;

    if (columns <= 0) return 18;

    let rows = Math.round(18 / columns);
    // En pantallas muy grandes (ej 10 cols), no permitas una sola fila
    if (rows < 2 && columns >= 9) rows = 2;
    // En móviles, permite scroll más largo
    if (columns <= 3) rows = Math.max(6, rows);

    return columns * Math.max(1, rows);
}

/**
 * Radar de cambio de columnas (Sincronizado con Historial)
 */
function monitorGridResize() {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(() => {
        const grid = document.querySelector('.collection-grid-premium');
        if (!grid) return;

        const computedStyle = window.getComputedStyle(grid);
        const gridTemplateColumns = computedStyle.getPropertyValue('grid-template-columns');
        const newColumns = gridTemplateColumns.trim().split(/\s+/).length;

        if (newColumns !== currentColumns && currentColumns !== -1) {
            console.log(`Grid cambio detectado: de ${currentColumns} a ${newColumns}.`);
            const urlParams = new URLSearchParams(window.location.search);
            const currentPage = urlParams.get('page') || 1;

            // Usamos replaceHistory=true para que el resize no ensucie el botón Atrás
            loadCollectionPage(currentPage, null, false, true);
        }
        currentColumns = newColumns;
    }, 500);
}

// Inicialización
window.addEventListener('load', () => {
    window.addEventListener('resize', monitorGridResize);

    // ESCUCHADOR MAESTRO PARA PAGINACIÓN
    document.addEventListener('click', (e) => {
        const link = e.target.closest('.ajax-page-link');
        if (link) {
            e.preventDefault();
            const page = link.getAttribute('data-page');
            // Navegación Manual: Usamos pushState (replaceHistory=false)
            loadCollectionPage(page, null, true, false);
        }
    });

    // Guardamos las columnas iniciales
    const grid = document.querySelector('.collection-grid-premium');
    if (grid) {
        const computedStyle = window.getComputedStyle(grid);
        const gridTemplateColumns = computedStyle.getPropertyValue('grid-template-columns');
        currentColumns = gridTemplateColumns.trim().split(/\s+/).length;

        const urlParams = new URLSearchParams(window.location.search);
        const ideal = calculateIdealPerPage();
        if (!urlParams.has('per_page') || parseInt(urlParams.get('per_page')) !== ideal) {
            // Ajuste inicial: replaceHistory=true
            loadCollectionPage(1, ideal, false, true);
        }
    }

    // RADAR DE NAVEGACIÓN (popstate): Sincroniza el botón Atrás/Adelante
    window.addEventListener('popstate', () => {
        const urlParams = new URLSearchParams(window.location.search);
        const page = urlParams.get('page') || 1;
        const perPage = urlParams.get('per_page') || 18;
        // Al navegar por historial, usamos replaceHistory=true para no crear bucles
        loadCollectionPage(page, perPage, true, true);
    });
});
