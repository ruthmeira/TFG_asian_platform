document.addEventListener('DOMContentLoaded', function() {
    const banModal = document.getElementById('ban-confirm-modal');
    const banBtn = document.getElementById('ban-toggle-btn');
    const confirmBtn = document.getElementById('confirm-ban');
    const cancelBtn = document.getElementById('cancel-ban');
    const banForm = document.getElementById('ban-user-form');
    
    const getIsBanned = () => banForm ? banForm.getAttribute('data-is-banned') === 'true' : false;

    const performBanAction = async () => {
        if (!banForm) return;
        const postUrl = banForm.getAttribute('action');
        const confirmBox = banModal ? banModal.querySelector('.shiori-confirm-box') : null;

        if (confirmBtn) {
            confirmBtn.disabled = true;
            confirmBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Procesando...';
        }

        try {
            const response = await fetch(postUrl, { method: 'POST' });
            const result = await response.json();

            if (result.category === 'success') {
                if (confirmBox) {
                    confirmBox.innerHTML = `
                        <div class="confirm-icon icon-success-shiori">
                            <i class="fas fa-check-circle"></i>
                        </div>
                        <h3>¡Hecho!</h3>
                        <p>${result.message}</p>
                        <div class="confirm-actions">
                            <button class="confirm-btn shiori-cancel" id="finish-ban-process" style="flex: 1;">Entendido</button>
                        </div>
                    `;
                    document.getElementById('finish-ban-process').addEventListener('click', () => location.reload());
                    if (banModal) banModal.classList.add('show');
                } else {
                    location.reload();
                }
            } else {
                alert("Error: " + result.message);
                location.reload();
            }
        } catch (error) {
            console.error("Error:", error);
            location.reload();
        }
    };

    // MODERACIÓN INSTANTÁNEA (AJAX)
    const moderateBtns = document.querySelectorAll('.moderate-action');
    moderateBtns.forEach(btn => {
        btn.addEventListener('click', async function(e) {
            e.preventDefault();
            const url = this.getAttribute('data-url');
            const card = this.closest('.admin-review-card');
            
            // Feedback visual inmediato (deshabilitar botones)
            const parent = this.parentElement;
            const buttons = parent.querySelectorAll('button');
            buttons.forEach(b => b.disabled = true);
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Procesando...';

            try {
                const response = await fetch(url, { method: 'POST' });
                // Como las rutas actuales de admin en app.py devuelven redirect, 
                // pero fetch las sigue, si el status es OK (200), asumimos éxito.
                if (response.ok) {
                    card.style.opacity = '0';
                    card.style.transform = 'translateX(20px)';
                    card.style.transition = 'all 0.4s ease';
                    
                    setTimeout(() => {
                        card.remove();
                        // Si no quedan tarjetas, mostrar estado vacío
                        const remaining = document.querySelectorAll('.admin-review-card');
                        if (remaining.length === 0) {
                            const grid = document.querySelector('.admin-reviews-grid');
                            if (grid) {
                                grid.innerHTML = `
                                    <div class="admin-empty-state">
                                        <i class="fas fa-shield-alt"></i>
                                        <h2>Comunidad en Armonía</h2>
                                        <p>No hay opiniones pendientes de revisión ni denuncias activas en este momento.</p>
                                    </div>
                                `;
                            }
                        }
                    }, 400);
                } else {
                    alert("Error en el servidor al procesar la acción.");
                    location.reload();
                }
            } catch (error) {
                console.error("Error en moderación:", error);
                location.reload();
            }
        });
    });

    if (banBtn && banForm) {
        banBtn.addEventListener('click', function(e) {
            e.preventDefault();
            if (getIsBanned()) {
                performBanAction();
            } else {
                if (banModal) banModal.classList.add('show');
            }
        });

        // Interceptar submit directo por si acaso
        banForm.addEventListener('submit', function(e) {
            e.preventDefault();
            if (getIsBanned()) performBanAction();
        });
    }

    if (cancelBtn && banModal) {
        cancelBtn.addEventListener('click', () => banModal.classList.remove('show'));
    }

    if (confirmBtn) {
        confirmBtn.addEventListener('click', (e) => {
            e.preventDefault();
            performBanAction();
        });
    }

    if (banModal) {
        banModal.addEventListener('click', (e) => {
            if (e.target === banModal) banModal.classList.remove('show');
        });
    }

    // BUSCADOR EN TIEMPO REAL PARA LA CÁRCEL
    const prisonSearch = document.getElementById('prison-search-input');
    if (prisonSearch) {
        prisonSearch.addEventListener('input', function() {
            const query = this.value.toLowerCase().trim();
            const cards = document.querySelectorAll('.banned-user-card');
            let hasResults = false;

            cards.forEach(card => {
                const username = card.querySelector('h3').textContent.toLowerCase();
                const email = card.querySelector('.banned-email').textContent.toLowerCase();

                if (username.includes(query) || email.includes(query)) {
                    card.style.display = 'flex';
                    hasResults = true;
                } else {
                    card.style.display = 'none';
                }
            });

            // Gestionar el estado vacío si el buscador no encuentra nada
            const emptyState = document.querySelector('.prison-empty');
            if (!hasResults) {
                if (!emptyState) {
                    const grid = document.querySelector('.banned-users-grid');
                    const newEmpty = document.createElement('div');
                    newEmpty.className = 'admin-empty-state prison-empty';
                    newEmpty.innerHTML = `
                        <i class="fas fa-search-minus"></i>
                        <h2>Sin rastro del prisionero</h2>
                        <p>No hay ningún usuario baneado que coincida con "${query}".</p>
                    `;
                    grid.appendChild(newEmpty);
                } else {
                    emptyState.style.display = 'block';
                    emptyState.querySelector('h2').textContent = 'Sin rastro del prisionero';
                    emptyState.querySelector('p').textContent = `No hay ningún usuario baneado que coincida con "${query}".`;
                }
            } else {
                if (emptyState) {
                    // Si el emptyState era el original (Cárcel Vacía), solo lo ocultamos si hay query
                    // Si es el de búsqueda, lo ocultamos siempre si hay resultados
                    emptyState.style.display = 'none';
                }
            }
        });
    }
});

// GESTIÓN DE REPORTES DE DATOS (AJAX)
window.resolveReport = async function(reportId) {
    const card = document.getElementById(`report-${reportId}`);
    const btn = card.querySelector('.resolve-d');
    const originalText = btn.innerHTML;

    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

    try {
        const response = await fetch(`/admin/data-report/${reportId}/resolve`, { method: 'POST' });
        const result = await response.json();

        if (result.category === 'success') {
            card.style.opacity = '0';
            card.style.transform = 'scale(0.95)';
            card.style.transition = 'all 0.4s ease';
            
            setTimeout(() => {
                card.remove();
                // Verificar si quedan reportes
                if (document.querySelectorAll('.report-card').length === 0) {
                    location.reload(); // Recargamos para mostrar el empty state
                }
            }, 400);
        } else {
            alert("Error: " + result.message);
            btn.disabled = false;
            btn.innerHTML = originalText;
        }
    } catch (error) {
        console.error("Error al resolver reporte:", error);
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
};

window.dismissReport = async function(reportId) {
    const card = document.getElementById(`report-${reportId}`);
    const btn = card.querySelector('.reject-d');
    const originalText = btn.innerHTML;

    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

    try {
        const response = await fetch(`/admin/data-report/${reportId}/dismiss`, { method: 'POST' });
        const result = await response.json();

        if (result.category === 'success') {
            card.style.opacity = '0';
            card.style.transform = 'scale(0.95)';
            card.style.transition = 'all 0.4s ease';
            
            setTimeout(() => {
                card.remove();
                if (document.querySelectorAll('.report-card').length === 0) {
                    location.reload();
                }
            }, 400);
        } else {
            alert("Error: " + result.message);
            btn.disabled = false;
            btn.innerHTML = originalText;
        }
    } catch (error) {
        console.error("Error al ignorar reporte:", error);
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
};


