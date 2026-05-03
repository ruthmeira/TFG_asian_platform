

document.addEventListener("DOMContentLoaded", function () {
    
    
    let capsLockOn = false;

    const updateCapsLockState = (e) => {
        if (e.getModifierState) {
            capsLockOn = e.getModifierState('CapsLock');
        }
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

    
    const menuToggle = document.getElementById('menu-toggle');
    const navLinks = document.getElementById('nav-links');

    if (menuToggle && navLinks) {
        menuToggle.addEventListener('click', (e) => {
            e.stopPropagation();
            navLinks.classList.toggle('active');
            const icon = menuToggle.querySelector('i');
            if (navLinks.classList.contains('active')) {
                icon.classList.remove('fa-bars');
                icon.classList.add('fa-times');
            } else {
                icon.classList.remove('fa-times');
                icon.classList.add('fa-bars');
            }
        });

        
        document.addEventListener('click', (e) => {
            if (!navLinks.contains(e.target) && !menuToggle.contains(e.target)) {
                navLinks.classList.remove('active');
                const icon = menuToggle.querySelector('i');
                if (icon) {
                    icon.classList.remove('fa-times');
                    icon.classList.add('fa-bars');
                }
            }
        });
    }

    
    const scrollTopBtn = document.getElementById('scroll-to-top');
    const footer = document.querySelector('.footer');

    if (scrollTopBtn) {
        window.addEventListener('scroll', () => {
            
            if (window.scrollY > 400) {
                scrollTopBtn.classList.add('visible');
            } else {
                scrollTopBtn.classList.remove('visible');
            }

            
            if (footer) {
                const footerRect = footer.getBoundingClientRect();
                const windowHeight = window.innerHeight;
                
                
                if (footerRect.top < windowHeight) {
                    const offset = windowHeight - footerRect.top + 30; 
                    scrollTopBtn.style.bottom = offset + 'px';
                } else {
                    scrollTopBtn.style.bottom = '30px'; 
                }
            }
        });

        scrollTopBtn.addEventListener('click', () => {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }

    
    const homeSearchInput = document.getElementById('home-search-input');
    const homeSearchBtn = document.getElementById('home-search-btn');

    if (homeSearchInput && homeSearchBtn) {
        const performSearch = () => {
            const query = homeSearchInput.value.trim();
            if (query) {
                window.location.href = `/search?q=${encodeURIComponent(query)}`;
            }
        };

        homeSearchBtn.addEventListener('click', performSearch);
        homeSearchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') performSearch();
        });
    }

    
    const loaderBar = document.getElementById('global-loader-bar');
    let loaderTimeout;

    function startLoader() {
        if (!loaderBar) return;
        clearTimeout(loaderTimeout);
        loaderBar.classList.remove('complete');
        loaderBar.classList.add('loading');
        loaderBar.style.width = '0%';
        
        
        setTimeout(() => {
            loaderBar.style.width = '30%';
        }, 50);

        setTimeout(() => {
            loaderBar.style.width = '70%';
        }, 400);

        
        let progress = 70;
        const interval = setInterval(() => {
            if (progress < 95) {
                progress += 0.5;
                loaderBar.style.width = progress + '%';
            } else {
                clearInterval(interval);
            }
        }, 200);
    }

    function completeLoader() {
        if (!loaderBar) return;
        loaderBar.classList.add('complete');
        loaderBar.classList.remove('loading');
        
        setTimeout(() => {
            loaderBar.classList.add('fade-out');
            setTimeout(() => {
                loaderBar.style.width = '0%';
                loaderBar.classList.remove('complete', 'fade-out');
            }, 400);
        }, 300);
    }

    
    document.addEventListener('click', (e) => {
        const link = e.target.closest('a');
        if (!link) return;

        
        const href = link.getAttribute('href');
        const target = link.getAttribute('target');
        const isExternal = href && (href.startsWith('http') && !href.includes(window.location.host));
        const isAction = !href || href.startsWith('#') || href.startsWith('javascript:');
        const isDownload = link.hasAttribute('download');

        if (target === '_blank' || isExternal || isAction || isDownload) {
            return;
        }

        
        startLoader();
    });

    
    document.addEventListener('submit', (e) => {
        const form = e.target;
        if (form.getAttribute('target') === '_blank' || form.classList.contains('no-loader')) return;
        startLoader();
    });

    
    window.addEventListener('pageshow', (event) => {
        if (event.persisted) {
            completeLoader();
        }
    });

    
    completeLoader();

    
    document.addEventListener('submit', async (e) => {
        if (e.target.id !== 'data-report-form') return;
        
        e.preventDefault();
        const reportForm = e.target;
        const submitBtn = reportForm.querySelector('.confirm-btn-submit');
        const alertContainer = document.getElementById('data-report-alert-container');
        
        
        const modal = document.getElementById('data-report-modal');
        const confirmBox = modal ? modal.querySelector('.shiori-confirm-box') : null;
        if (!confirmBox) return;

        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Enviando...';
        }
        if (alertContainer) alertContainer.innerHTML = '';

        try {
            const formData = new FormData(reportForm);
            const res = await fetch(reportForm.action, {
                method: 'POST',
                body: formData
            });
            const result = await res.json();

            if (result.category === 'success' || result.category === 'info') {
                
                const isSuccess = result.category === 'success';
                const iconClass = isSuccess ? 'check-circle' : 'info-circle';
                const statusClass = isSuccess ? 'icon-success-shiori' : 'icon-info-shiori';
                const titleText = isSuccess ? '¡Hecho!' : 'Aviso';

                confirmBox.innerHTML = `
                    <div class="confirm-icon ${statusClass}">
                        <i class="fas fa-${iconClass}"></i>
                    </div>
                    <h3>${titleText}</h3>
                    <p>${result.message}</p>
                    <div class="confirm-actions">
                        <button class="confirm-btn shiori-cancel" id="finish-data-report" style="flex: 1; margin-top: 20px;">Entendido</button>
                    </div>
                `;

                
                const finishBtn = document.getElementById('finish-data-report');
                if (finishBtn) {
                    finishBtn.onclick = () => {
                        modal.classList.remove('show');
                        document.body.style.overflow = '';
                        
                        const originalHtml = modal.dataset.originalHtml;
                        if (originalHtml) {
                            setTimeout(() => { confirmBox.innerHTML = originalHtml; }, 300);
                        }
                    };
                }
            } else {
                if (alertContainer) {
                    alertContainer.innerHTML = `
                        <div class="alert-error" style="margin-bottom: 20px;">
                            <i class="fas fa-exclamation-circle"></i> ${result.message}
                        </div>
                    `;
                }
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = 'Enviar Reporte';
                }
            }

        } catch (err) {
            console.error("Error en reporte:", err);
            if (alertContainer) {
                alertContainer.innerHTML = `<div class="alert-error" style="margin-bottom:20px;"><i class="fas fa-exclamation-circle"></i> Error de conexión.</div>`;
            }
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = 'Enviar Reporte';
            }
        }
    });

    
    function initDataReport() {
        const openBtn = document.getElementById('open-report-modal-btn');
        const modal = document.getElementById('data-report-modal');
        const closeBtn = document.getElementById('close-data-modal');
        const confirmBox = modal ? modal.querySelector('.shiori-confirm-box') : null;

        if (!openBtn || !modal || !confirmBox) return;

        
        const originalContent = confirmBox.innerHTML;
        modal.dataset.originalHtml = originalContent;

        openBtn.onclick = (e) => {
            e.preventDefault();
            modal.classList.add('show');
            document.body.style.overflow = 'hidden';
        };

        const close = () => {
            modal.classList.remove('show');
            document.body.style.overflow = '';
            
            setTimeout(() => { confirmBox.innerHTML = originalContent; }, 300);
        };

        if (closeBtn) closeBtn.onclick = close;
        modal.onclick = (e) => {
            if (e.target === modal) close();
        };
    }

    initDataReport();
});


window.selectReportOption = function(element, value) {
    const parent = element.closest('.report-options-list') || document;
    parent.querySelectorAll('.report-option-item').forEach(el => el.classList.remove('selected'));
    element.classList.add('selected');
    const hiddenInput = document.getElementById('selected-field-type');
    if (hiddenInput) hiddenInput.value = value;
};


window.SHIORI = {
    
    initRegionSelector: function(config) {
        const container = config.container || document.getElementById(config.containerId);
        if (!container) return;

        const countries = config.countries || [];
        const btn = container.querySelector('.region-dropdown-btn');
        const display = container.querySelector('.selected-region');
        const listContainer = container.querySelector('.region-list') || container.querySelector('ul');
        const searchInput = container.querySelector('.region-search-box input') || container.querySelector('#region-search-input');
        const hiddenInput = container.querySelector('input[type="hidden"]');
        const placeholder = config.placeholder || "Selecciona un país...";

        function renderDisplay(code) {
            const country = countries.find(c => c.code === code);
            if (country && display) {
                display.innerHTML = `<span class="flag">${country.emoji}</span><span class="name">${country.name}</span><span class="code">${country.code}</span>`;
                if (hiddenInput) {
                    hiddenInput.value = country.code;
                    
                    hiddenInput.dispatchEvent(new Event('change'));
                }
                if (config.onSelect) config.onSelect(country);
            } else if (display) {
                display.innerHTML = placeholder;
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
                li.className = `region-item ${country.code === (hiddenInput ? hiddenInput.value : '') ? 'selected' : ''}`;
                li.innerHTML = `<span class="flag">${country.emoji}</span><span class="name">${country.name}</span><span class="code">${country.code}</span>`;
                
                li.addEventListener('click', (e) => {
                    e.stopPropagation();
                    renderDisplay(country.code);
                    container.classList.remove('open');
                    if (searchInput) searchInput.value = "";
                });
                listContainer.appendChild(li);
            });
        }

        if (btn) {
            btn.onclick = (e) => {
                e.stopPropagation();
                const isOpen = container.classList.toggle('open');
                
                document.querySelectorAll('.custom-region-dropdown').forEach(d => {
                    if (d !== container) d.classList.remove('open');
                });
                if (isOpen && searchInput) {
                    searchInput.value = "";
                    renderList();
                    setTimeout(() => searchInput.focus(), 100);
                }
            };
        }

        if (searchInput) {
            searchInput.onclick = e => e.stopPropagation();
            searchInput.oninput = e => renderList(e.target.value);
        }

        document.addEventListener('click', (e) => {
            if (!container.contains(e.target)) container.classList.remove('open');
        });

        
        if (hiddenInput && hiddenInput.value) {
            renderDisplay(hiddenInput.value);
        } else if (config.defaultCountry) {
            renderDisplay(config.defaultCountry);
        }
        
        renderList();
    }
};