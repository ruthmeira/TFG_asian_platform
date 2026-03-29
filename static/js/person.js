document.getElementById('show-more-btn')?.addEventListener('click', function() {
    const hiddenItems = document.querySelectorAll('.hidden-work');
    const button = this;
    
    hiddenItems.forEach((item, index) => {
        setTimeout(() => {
            item.style.display = 'block';
            item.classList.remove('hidden-work');
        }, index * 50); // Efecto cascada suave
    });
    
    button.parentElement.style.display = 'none'; // Ocultar el contenedor del botón
});

// Lógica "Leer más" Biografía
document.addEventListener('DOMContentLoaded', function() {
    const bioText = document.getElementById('bio-text');
    const toggleBtn = document.getElementById('bio-toggle');
    
    if (!bioText || !toggleBtn) return;
    
    // Si la biografía es más alta que el contenedor inicial, mostramos el botón
    if (bioText.scrollHeight > bioText.clientHeight + 20) {
        toggleBtn.style.display = 'flex';
    }
    
    toggleBtn.addEventListener('click', function() {
        if (bioText.classList.contains('expanded')) {
            // CERRAR: Volvemos a los 150px
            bioText.style.maxHeight = '150px';
            bioText.classList.remove('expanded');
            toggleBtn.innerHTML = 'Leer más <i class="fas fa-chevron-down"></i>';
        } else {
            // ABRIR: Ponemos su altura REAL exacta (scrollHeight)
            bioText.style.maxHeight = bioText.scrollHeight + 'px';
            bioText.classList.add('expanded');
            toggleBtn.innerHTML = 'Leer menos <i class="fas fa-chevron-up"></i>';
        }
    });
});
