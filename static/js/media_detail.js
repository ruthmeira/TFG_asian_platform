/**
 * MEDIA DETAIL PAGE LOGIC
 * Includes Trailer Modal, Favorites, and Collection management.
 */

window.MediaDetail = (() => {
    function init(container = document) {
        initTrailer(container);
        initActions(container);
        initDataReport(container);
    }

    function initDataReport(container) {
        const openBtn = container.querySelector('#open-report-modal-btn');
        const modal = document.getElementById('data-report-modal');
        const closeBtn = document.getElementById('close-data-modal');
        const form = document.getElementById('data-report-form');
        const confirmBox = modal ? modal.querySelector('.shiori-confirm-box') : null;

        if (!openBtn || !modal || !form || !confirmBox) return;

        const originalContent = confirmBox.innerHTML;
        modal.dataset.originalHtml = originalContent;


        openBtn.onclick = () => {
            modal.classList.add('show');
            document.body.style.overflow = 'hidden';
        };

        const close = () => {
            modal.classList.remove('show');
            document.body.style.overflow = '';
            // Restauramos el contenido original después de cerrar
            setTimeout(() => { confirmBox.innerHTML = originalContent; }, 300);
        };

        if (closeBtn) closeBtn.onclick = close;
        modal.onclick = (e) => {
            if (e.target === modal) close();
        };
    }
    
    function initTrailer(container) {
        const trailerBtn = container.querySelector('#trailer-btn');
        const trailerModal = document.getElementById('trailer-modal');
        if (!trailerBtn || !trailerModal) return;

        const iframe = trailerModal.querySelector('#trailer-iframe');
        const closeModal = trailerModal.querySelector('#close-modal');
        const overlay = trailerModal.querySelector('.modal-overlay');

        // The key is usually in a data attribute for modularity
        const key = trailerBtn.dataset.key;

        const open = () => {
            if (!key) return;
            iframe.src = `https://www.youtube.com/embed/${key}?autoplay=1`;
            trailerModal.classList.remove('hidden');
            document.body.style.overflow = 'hidden';
        };

        const close = () => {
            trailerModal.classList.add('hidden');
            iframe.src = '';
            document.body.style.overflow = '';
        };

        trailerBtn.onclick = open;
        if (closeModal) closeModal.onclick = close;
        if (overlay) overlay.onclick = close;

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !trailerModal.classList.contains('hidden')) close();
        });
    }

    function initActions(container) {
        const favBtn = container.querySelector("#favorite-btn");
        const toggleBtn = container.querySelector("#collection-toggle");
        const options = container.querySelector("#collection-options");

        if (favBtn) {
            favBtn.onclick = async function () {
                const res = await fetch("/toggle_favorite", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        media_id: favBtn.dataset.id,
                        media_type: favBtn.dataset.type,
                        media_subtype: favBtn.dataset.mediaSubtype,
                        title: favBtn.dataset.title,
                        original_title: favBtn.dataset.originalTitle,
                        vote_average: favBtn.dataset.vote_average,
                        flag: favBtn.dataset.flag,
                        poster: favBtn.dataset.poster
                    })
                });
                const data = await res.json();
                favBtn.classList.toggle("active", data.favorite);
            };
        }

        if (toggleBtn && options) {
            toggleBtn.onclick = (e) => {
                e.stopPropagation();
                options.classList.toggle("hidden");
            };

            container.querySelectorAll(".collection-option").forEach(btn => {
                btn.onclick = async function () {
                    const status = btn.dataset.status;
                    const res = await fetch("/toggle_status", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            media_id: favBtn.dataset.id,
                            media_type: favBtn.dataset.type,
                            media_subtype: favBtn.dataset.mediaSubtype,
                            status: status,
                            title: favBtn.dataset.title,
                            original_title: favBtn.dataset.originalTitle,
                            vote_average: favBtn.dataset.vote_average,
                            flag: favBtn.dataset.flag,
                            poster: favBtn.dataset.poster
                        })
                    });
                    const data = await res.json();
                    container.querySelectorAll(".collection-option").forEach(b => b.classList.remove("active"));
                    if (data.current_status) {
                        const activeBtn = container.querySelector(`[data-status="${data.current_status}"]`);
                        if (activeBtn) activeBtn.classList.add("active");
                    }
                    options.classList.add("hidden");
                };
            });

            document.addEventListener("click", (e) => {
                if (!options.classList.contains("hidden") && !e.target.closest('.collection-dropdown')) {
                    options.classList.add("hidden");
                }
            });
        }
    }

    return { init };
})();

// Auto-initialization if media-detail-container is present
document.addEventListener('DOMContentLoaded', () => {
    const container = document.querySelector('.media-detail-container');
    if (container && window.MediaDetail) {
        window.MediaDetail.init(container);
    }
});

// Silent Prefetch (Speed Triangle)
window.addEventListener('load', () => {
    setTimeout(() => {
        const path = window.location.pathname;
        if (path.includes('/media/')) {
            fetch(path + '/cast').catch(() => { });
            if (path.includes('/tv/')) {
                fetch(path + '/seasons').catch(() => { });
            }
        }
    }, 1500);
});
