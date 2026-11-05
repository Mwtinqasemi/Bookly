const userMenuButton = document.getElementById('userMenuButton');
const userDropdown = document.getElementById('userDropdown');

if (userMenuButton && userDropdown) {

    userMenuButton.addEventListener('click', function (event) {

        event.stopPropagation();

        userDropdown.classList.toggle('show');

        const isOpen = userDropdown.classList.contains('show');

        userMenuButton.setAttribute('aria-expanded', isOpen);

    });

    document.addEventListener('click', function (event) {

        if (!event.target.closest('.user-menu')) {

            userDropdown.classList.remove('show');

            userMenuButton.setAttribute('aria-expanded', 'false');

        }

    });

    document.addEventListener('keydown', function (event) {

        if (event.key === 'Escape') {

            userDropdown.classList.remove('show');

            userMenuButton.setAttribute('aria-expanded', 'false');

        }

    });

}