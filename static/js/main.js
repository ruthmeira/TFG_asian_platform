/**
 * MAIN GLOBAL JAVASCRIPT
 * Handles global interactions like Auth forms, Navbar, etc.
 */

document.addEventListener("DOMContentLoaded", function () {
    
    // --- LÓGICA DE MOSTRAR CONTRASEÑA Y MAYÚSCULAS ---
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
});