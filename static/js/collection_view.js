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

    // LIMPIEZA ATÓMICA: Borramos el contenido viejo ANTES de la petición
    // Esto evita el efecto de "fantasmas" de la página anterior
    gridContainer.innerHTML = ''; 

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
    if (!grid) return 16; // Objetivo base: 16

    const computedStyle = window.getComputedStyle(grid);
    const gridTemplateColumns = computedStyle.getPropertyValue('grid-template-columns');
    const columns = gridTemplateColumns.trim().split(/\s+/).length;

    if (columns <= 0) return 16;

    // Calculamos las filas necesarias para acercarnos lo más posible a 16
    let rows = Math.round(16 / columns);

    // Ajustes de UX:
    // 1. En móviles (1 o 2 cols), forzamos más filas para que el scroll valga la pena
    if (columns <= 2) rows = Math.max(8, rows);
    // 2. En escritorio, al menos 3 filas para que se vea lleno
    else if (columns >= 3 && columns <= 5) rows = Math.max(4, rows);
    // 3. En pantallas gigantes, al menos 2 filas
    else rows = Math.max(2, rows);

    return columns * rows;
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
        const perPage = urlParams.get('per_page') || 16;
        // Al navegar por historial, usamos replaceHistory=true para no crear bucles
        loadCollectionPage(page, perPage, true, true);
    });
});
