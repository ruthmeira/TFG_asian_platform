document.addEventListener('DOMContentLoaded', function() {
    const mainHeaders = document.querySelectorAll('.cast-toggle-header');
    mainHeaders.forEach(header => {
        header.addEventListener('click', function() {
            if (window.innerWidth <= 600) {
                toggleElement(this);
            }
        });
    });

    const deptHeaders = document.querySelectorAll('.dept-subtitle');
    deptHeaders.forEach(header => {
        header.addEventListener('click', function() {
            toggleElement(this);
        });
    });

    function toggleElement(header) {
        const group = header.parentElement;
        const list = header.nextElementSibling;
        if (!list) return;
        
        if (group.classList.contains('collapsed')) {
            list.style.maxHeight = list.scrollHeight + 100 + "px";
            group.classList.remove('collapsed');
            
            setTimeout(() => {
                if(!group.classList.contains('collapsed')) {
                    list.style.maxHeight = "4000px";
                }
            }, 400);
        } else {
            list.style.maxHeight = list.scrollHeight + "px";
            setTimeout(() => {
                group.classList.add('collapsed');
                list.style.maxHeight = "0";
            }, 10);
        }
    }
});
