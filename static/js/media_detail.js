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

        // DELEGACIÓN DE EVENTOS PARA EL FORMULARIO (Arregla el bug del JSON)
        document.addEventListener('submit', async (e) => {
            if (e.target.id !== 'data-report-form') return;
            
            e.preventDefault();
            const reportForm = e.target;
            const submitBtn = reportForm.querySelector('.confirm-btn-submit');
            const alertContainer = document.getElementById('data-report-alert-container');
            
            if (submitBtn) submitBtn.disabled = true;
            if (alertContainer) alertContainer.innerHTML = '';

            try {
                const formData = new FormData(reportForm);
                const res = await fetch(reportForm.action, {
                    method: 'POST',
                    body: formData
                });
                const result = await res.json();

                if (result.category === 'success') {
                    // METAMORFOSIS AL ESTILO SHIORI
                    confirmBox.innerHTML = `
                        <div class="confirm-icon icon-success-shiori">
                            <i class="fas fa-check-circle"></i>
                        </div>
                        <h3>¡Hecho!</h3>
                        <p>${result.message}</p>
                        <div class="confirm-actions">
                            <button class="confirm-btn shiori-cancel" id="finish-data-report" style="flex: 1; margin-top: 20px;">Entendido</button>
                        </div>
                    `;

                    document.getElementById('finish-data-report').onclick = close;
                } else {
                    // ALERTA INTERNA SHIORI (ERRORES)
                    if (alertContainer) {
                        const alertDiv = document.createElement('div');
                        alertDiv.className = `alert-error`;
                        alertDiv.style.marginBottom = "20px";
                        alertDiv.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${result.message}`;
                        alertContainer.appendChild(alertDiv);
                    }
                    if (submitBtn) submitBtn.disabled = false;
                }
            } catch (err) {
                console.error("Error en reporte:", err);
                if (alertContainer) {
                    alertContainer.innerHTML = `<div class="alert-error" style="margin-bottom:20px;"><i class="fas fa-exclamation-circle"></i> Error de conexión.</div>`;
                }
                if (submitBtn) submitBtn.disabled = false;
            }
        });

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
