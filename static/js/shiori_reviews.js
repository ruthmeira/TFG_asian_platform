document.addEventListener('DOMContentLoaded', function () {
    // FUNCIÓN MADRE: VINCULAR EVENTOS SHIORI
    const attachShioriEvents = () => {
        // LÓGICA DE VOTO OPTIMISTA SHIORI
        document.querySelectorAll('.engagement-btn').forEach(btn => {
            const newBtn = btn.cloneNode(true);
            btn.parentNode.replaceChild(newBtn, btn);
            
            newBtn.addEventListener('click', async function () {
                const reviewId = this.getAttribute('data-id');
                const voteType = this.getAttribute('data-type');
                const card = document.getElementById(`review-${reviewId}`);
                const likeBtn = card.querySelector('.like-btn');
                const dislikeBtn = card.querySelector('.dislike-btn');

                const wasActive = this.classList.contains('active');
                const otherBtn = voteType === 'like' ? dislikeBtn : likeBtn;
                const wasOtherActive = otherBtn.classList.contains('active');

                if (wasActive) {
                    this.classList.remove('active');
                    this.querySelector('.count').textContent = parseInt(this.querySelector('.count').textContent) - 1;
                } else {
                    if (wasOtherActive) {
                        otherBtn.classList.remove('active');
                        otherBtn.querySelector('.count').textContent = parseInt(otherBtn.querySelector('.count').textContent) - 1;
                    }
                    this.classList.add('active');
                    this.querySelector('.count').textContent = parseInt(this.querySelector('.count').textContent) + 1;
                }

                try {
                    const response = await fetch(`/review/${reviewId}/vote`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ vote_type: voteType })
                    });
                    const result = await response.json();
                    if (likeBtn) likeBtn.querySelector('.count').textContent = result.likes;
                    if (dislikeBtn) dislikeBtn.querySelector('.count').textContent = result.dislikes;
                    if (likeBtn) likeBtn.classList.toggle('active', result.current_vote === 'like');
                    if (dislikeBtn) dislikeBtn.classList.toggle('active', result.current_vote === 'dislike');
                } catch (error) {
                    console.error('Error de red al votar:', error);
                    location.reload();
                }
            });
        });

        // LÓGICA DE BORRADO
        document.querySelectorAll('.btn-delete-shiori-btn').forEach(btn => {
            const newBtn = btn.cloneNode(true);
            btn.parentNode.replaceChild(newBtn, btn);
            newBtn.addEventListener('click', function () {
                reviewIdToDelete = this.getAttribute('data-id');
                deleteConfirmModal.classList.add('show');
            });
        });

        // LÓGICA DE REPORTE (BOTÓN)
        document.querySelectorAll('.btn-report-shiori-btn').forEach(btn => {
            const newBtn = btn.cloneNode(true);
            btn.parentNode.replaceChild(newBtn, btn);
            newBtn.addEventListener('click', function () {
                reviewIdToReport = this.getAttribute('data-id');
                reportConfirmModal.classList.add('show');
            });
        });
    };

    // GESTIÓN DE MODALES SHIORI
    const reviewModal = document.getElementById('review-modal');
    const writeReviewBtn = document.getElementById('write-review-btn');
    const closeReviewBtn = document.getElementById('close-review-modal');
    const deleteConfirmModal = document.getElementById('delete-confirm-modal');
    const confirmDeleteBtn = document.getElementById('confirm-delete');
    const cancelDeleteBtn = document.getElementById('cancel-delete');
    const reportConfirmModal = document.getElementById('report-confirm-modal');
    const confirmReportBtn = document.getElementById('confirm-report');
    const cancelReportBtn = document.getElementById('cancel-report');
    
    const reviewForm = document.getElementById('shiori-review-form');
    const alertContainer = document.getElementById('review-alert-container');
    const submitBtn = reviewForm ? reviewForm.querySelector('.btn-submit-full-shiori') : null;
    
    let reviewIdToDelete = null;
    let reviewIdToReport = null;

    // ACTUALIZACIÓN DINÁMICA DEL RATING (0.5)
    const sliderRating = document.getElementById('rating-range-shiori');
    const displayRating = document.getElementById('rating-value-shiori');
    const labelRating = document.getElementById('rating-label-shiori');
    const starMin = document.querySelector('.star-icon-min');
    const starMax = document.querySelector('.star-icon-max');

    const updateSliderUI = () => {
        if (!sliderRating || !displayRating || !labelRating) return;
        const val = parseFloat(sliderRating.value);
        displayRating.textContent = val.toFixed(1);

        // Etiquetas dinámicas según la nota
        if (val <= 0) labelRating.textContent = "Horrible... 🏮🏮";
        else if (val <= 2) labelRating.textContent = "No me ha gustado 🏮";
        else if (val <= 4) labelRating.textContent = "Un poco aburrida 🥱";
        else if (val <= 5.5) labelRating.textContent = "Es pasable 🤔";
        else if (val <= 7) labelRating.textContent = "Me ha gustado 👍";
        else if (val <= 8.5) labelRating.textContent = "¡Muy buena! 🔥";
        else if (val < 10) labelRating.textContent = "¡Increíble! ✨";
        else labelRating.textContent = "¡OBRA MAESTRA! ❤️";

        // Efecto Progress Bar Neón
        const percentage = (val / 10) * 100;
        sliderRating.style.background = `linear-gradient(to right, var(--primary) ${percentage}%, rgba(255, 255, 255, 0.1) ${percentage}%)`;
    };

    if (sliderRating) {
        sliderRating.addEventListener('input', updateSliderUI);
        // Botones de precisión (+/- 0.5)
        if (starMin) {
            starMin.addEventListener('click', () => {
                sliderRating.value = Math.max(0, parseFloat(sliderRating.value) - 0.5);
                updateSliderUI();
            });
        }
        if (starMax) {
            starMax.addEventListener('click', () => {
                sliderRating.value = Math.min(10, parseFloat(sliderRating.value) + 0.5);
                updateSliderUI();
            });
        }
        updateSliderUI(); // Inicialización
    }

    // ABRIR/CERRAR MODAL OPINIÓN
    if (writeReviewBtn && reviewModal) {
        writeReviewBtn.addEventListener('click', () => {
            reviewModal.classList.remove('hidden');
            document.body.style.overflow = 'hidden';
            if (alertContainer) alertContainer.innerHTML = '';
        });
    }

    const closeReviewMod = () => {
        if (reviewModal) {
            reviewModal.classList.add('hidden');
            document.body.style.overflow = '';
        }
    };

    if (closeReviewBtn) closeReviewBtn.addEventListener('click', closeReviewMod);
    if (reviewModal) {
        reviewModal.addEventListener('click', (e) => {
            if (e.target === reviewModal) closeReviewMod();
        });
    }

    // FUNCIÓN DE REFRESCO UNIVERSAL (Para que todo se actualice sin recargar)
    const refreshShioriData = async () => {
        try {
            const refreshRes = await fetch(window.location.href);
            const refreshHTML = await refreshRes.text();
            const parser = new DOMParser();
            const doc = parser.parseFromString(refreshHTML, 'text/html');
            
            // 1. Rejilla de opiniones
            const newGrid = doc.querySelector('.reviews-shiori-grid');
            const currentGrid = document.querySelector('.reviews-shiori-grid');
            if (newGrid && currentGrid) {
                currentGrid.innerHTML = newGrid.innerHTML;
                attachShioriEvents(); // Volvemos a vincular eventos a los nuevos elementos
            }

            // 2. Actualizar Nota Media en la Cabecera
            const newRating = doc.getElementById('shiori-rating-val');
            const currentRating = document.getElementById('shiori-rating-val');
            if (newRating && currentRating) {
                currentRating.textContent = newRating.textContent;
            }

            // 3. Actualizar Contador de Opiniones
            const newCount = doc.querySelector('.shiori-count');
            const currentCount = document.querySelector('.shiori-count');
            if (newCount && currentCount) {
                currentCount.textContent = newCount.textContent;
            }

        } catch (e) { console.error("Error al refrescar datos Shiori:", e); }
    };

    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener('click', async function () {
            if (reviewIdToDelete) {
                const card = document.getElementById(`review-${reviewIdToDelete}`);
                try {
                    const response = await fetch(`/review/${reviewIdToDelete}/delete`, { method: 'POST' });
                    const result = await response.json();

                    if (result.category === 'success') {
                        deleteConfirmModal.classList.remove('show');
                        if (card) {
                            card.style.opacity = '0';
                            card.style.transform = 'scale(0.95)';
                        }
                        setTimeout(async () => {
                            await refreshShioriData();
                            if (writeReviewBtn) writeReviewBtn.innerHTML = '<i class="fas fa-pen"></i> Añadir Opinión';
                            if (reviewForm) {
                                reviewForm.reset();
                                const commentArea = document.getElementById('review-comment');
                                if (commentArea) commentArea.value = '';
                                if (alertContainer) alertContainer.innerHTML = '';
                                const modalSubmitBtn = reviewForm.querySelector('.btn-submit-full-shiori');
                                if (modalSubmitBtn) modalSubmitBtn.textContent = 'Publicar Opinión';
                            }
                        }, 400);
                    }
                } catch (error) {
                    console.error('Error al borrar la opinión:', error);
                }
            }
        });
    }

    // GESTIÓN DE REPORTES
    if (cancelReportBtn) {
        cancelReportBtn.addEventListener('click', () => {
            reportConfirmModal.classList.remove('show');
            reviewIdToReport = null;
        });
    }

    if (confirmReportBtn) {
        confirmReportBtn.addEventListener('click', async function () {
            if (reviewIdToReport) {
                const originalContent = reportConfirmModal.querySelector('.shiori-confirm-box').innerHTML;
                const confirmBox = reportConfirmModal.querySelector('.shiori-confirm-box');
                
                try {
                    const response = await fetch(`/review/${reviewIdToReport}/report`, { method: 'POST' });
                    const result = await response.json();
                    
                    // Icono dinámico según la categoría
                    let iconClass = 'info-circle';
                    let statusClass = 'icon-info-shiori';
                    if (result.category === 'success') {
                        iconClass = 'check-circle';
                        statusClass = 'icon-success-shiori';
                    }
                    
                    // METAMORFOSIS DEL CONTENIDO
                    confirmBox.innerHTML = `
                        <div class="confirm-icon ${statusClass}">
                            <i class="fas fa-${iconClass}"></i>
                        </div>
                        <h3>${result.category === 'success' ? '¡Hecho!' : 'Aviso Shiori'}</h3>
                        <p>${result.message}</p>
                        <div class="confirm-actions">
                            <button class="confirm-btn shiori-cancel" id="finish-report" style="flex: 1;">Entendido</button>
                        </div>
                    `;
                    
                    document.getElementById('finish-report').addEventListener('click', () => {
                        reportConfirmModal.classList.remove('show');
                        setTimeout(() => { confirmBox.innerHTML = originalContent; }, 300);
                        reviewIdToReport = null;
                    });
                    
                } catch (error) {
                    console.error('Error al reportar:', error);
                    reportConfirmModal.classList.remove('show');
                }
            }
        });
    }

    // SUBMIT FORMULARIO (PUBLISH/EDIT)
    if (reviewForm) {
        const commentArea = document.getElementById('review-comment');
        const charCounter = reviewForm.querySelector('.char-counter');
        const updateCounter = () => {
            const len = commentArea.value.length;
            if (charCounter) charCounter.textContent = `${len} / 1000 caracteres`;
        };
        if (commentArea) {
            updateCounter();
            commentArea.addEventListener('input', updateCounter);
        }

        reviewForm.addEventListener('submit', async function (e) {
            e.preventDefault();
            if (submitBtn) submitBtn.disabled = true;
            const formData = new FormData(reviewForm);
            const postUrl = reviewForm.getAttribute('action');

            try {
                const response = await fetch(postUrl, {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();
                if (alertContainer) {
                    alertContainer.innerHTML = '';
                    reviewForm.classList.add('has-alert');
                    const alertDiv = document.createElement('div');
                    alertDiv.className = `alert-${result.category === 'success' ? 'success' : 'error'}`;
                    alertDiv.innerHTML = `<i class="fas fa-${result.category === 'success' ? 'check-circle' : 'exclamation-circle'}"></i> ${result.message}`;
                    alertContainer.appendChild(alertDiv);
                }

                if (result.category === 'success') {
                    if (writeReviewBtn) writeReviewBtn.innerHTML = '<i class="fas fa-pen"></i> Editar Opinión';
                    if (submitBtn) {
                        submitBtn.innerHTML = 'Guardar Opinión';
                        submitBtn.disabled = false;
                    }
                    await refreshShioriData();
                } else {
                    if (submitBtn) {
                        submitBtn.disabled = false;
                        submitBtn.innerHTML = writeReviewBtn.innerText.includes('Editar') ? 'Guardar Opinión' : 'Publicar Opinión';
                    }
                }
            } catch (error) {
                if (alertContainer) {
                    alertContainer.innerHTML = '<div class="alert-error"><i class="fas fa-exclamation-circle"></i> Error de conexión.</div>';
                    reviewForm.classList.add('has-alert');
                }
                if (submitBtn) submitBtn.disabled = false;
            }
        });
    }

    // CIERRE CLICK FUERA
    window.addEventListener('click', (e) => {
        if (e.target === deleteConfirmModal) {
            deleteConfirmModal.classList.remove('show');
            reviewIdToDelete = null;
        }
        if (e.target === reportConfirmModal) {
            reportConfirmModal.classList.remove('show');
            reviewIdToReport = null;
        }
    });

    // LLAMADA INICIAL
    attachShioriEvents();
});
