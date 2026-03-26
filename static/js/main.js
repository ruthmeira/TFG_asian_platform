document.addEventListener("DOMContentLoaded", function () {
    const favBtn = document.getElementById("favorite-btn");
    const toggleBtn = document.getElementById("collection-toggle");
    const options = document.getElementById("collection-options");
    const dropdown = toggleBtn ? toggleBtn.parentElement : null;

    // --- LÓGICA DE DETALLES (FAVORITOS Y ESTADOS) ---
    if (favBtn) {
        const mediaId = favBtn.dataset.id;
        const mediaType = favBtn.dataset.type;
        const mediaSubtype = favBtn.dataset.mediaSubtype;
        const mediaTitle = favBtn.dataset.title;
        const mediaOriginalTitle = favBtn.dataset.originalTitle;
        const mediaVoteAverage = favBtn.dataset.vote_average;
        const mediaFlag = favBtn.dataset.flag;
        const mediaPoster = favBtn.dataset.poster;

        // ❤️ Favorito
        favBtn.addEventListener("click", async function () {
            const res = await fetch("/toggle_favorite", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ 
                    media_id: mediaId, 
                    media_type: mediaType,
                    media_subtype: mediaSubtype,
                    title: mediaTitle,
                    original_title: mediaOriginalTitle,
                    vote_average: mediaVoteAverage,
                    flag: mediaFlag,
                    poster: mediaPoster 
                })
            });
            const data = await res.json();
            favBtn.classList.toggle("active", data.favorite);
        });

        // 📂 Cambiar Estado
        document.querySelectorAll(".collection-option").forEach(btn => {
            btn.addEventListener("click", async function () {
                const status = btn.dataset.status;
                const res = await fetch("/toggle_status", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ 
                        media_id: mediaId, 
                        media_type: mediaType, 
                        media_subtype: mediaSubtype,
                        status: status,
                        title: mediaTitle,
                        original_title: mediaOriginalTitle,
                        vote_average: mediaVoteAverage,
                        flag: mediaFlag,
                        poster: mediaPoster
                    })
                });
                const data = await res.json();
                document.querySelectorAll(".collection-option").forEach(b => b.classList.remove("active"));
                if (data.current_status) {
                    const activeBtn = document.querySelector(`[data-status="${data.current_status}"]`);
                    if (activeBtn) activeBtn.classList.add("active");
                }
                options.classList.add("hidden");
                if (dropdown) dropdown.classList.remove("upwards");
            });
        });
    }

    // --- LÓGICA DE VISIBILIDAD DINÁMICA (EXPLORE) ---
    const typeSelect = document.getElementById('media-type-select');
    const statusGroup = document.getElementById('status-filter-group');
    if (typeSelect && statusGroup) {
        typeSelect.addEventListener('change', function() {
            if (this.value === 'movie') {
                statusGroup.style.display = 'none';
                statusGroup.querySelector('select').value = ''; // Resetear al cambiar a pelis
            } else {
                statusGroup.style.display = 'block';
            }
        });
    }

    // --- LÓGICA DEL BOTÓN "VER MÁS" (EXPLORE) ---
    // (Ahora se maneja directamente en explore.html a través de la nueva API /api/explore)

    // --- LÓGICA DEL DROPDOWN ---
    if (toggleBtn) {
        toggleBtn.addEventListener("click", function (e) {
            e.stopPropagation();
            options.classList.toggle("hidden");
            const rect = options.getBoundingClientRect();
            if (window.innerHeight - rect.top < rect.height + 20) {
                dropdown.classList.add("upwards");
            } else {
                dropdown.classList.remove("upwards");
            }
        });
    }

    document.addEventListener("click", () => {
        if (options && !options.classList.contains("hidden")) {
            options.classList.add("hidden");
            if (dropdown) dropdown.classList.remove("upwards");
        }
    });
    // --- LÓGICA DE MOSTRAR CONTRASEÑA Y MAYÚSCULAS ---
    let capsLockOn = false;

    // Actualizamos el estado global de CapsLock con cualquier evento compatible
    const updateCapsLockState = (e) => {
        if (e.getModifierState) {
            capsLockOn = e.getModifierState('CapsLock');
        }
        // Disparamos una actualización visual en los campos activos
        document.querySelectorAll('.password-input').forEach(input => {
            if (document.activeElement === input) {
                const group = input.closest('.input-group');
                const warning = group ? group.querySelector('.caps-warning') : null;
                if (warning) {
                    if (capsLockOn) warning.classList.add('visible');
                    else warning.classList.remove('visible');
                }
                if (capsLockOn) input.classList.add('caps-on');
                else input.classList.remove('caps-on');
            }
        });
    };

    window.addEventListener('keydown', updateCapsLockState);
    window.addEventListener('keyup', updateCapsLockState);
    window.addEventListener('mousedown', updateCapsLockState);

    function setupPasswordField(inputId, toggleId) {
        const input = document.getElementById(inputId);
        const toggle = document.getElementById(toggleId);

        if (!input) return;

        if (toggle) {
            toggle.addEventListener('click', function() {
                const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
                input.setAttribute('type', type);
                this.classList.toggle('fa-eye');
                this.classList.toggle('fa-eye-slash');
            });
        }

        input.addEventListener('focus', updateCapsLockState);
        input.addEventListener('blur', () => {
            const group = input.closest('.input-group');
            const warning = group ? group.querySelector('.caps-warning') : null;
            if (warning) warning.classList.remove('visible');
            input.classList.remove('caps-on');
        });
    }

    setupPasswordField('password', 'togglePassword');
    setupPasswordField('confirm_password', 'toggleConfirmPassword');
    setupPasswordField('current_password', 'toggleCurrentPassword');
});