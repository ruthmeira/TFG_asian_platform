/**
 * AUTH JAVASCRIPT
 * Handles specialized components for Auth & Profile pages
 */

window.AuthApp = (function() {
    
    /**
     * Initializes the Custom Region Dropdown using the global SHIORI engine
     */
    function initRegionDropdown(config) {
        // Delegamos la lógica al motor central de main.js
        SHIORI.initRegionSelector({
            containerId: config.containerId,
            countries: config.countries,
            placeholder: config.placeholder || "Selecciona un país...",
            onSelect: config.onSelect
        });
    }

    return {
        initRegionDropdown: initRegionDropdown
    };
})();

// Auto-initialization for specific pages
document.addEventListener('DOMContentLoaded', () => {
    const registerData = document.getElementById('register-data');
    const profileData = document.getElementById('profile-data');
    
    if (registerData && window.AuthApp) {
        try {
            const countries = JSON.parse(registerData.textContent);
            window.AuthApp.initRegionDropdown({ countries, containerId: 'region-dropdown-container' });
        } catch (e) { console.error("Error init AuthApp (Register):", e); }
    }
    
    if (profileData && window.AuthApp) {
        try {
            const countries = JSON.parse(profileData.textContent);
            window.AuthApp.initRegionDropdown({ countries, containerId: 'region-dropdown-container' });
        } catch (e) { console.error("Error init AuthApp (Profile):", e); }
    }
});
