/**
 * CAST & CREW JAVASCRIPT
 * Handles interactions on the Cast & Crew page
 */

function toggleDept(header) {
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

// Global scope for onclick attributes in HTML
window.toggleDept = toggleDept;
