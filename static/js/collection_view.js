/**
 * AJAX COLLECTION RADAR 🧠🚀
 * Gestiona la carga de tarjetas y paginación sin recargas de página.
 */

let currentColumns = -1;
let resizeTimeout;

/**
 * Función principal para cargar contenido por AJAX
 */
async function loadCollectionPage(page = 1, perPage = null, useAnimation = true) {
    const gridContainer = document.getElementById('ajax-collection-container');
    if (!gridContainer) return;

    if (!perPage) {
        perPage = calculateIdealPerPage();
    }

    // Si queremos efecto, quitamos la clase silenciadora. Si no, la ponemos.
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
        window.history.pushState({ path: newUrl }, '', newUrl);

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

    const idealRows = Math.max(2, Math.round(18 / columns));
    return columns * idealRows;
}

/**
 * Radar de cambio de columnas (SIN RECARGA)
 */
function monitorGridResize() {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(() => {
        const grid = document.querySelector('.collection-grid-premium');
        if (!grid) return;

        const computedStyle = window.getComputedStyle(grid);
        const gridTemplateColumns = computedStyle.getPropertyValue('grid-template-columns');
        const newColumns = gridTemplateColumns.trim().split(/\s+/).length;

        // SOLO ACTIVAR EL RADAR SI EL CAMBIO DE VENTANA HA GENERADO UN NUEVO GRID
        if (newColumns !== currentColumns && currentColumns !== -1) {
            console.log(`Grid cambio detectado: de ${currentColumns} a ${newColumns}. Ajustando...`);
            
            // Detectamos en qué página estamos actualmente para NO volver a la 1
            const urlParams = new URLSearchParams(window.location.search);
            const currentPage = urlParams.get('page') || 1;
            
            loadCollectionPage(currentPage, null, false); // Mantenemos página y SIN EFECTO (false)
        }
        currentColumns = newColumns;
    }, 500); 
}

// Inicialización
window.addEventListener('load', () => {
    // Escuchamos el resize
    window.addEventListener('resize', monitorGridResize);

    // ESCUCHADOR MAESTRO PARA PAGINACIÓN (Evita tener JS en el HTML)
    document.addEventListener('click', (e) => {
        const link = e.target.closest('.ajax-page-link');
        if (link) {
            e.preventDefault();
            const page = link.getAttribute('data-page');
            loadCollectionPage(page);
        }
    });

    // Guardamos las columnas iniciales
    const grid = document.querySelector('.collection-grid-premium');
    if (grid) {
        const computedStyle = window.getComputedStyle(grid);
        const gridTemplateColumns = computedStyle.getPropertyValue('grid-template-columns');
        currentColumns = gridTemplateColumns.trim().split(/\s+/).length;
        
        // Si al entrar el per_page no cuadra, ajustamos por AJAX al momento
        const urlParams = new URLSearchParams(window.location.search);
        const ideal = calculateIdealPerPage();
        if (!urlParams.has('per_page') || parseInt(urlParams.get('per_page')) !== ideal) {
            loadCollectionPage(1, ideal, false); // SIN EFECTO al entrar (false)
        }
    }
});
