/**
 * CAST & CREW JAVASCRIPT
 * Optimized for clean HTML and mobile-only interactions
 */

document.addEventListener('DOMContentLoaded', function() {
    
    // 1. COLLAPSIBLE MAIN SECTIONS (REPARTO & EQUIPO - MOBILE ONLY < 600px)
    const mainHeaders = document.querySelectorAll('.cast-toggle-header');
    mainHeaders.forEach(header => {
        header.addEventListener('click', function() {
            // ONLY execute on mobile viewports
            if (window.innerWidth <= 600) {
                toggleElement(this);
            }
        });
    });

    // 2. COLLAPSIBLE DEPARTMENTS (CREW)
    const deptHeaders = document.querySelectorAll('.dept-subtitle');
    deptHeaders.forEach(header => {
        header.addEventListener('click', function() {
            toggleElement(this);
        });
    });

    /**
     * Common toggle logic
     * @param {HTMLElement} header The clicked header element
     */
    function toggleElement(header) {
        const group = header.parentElement;
        const list = header.nextElementSibling;
        if (!list) return;
        
        if (group.classList.contains('collapsed')) {
            // OPEN
            list.style.maxHeight = list.scrollHeight + 100 + "px"; // Safety buffer
            group.classList.remove('collapsed');
            
            // Remove fixed max-height after animation for responsiveness
            setTimeout(() => {
                if(!group.classList.contains('collapsed')) {
                    list.style.maxHeight = "4000px";
                }
            }, 400);
        } else {
            // CLOSE
            list.style.maxHeight = list.scrollHeight + "px"; // Fix height before collapse
            setTimeout(() => {
                group.classList.add('collapsed');
                list.style.maxHeight = "0";
            }, 10);
        }
    }
});
