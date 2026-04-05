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
});
