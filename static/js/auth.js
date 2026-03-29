/**
 * AUTH JAVASCRIPT
 * Handles specialized components for Auth & Profile pages
 */

window.AuthApp = (function() {
    
    /**
     * Initializes the Custom Region Dropdown
     * @param {Object} config - Configuration object
     * @param {Array} config.countries - List of country objects {code, name, emoji}
     * @param {String} config.containerId - ID of the container element
     */
    function initRegionDropdown(config) {
        const countries = config.countries || [];
        const container = document.getElementById(config.containerId);
        if (!container) return;

        const btn = container.querySelector('.region-dropdown-btn');
        const display = container.querySelector('.selected-region');
        const menu = container.querySelector('.region-dropdown-menu');
        const listContainer = container.querySelector('.region-list');
        const searchInput = container.querySelector('.region-search-box input');
        const hiddenInput = container.querySelector('input[type="hidden"]');
        const defaultText = config.placeholder || "Selecciona tu país (Opcional)";

        function renderDisplay(code) {
            const country = countries.find(c => c.code === code);
            if (country) {
                display.innerHTML = `<span class="flag">${country.emoji}</span><span class="name">${country.name}</span><span class="code">${country.code}</span>`;
                hiddenInput.value = country.code;
            } else {
                display.innerHTML = defaultText;
                hiddenInput.value = "";
            }
        }

        function renderList(query = "") {
            if (!listContainer) return;
            listContainer.innerHTML = '';
            const q = query.toLowerCase().trim();
            const filtered = countries.filter(c => 
                c.name.toLowerCase().includes(q) || 
                c.code.toLowerCase().includes(q)
            );
            
            if (filtered.length === 0) {
                listContainer.innerHTML = `<li style="padding: 15px; color: rgba(255,255,255,0.4); text-align: center; font-size: 0.9rem;">No se encontraron países</li>`;
                return;
            }
            
            filtered.forEach(country => {
                const li = document.createElement('li');
                li.className = `region-item ${country.code === hiddenInput.value ? 'selected' : ''}`;
                li.innerHTML = `<span class="flag">${country.emoji}</span><span class="name">${country.name}</span><span class="code">${country.code}</span>`;
                
                li.addEventListener('click', (e) => {
                    e.stopPropagation();
                    renderDisplay(country.code);
                    closeDropdown();
                });
                listContainer.appendChild(li);
            });
        }

        function toggleDropdown(e) {
            e.stopPropagation();
            const isOpen = container.classList.toggle('open');
            if (isOpen) {
                if (searchInput) {
                    searchInput.value = "";
                    renderList();
                    setTimeout(() => searchInput.focus(), 100);
                }
            }
        }

        function closeDropdown() {
            container.classList.remove('open');
        }

        if (btn) btn.addEventListener('click', toggleDropdown);
        if (searchInput) searchInput.addEventListener('click', e => e.stopPropagation());
        if (menu) menu.addEventListener('click', e => e.stopPropagation());
        if (searchInput) searchInput.addEventListener('input', (e) => renderList(e.target.value));
        
        document.addEventListener('click', (e) => {
            if (!container.contains(e.target)) closeDropdown();
        });

        // Initialize with hidden input value if exists
        if (hiddenInput && hiddenInput.value) {
            renderDisplay(hiddenInput.value);
        }
        
        renderList();
    }

    return {
        initRegionDropdown: initRegionDropdown
    };
})();
