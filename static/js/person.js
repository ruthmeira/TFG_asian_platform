document.addEventListener('DOMContentLoaded', function () {
    const worksGrid = document.getElementById('works-grid');
    const personId = worksGrid?.dataset.personId;
    const showMoreContainer = document.getElementById('show-more-container');
    const showMoreBtn = document.getElementById('show-more-btn');

    // 1. CARGA DE PROYECTOS (Async)
    if (personId) {
        const loader = document.getElementById('projects-loader');
        const hint = worksGrid.dataset.countryHint || '';
        fetch(`/api/person/${personId}/projects?h=${hint}`)
            .then(response => response.text())
            .then(html => {
                // Quitar cargador de golpe
                if (loader) loader.remove();

                worksGrid.innerHTML = html;
                const items = worksGrid.querySelectorAll('.card-link');

                // Mantenemos tu lógica de 8 iniciales
                items.forEach((item, index) => {
                    if (index >= 8) {
                        item.classList.add('hidden-work');
                        item.style.display = 'none';
                    }
                });

                if (items.length > 8) {
                    showMoreContainer.style.display = 'flex';
                    showMoreBtn.textContent = `Ver filmografía completa (+${items.length - 8})`;
                }
            })
            .catch(err => {
                if (loader) loader.remove();
                console.error("Error cargando proyectos:", err);
            });
    }

    // 2. TU LÓGICA ORIGINAL DE MOSTRAR MÁS
    showMoreBtn?.addEventListener('click', function () {
        const hiddenItems = document.querySelectorAll('.hidden-work');
        hiddenItems.forEach((item, index) => {
            setTimeout(() => {
                item.style.display = 'block';
                item.classList.remove('hidden-work');
            }, index * 50); // Tu Cascada original
        });
        showMoreContainer.style.display = 'none';
    });

    // 3. TU LÓGICA ORIGINAL DE BIOGRAFÍA
    const bioText = document.getElementById('bio-text');
    const toggleBtn = document.getElementById('bio-toggle');

    if (!bioText || !toggleBtn) return;

    if (bioText.scrollHeight > bioText.clientHeight + 20) {
        toggleBtn.style.display = 'flex';
    }

    toggleBtn.addEventListener('click', function () {
        if (bioText.classList.contains('expanded')) {
            bioText.style.maxHeight = '150px';
            bioText.classList.remove('expanded');
            toggleBtn.innerHTML = 'Leer más <i class="fas fa-chevron-down"></i>';
        } else {
            bioText.style.maxHeight = bioText.scrollHeight + 'px';
            bioText.classList.add('expanded');
            toggleBtn.innerHTML = 'Leer menos <i class="fas fa-chevron-up"></i>';
        }
    });
});
