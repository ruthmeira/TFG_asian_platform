document.addEventListener("DOMContentLoaded", function () {
    const favBtn = document.getElementById("favorite-btn");
    const toggleBtn = document.getElementById("collection-toggle");
    const options = document.getElementById("collection-options");
    const dropdown = toggleBtn ? toggleBtn.parentElement : null;

    // --- LÓGICA DE DETALLES (FAVORITOS Y ESTADOS) ---
    if (favBtn) {
        const mediaId = favBtn.dataset.id;
        const mediaType = favBtn.dataset.type;
        const mediaTitle = favBtn.dataset.title;
        const mediaOriginalTitle = favBtn.dataset.originalTitle;
        const mediaVoteAverage = favBtn.dataset.voteAverage;
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
});