let currentColumns = -1;
let resizeTimeout;


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

    gridContainer.innerHTML = ''; 

    try {
        const response = await fetch(`/collections/${status}?page=${page}&per_page=${perPage}&ajax=1`);
        const html = await response.text();

        gridContainer.innerHTML = html;

        window.scrollTo({ top: 0, behavior: 'smooth' });

        let newUrl = `/collections/${status}`;
        if (parseInt(page) > 1) {
            newUrl += `?page=${page}`;
        }

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


function calculateIdealPerPage() {
    const grid = document.querySelector('.collection-grid-premium');
    if (!grid) return 16; 

    const computedStyle = window.getComputedStyle(grid);
    const gridTemplateColumns = computedStyle.getPropertyValue('grid-template-columns');
    const columns = gridTemplateColumns.trim().split(/\s+/).length;

    if (columns <= 0) return 16;

    let rows = Math.round(16 / columns);
    if (columns <= 2) rows = Math.max(8, rows);
    else if (columns >= 3 && columns <= 5) rows = Math.max(4, rows);
    else rows = Math.max(2, rows);

    return columns * rows;
}


function monitorGridResize() {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(() => {
        const grid = document.querySelector('.collection-grid-premium');
        if (!grid) return;

        const computedStyle = window.getComputedStyle(grid);
        const gridTemplateColumns = computedStyle.getPropertyValue('grid-template-columns');
        const newColumns = gridTemplateColumns.trim().split(/\s+/).length;

        if (newColumns !== currentColumns && currentColumns !== -1) {
            const urlParams = new URLSearchParams(window.location.search);
            const currentPage = urlParams.get('page') || 1;
            loadCollectionPage(currentPage, null, false, true);
        }
        currentColumns = newColumns;
    }, 500);
}

window.addEventListener('load', () => {
    window.addEventListener('resize', monitorGridResize);

    document.addEventListener('click', (e) => {
        const link = e.target.closest('.ajax-page-link');
        if (link) {
            e.preventDefault();
            const page = link.getAttribute('data-page');
            loadCollectionPage(page, null, true, false);
        }
    });

    const grid = document.querySelector('.collection-grid-premium');
    if (grid) {
        const computedStyle = window.getComputedStyle(grid);
        const gridTemplateColumns = computedStyle.getPropertyValue('grid-template-columns');
        currentColumns = gridTemplateColumns.trim().split(/\s+/).length;

        const urlParams = new URLSearchParams(window.location.search);
        const ideal = calculateIdealPerPage();
        const currentCards = document.querySelectorAll('.card-link').length;
        
        if (currentCards !== ideal && currentCards > 0) {
             const currentPage = urlParams.get('page') || 1;
             loadCollectionPage(currentPage, ideal, false, true);
        }
    }

    window.addEventListener('popstate', () => {
        const urlParams = new URLSearchParams(window.location.search);
        const page = urlParams.get('page') || 1;
        loadCollectionPage(page, null, true, true);
    });
});
