/**
 * PROFILE PAGE JAVASCRIPT
 * Handles specialized interactions for Profile pages
 */

document.addEventListener('DOMContentLoaded', () => {

    // 1. IMAGE PREVIEW (Real-time avatar update)
    // Only handles the specific preview on Edit Profile
    const profileInput = document.getElementById('profile_image');
    if (profileInput) {
        profileInput.addEventListener('change', function (e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function (event) {
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

    // 3. DELETE ACCOUNT MODAL (Profile Actions)
    const openDelBtn = document.getElementById('open-delete-account-btn');
    const delModal = document.getElementById('delete-account-modal');
    const cancelDelBtn = document.getElementById('cancel-delete-account-btn');

    if (openDelBtn && delModal) {
        openDelBtn.addEventListener('click', () => {
            delModal.classList.remove('hidden');
            document.body.style.overflow = 'hidden'; 
        });

        const closeDel = () => {
            delModal.classList.add('hidden');
            document.body.style.overflow = '';
        };

        if (cancelDelBtn) cancelDelBtn.addEventListener('click', closeDel);

        delModal.addEventListener('click', (e) => {
            if (e.target === delModal) closeDel();
        });
    }

    // NOTE: Password toggle and CapsLock warning are handled globally in main.js
    // to avoid redundant event listeners and flickering.
});
