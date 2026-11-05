const container = document.getElementById('bookings-container');

function getCsrfToken() {
    const cookies = document.cookie.split(';');

    for (let cookie of cookies) {
        cookie = cookie.trim();

        if (cookie.startsWith('csrftoken=')) {
            return cookie.substring('csrftoken='.length);
        }
    }

    return '';
}

function formatDate(date) {
    const [year, month, day] = date.split('-');
    return `${day}/${month}/${year}`;
}

function createBookingCard(booking) {
    const card = document.createElement('article');
    card.className = 'booking-card';

    const info = document.createElement('div');
    info.className = 'booking-info';

    const date = document.createElement('h3');
    date.className = 'booking-date';
    date.textContent = formatDate(booking.day.date);

    const details = document.createElement('div');
    details.className = 'booking-details';

    const time = document.createElement('p');
    time.innerHTML = '<strong>Time:</strong> ';
    time.append(document.createTextNode(booking.time.slice(0, 5)));

    const name = document.createElement('p');
    name.innerHTML = '<strong>Name:</strong> ';
    name.append(document.createTextNode(booking.customer_name));

    const email = document.createElement('p');
    email.innerHTML = '<strong>Email:</strong> ';
    email.append(document.createTextNode(booking.customer_email));

    details.append(time, name, email);
    info.append(date, details);

    const cancelButton = document.createElement('button');
    cancelButton.className = 'cancel-button';
    cancelButton.textContent = 'Cancel Booking';

    cancelButton.addEventListener('click', () => {
        cancelBooking(booking.id, card, cancelButton);
    });

    card.append(info, cancelButton);

    return card;
}

async function loadBookings() {
    container.textContent = 'Loading bookings...';

    try {
        const response = await fetch(bookingsUrl, {
            method: 'GET',
            credentials: 'same-origin'
        });

        if (!response.ok) {
            throw new Error('Failed to load bookings.');
        }

        const bookings = await response.json();

        container.replaceChildren();

        if (bookings.length === 0) {
            container.textContent = 'You have no bookings yet.';
            return;
        }

        bookings.forEach(booking => {
            const card = createBookingCard(booking);
            container.appendChild(card);
        });

    } catch (error) {
        container.textContent = error.message;
    }
}

async function cancelBooking(id, card, button) {
    const confirmed = confirm(
        'Are you sure you want to cancel this booking?'
    );

    if (!confirmed) return;

    button.disabled = true;
    button.textContent = 'Cancelling...';

    try {
        const url = cancelUrl.replace('/0/', `/${id}/`);

        const response = await fetch(url, {
            method: 'DELETE',
            credentials: 'same-origin',
            headers: {
                'X-CSRFToken': getCsrfToken()
            }
        });

        if (!response.ok) {
            throw new Error('Failed to cancel booking.');
        }

        card.remove();

        if (container.children.length === 0) {
            container.textContent = 'You have no bookings yet.';
        }

        alert('Booking cancelled successfully.');

    } catch (error) {
        alert(error.message);
        button.disabled = false;
        button.textContent = 'Cancel Booking';
    }
}

loadBookings();
