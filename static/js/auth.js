window.AuthApp = (function() {
    

    function initRegionDropdown(config) {
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
