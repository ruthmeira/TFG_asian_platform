/**
 * PROFILE PAGE JAVASCRIPT
 * Handles specialized interactions for Profile pages
 */

document.addEventListener('DOMContentLoaded', () => {
    
    // 1. IMAGE PREVIEW (Real-time avatar update)
    // Only handles the specific preview on Edit Profile
    const profileInput = document.getElementById('profile_image');
    if (profileInput) {
        profileInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(event) {
                    const preview = document.getElementById('avatarPreview');
                    if (!preview) return;

                    let img = preview.querySelector('.avatar-img-clean');
                    const initial = preview.querySelector('.avatar-initial');

                    if (!img) {
                        img = document.createElement('img');
                        img.className = 'avatar-img-clean';
                        if (initial) initial.remove();
                        preview.prepend(img);
                    }
                    img.src = event.target.result;
                };
                reader.readAsDataURL(file);
            }
        });
    }

    // 2. CHARACTER COUNTER (Biography limit display)
    // Unique to the edit profile bio textarea
    const bioTextarea = document.querySelector('textarea[name="bio"]');
    const charCounter = document.querySelector('.char-counter');
    if (bioTextarea && charCounter) {
        const updateCounter = () => {
             const length = bioTextarea.value.length;
             charCounter.textContent = `${length} / 500 caracteres`;
             if (length > 450) {
                 charCounter.style.color = 'var(--primary)';
             } else {
                 charCounter.style.color = 'rgba(255, 255, 255, 0.3)';
             }
        };

        bioTextarea.addEventListener('input', updateCounter);
        updateCounter(); 
    }

    // NOTE: Password toggle and CapsLock warning are handled globally in main.js
    // to avoid redundant event listeners and flickering.
});
