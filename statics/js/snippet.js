/*!
 * Bookly Appointment Form
 * Vanilla JavaScript - Django REST Framework
 */
(() => {
  'use strict';

  const root = document.querySelector('.cl-appt04');

  if (!root) {
    console.error('Appointment form root was not found.');
    return;
  }

  const LENGTH = 30;

  const availabilityUrl = root.dataset.availabilityUrl;
  const holdUrl = root.dataset.holdUrl;
  const releaseUrl = root.dataset.releaseUrl;
  const loginUrl = root.dataset.loginUrl;
  const isAuthenticated = root.dataset.authenticated === 'true';

  const $ = (selector) => root.querySelector(selector);

  // Get CSRF token from cookie or hidden form input.
  const csrfToken = () => {
    const cookie = document.cookie
      .split('; ')
      .find((item) => item.startsWith('csrftoken='));

    if (cookie) {
      return decodeURIComponent(
        cookie.split('=').slice(1).join('=')
      );
    }

    const input = root.querySelector(
      '[name="csrfmiddlewaretoken"]'
    );

    return input ? input.value : '';
  };

  // Send POST requests to Django API.
  const postJson = async (url, data) => {
    if (!url) {
      throw new Error('Required API URL is missing.');
    }

    const response = await fetch(url, {
      method: 'POST',
      credentials: 'same-origin',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-CSRFToken': csrfToken()
      },
      body: JSON.stringify(data)
    });

    let result = {};

    try {
      result = await response.json();
    } catch (error) {
      // Response was not JSON.
    }

    if (!response.ok) {
      throw new Error(
        result.error ||
        result.detail ||
        `Request failed. HTTP ${response.status}`
      );
    }

    return result;
  };

  const views = {
    pick: $('[data-view="pick"]'),
    details: $('[data-view="details"]'),
    done: $('[data-view="done"]')
  };

  const daysBody = $('[data-days]');
  const monthLabel = $('[data-month]');
  const prevBtn = $('[data-prev]');
  const nextBtn = $('[data-next]');
  const timesList = $('[data-times]');
  const dayLabel = $('[data-day]');
  const live = $('[data-live]');

  if (
    !views.pick ||
    !views.details ||
    !views.done ||
    !daysBody ||
    !monthLabel ||
    !prevBtn ||
    !nextBtn ||
    !timesList ||
    !dayLabel
  ) {
    console.error(
      'Appointment form is missing required HTML elements.'
    );
    return;
  }

  let zone = 'UTC';

  try {
    zone = Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC';
  } catch (error) {
    console.warn('Could not determine timezone.', error);
  }

  const state = {
    view: null,
    selected: null,
    slot: null,
    h12: true,
    slots: new Map()
  };

  const reservationByTimestamp = new Map();

  // The reservation currently held by this browser session.
  let heldReservationId = null;

  const announce = (message) => {
    if (live) {
      live.textContent = message;
    }
  };

  const pad = (number) => {
    return String(number).padStart(2, '0');
  };

  const keyToUTC = (key) => {
    const [year, month, day] = key.split('-').map(Number);

    return new Date(
      Date.UTC(year, month - 1, day, 12)
    );
  };

  const addDays = (key, amount) => {
    const date = keyToUTC(key);

    date.setUTCDate(date.getUTCDate() + amount);

    return date.toISOString().slice(0, 10);
  };

  const todayKey = (() => {
    const now = new Date();

    return [
      now.getFullYear(),
      pad(now.getMonth() + 1),
      pad(now.getDate())
    ].join('-');
  })();

  const fmt = {
    long: new Intl.DateTimeFormat('en-US', {
      timeZone: 'UTC',
      weekday: 'long',
      month: 'long',
      day: 'numeric',
      year: 'numeric'
    }),

    day: new Intl.DateTimeFormat('en-US', {
      timeZone: 'UTC',
      weekday: 'long',
      month: 'long',
      day: 'numeric'
    }),

    month: new Intl.DateTimeFormat('en-US', {
      timeZone: 'UTC',
      month: 'long',
      year: 'numeric'
    }),

    zoneName: (() => {
      try {
        const parts = new Intl.DateTimeFormat('en-US', {
          timeZone: zone,
          timeZoneName: 'short'
        }).formatToParts(new Date());

        return (
          parts.find(
            (part) => part.type === 'timeZoneName'
          ) || {}
        ).value || '';
      } catch (error) {
        return '';
      }
    })()
  };

  const timeOf = (timestamp) => {
    return new Intl.DateTimeFormat('en-US', {
      timeZone: 'UTC',
      hour: 'numeric',
      minute: '2-digit',
      hour12: state.h12
    }).format(new Date(timestamp));
  };

  const keys = () => {
    return Array.from(state.slots.keys()).sort();
  };

  const available = (key) => {
    return (
      state.slots.has(key) &&
      state.slots.get(key).length > 0
    );
  };

  let view = {
    y: 0,
    m: 0
  };

  const minMonth = () => {
    const [year, month] = todayKey.split('-').map(Number);

    return year * 12 + month - 1;
  };

  const maxMonth = () => {
    const last = keys().pop() || todayKey;

    const [year, month] = last.split('-').map(Number);

    return year * 12 + month - 1;
  };

  // Render calendar.
  const renderMonth = (focusKey) => {
    const first = new Date(
      Date.UTC(view.y, view.m, 1, 12)
    );

    monthLabel.textContent = fmt.month.format(first);

    const monthIndex = view.y * 12 + view.m;

    prevBtn.disabled = monthIndex <= minMonth();
    nextBtn.disabled = monthIndex >= maxMonth();

    daysBody.textContent = '';

    const leadingDays = (
      first.getUTCDay() + 6
    ) % 7;

    const dayCount = new Date(
      Date.UTC(view.y, view.m + 1, 0)
    ).getUTCDate();

    const datesInMonth = [];

    for (let day = 1; day <= dayCount; day++) {
      datesInMonth.push(
        `${view.y}-${pad(view.m + 1)}-${pad(day)}`
      );
    }

    const focusTarget = [
      focusKey,
      state.selected
    ].find(
      (key) => key && datesInMonth.includes(key)
    ) || datesInMonth.find(available) || datesInMonth[0];

    let row = null;

    for (
      let index = 0;
      index < leadingDays + dayCount;
      index++
    ) {
      if (index % 7 === 0) {
        row = document.createElement('tr');
        daysBody.appendChild(row);
      }

      const cell = document.createElement('td');

      if (index >= leadingDays) {
        const key = datesInMonth[index - leadingDays];

        const isAvailable = available(key);

        const button = document.createElement('button');

        button.type = 'button';
        button.className = 'cl-appt04__daybtn';
        button.dataset.date = key;

        button.textContent = String(
          index - leadingDays + 1
        );

        if (isAvailable) {
          button.classList.add('is-open');
        }

        if (key === todayKey) {
          button.classList.add('is-today');
        }

        button.tabIndex = key === focusTarget ? 0 : -1;

        button.setAttribute(
          'aria-pressed',
          String(key === state.selected)
        );

        const count = isAvailable
          ? state.slots.get(key).length
          : 0;

        button.setAttribute(
          'aria-label',
          `${fmt.long.format(keyToUTC(key))}` +
          `${key === todayKey ? ', today' : ''}, ` +
          `${isAvailable
            ? `${count} ${count === 1 ? 'time' : 'times'} available`
            : 'unavailable'
          }`
        );

        if (!isAvailable) {
          button.setAttribute('aria-disabled', 'true');
        }

        cell.appendChild(button);
      }

      row.appendChild(cell);
    }

    while (row && row.children.length < 7) {
      row.appendChild(document.createElement('td'));
    }

    if (focusKey) {
      const target = daysBody.querySelector(
        `[data-date="${focusKey}"]`
      );

      if (target) {
        target.focus();
      }
    }
  };

  const showMonthOf = (key, focus) => {
    const [year, month] = key.split('-').map(Number);

    view = {
      y: year,
      m: month - 1
    };

    renderMonth(focus ? key : null);
  };

  // Select a calendar day.
  const selectDay = (key) => {
    if (!available(key)) return;

    state.selected = key;
    state.slot = null;

    daysBody.querySelectorAll('[data-date]').forEach(
      (button) => {
        button.setAttribute(
          'aria-pressed',
          String(button.dataset.date === key)
        );

        button.tabIndex = button.dataset.date === key ? 0 : -1;
      }
    );

    renderTimes();

    announce(
      `${fmt.day.format(keyToUTC(key))}: ` +
      `${state.slots.get(key).length} times available.`
    );
  };

  // Calendar interactions.
  const initCalendar = () => {
    prevBtn.addEventListener('click', () => {
      const date = new Date(
        Date.UTC(view.y, view.m - 1, 1)
      );

      view = {
        y: date.getUTCFullYear(),
        m: date.getUTCMonth()
      };

      renderMonth();
    });

    nextBtn.addEventListener('click', () => {
      const date = new Date(
        Date.UTC(view.y, view.m + 1, 1)
      );

      view = {
        y: date.getUTCFullYear(),
        m: date.getUTCMonth()
      };

      renderMonth();
    });

    daysBody.addEventListener('click', (event) => {
      const button = event.target.closest('[data-date]');

      if (button && available(button.dataset.date)) {
        selectDay(button.dataset.date);
      }
    });

    daysBody.addEventListener('keydown', (event) => {
      const button = event.target.closest('[data-date]');

      if (!button) return;

      const key = button.dataset.date;

      const dayOfWeek = (
        keyToUTC(key).getUTCDay() + 6
      ) % 7;

      const moves = {
        ArrowLeft: -1,
        ArrowRight: 1,
        ArrowUp: -7,
        ArrowDown: 7,
        Home: -dayOfWeek,
        End: 6 - dayOfWeek
      };

      let target = null;

      if (event.key in moves) {
        target = addDays(key, moves[event.key]);
      } else if (
        event.key === 'PageUp' ||
        event.key === 'PageDown'
      ) {
        const date = keyToUTC(key);

        date.setUTCMonth(
          date.getUTCMonth() +
          (event.key === 'PageUp' ? -1 : 1)
        );

        target = date.toISOString().slice(0, 10);
      } else {
        return;
      }

      event.preventDefault();

      const [targetYear, targetMonth] = target
        .split('-')
        .map(Number);

      const targetMonthIndex =
        targetYear * 12 + targetMonth - 1;

      if (
        targetMonthIndex < minMonth() ||
        targetMonthIndex > maxMonth()
      ) {
        return;
      }

      if (
        targetYear === view.y &&
        targetMonth - 1 === view.m
      ) {
        const nextButton = daysBody.querySelector(
          `[data-date="${target}"]`
        );

        if (!nextButton) return;

        daysBody.querySelectorAll('[data-date]').forEach(
          (item) => {
            item.tabIndex = item === nextButton ? 0 : -1;
          }
        );

        nextButton.focus();
      } else {
        showMonthOf(target, true);
      }
    });
  };

  // Render available time slots.
  const renderTimes = () => {
    timesList.textContent = '';

    if (
      !state.selected ||
      !state.slots.has(state.selected)
    ) {
      dayLabel.textContent = 'Pick a day';
      updatePicked();
      return;
    }

    dayLabel.textContent = fmt.day.format(
      keyToUTC(state.selected)
    );

    state.slots.get(state.selected).forEach(
      (timestamp) => {
        const item = document.createElement('li');

        item.className = 'cl-appt04__slot';

        const button = document.createElement('button');

        button.type = 'button';
        button.className = 'cl-appt04__time';
        button.dataset.ts = String(timestamp);
        button.textContent = timeOf(timestamp);

        button.setAttribute(
          'aria-pressed',
          String(timestamp === state.slot)
        );

        item.appendChild(button);

        if (timestamp === state.slot) {
          item.classList.add('is-picked');

          const nextButton = document.createElement('button');

          nextButton.type = 'button';
          nextButton.className = 'cl-appt04__next';
          nextButton.dataset.goNext = '';
          nextButton.textContent = 'Next';

          nextButton.setAttribute(
            'aria-label',
            `Next: confirm ${timeOf(timestamp)}`
          );

          item.appendChild(nextButton);
        }

        timesList.appendChild(item);
      }
    );

    updatePicked();
  };

  // Select a time and hold it when Next is clicked.
  const initTimes = () => {
    timesList.addEventListener('click', async (event) => {

      // User clicked Next.
      if (event.target.closest('[data-go-next]')) {
        if (state.slot === null) return;

        const reservation = reservationByTimestamp.get(
          state.slot
        );

        if (!reservation) {
          announce('Please select an available time again.');
          return;
        }

        const nextButton = event.target.closest('[data-go-next]');

        nextButton.disabled = true;
        nextButton.textContent = 'Please wait…';

        try {
          // Release previous hold if user selected another slot.
          if (
            heldReservationId !== null &&
            Number(heldReservationId) !== Number(reservation.id)
          ) {
            await postJson(releaseUrl, {
              reservation_id: heldReservationId
            });

            heldReservationId = null;
          }

          // Create temporary hold in Django.
          await postJson(holdUrl, {
            reservation_id: reservation.id
          });

          heldReservationId = reservation.id;

          // If user is anonymous, redirect to login.
          if (!isAuthenticated) {
            if (!loginUrl) {
              throw new Error('Login URL is missing.');
            }

            const returnUrl = new URL(window.location.href);

            returnUrl.searchParams.set(
              'reservation_id',
              reservation.id
            );

            const target = new URL(
              loginUrl,
              window.location.origin
            );

            target.searchParams.set(
              'next',
              returnUrl.toString()
            );

            window.location.assign(target.toString());

            return;
          }

          // Logged-in user goes directly to details form.
          go('details');

        } catch (error) {
          console.error('Could not hold reservation:', error);

          announce(
            error.message ||
            'Could not reserve this time. Please choose another.'
          );

          alert(
            error.message ||
            'Could not reserve this time. Please choose another.'
          );

          try {
            await loadAvailableSlots();

            renderMonth();
            renderTimes();

          } catch (refreshError) {
            console.error(
              'Could not refresh availability:',
              refreshError
            );
          }

        } finally {
          if (nextButton.isConnected) {
            nextButton.disabled = false;
            nextButton.textContent = 'Next';
          }
        }

        return;
      }

      // User selected a time.
      const button = event.target.closest('[data-ts]');

      if (!button) return;

      state.slot = Number(button.dataset.ts);

      renderTimes();

      const selectedButton = timesList.querySelector(
        `[data-ts="${state.slot}"]`
      );

      if (selectedButton) {
        selectedButton.focus();
      }

      announce(
        `${timeOf(state.slot)} selected. Press Next to continue.`
      );
    });

    // 12-hour / 24-hour format.
    root.querySelectorAll('[data-fmt]').forEach((button) => {
      button.addEventListener('click', () => {
        state.h12 = button.dataset.fmt === '12';

        root.querySelectorAll('[data-fmt]').forEach(
          (item) => {
            item.setAttribute(
              'aria-pressed',
              String(item === button)
            );
          }
        );

        renderTimes();
      });
    });
  };

  const whenText = () => {
    if (state.slot === null || !state.selected) {
      return '';
    }

    const startTime = timeOf(state.slot);

    const endTime = timeOf(
      state.slot + LENGTH * 60000
    );

    return (
      `${startTime} – ${endTime}, ` +
      `${fmt.day.format(keyToUTC(state.selected))}`
    );
  };

  const updatePicked = () => {
    const box = $('[data-picked]');
    const value = $('[data-picked-value]');

    if (box) {
      box.hidden = (
        state.slot === null ||
        state.view === 'pick'
      );
    }

    if (value) {
      value.textContent = whenText();
    }
  };

  // Switch between calendar, details and success views.
  const go = (name) => {
    state.view = name;

    Object.keys(views).forEach((key) => {
      views[key].hidden = key !== name;
    });

    updatePicked();

    if (name === 'details') {
      const when = $('[data-when]');

      if (when) {
        when.textContent = `${whenText()} (${zone})`;
      }

      const nameInput = $('#cl-appt04-name');

      if (nameInput) {
        nameInput.focus();
      }
    }
  };

  const messageFor = (element) => {
    const validity = element.validity;

    if (validity.valueMissing) {
      return element.dataset.msgRequired ||
        'This field is required.';
    }

    if (validity.typeMismatch) {
      return element.dataset.msgType ||
        'Please check the format.';
    }

    if (validity.tooShort) {
      return `Please enter at least ${element.minLength} characters.`;
    }

    return '';
  };

  const validate = (element) => {
    const wrapper = element.closest('[data-field]');

    const error = wrapper &&
      wrapper.querySelector('[data-error]');

    const valid = element.checkValidity();

    if (wrapper) {
      wrapper.classList.toggle('is-error', !valid);
    }

    if (valid) {
      element.removeAttribute('aria-invalid');
    } else {
      element.setAttribute('aria-invalid', 'true');
    }

    if (error) {
      error.textContent = valid ? '' : messageFor(element);
    }

    return valid;
  };

  // Download appointment as calendar file.
  const downloadIcs = () => {
    if (state.slot === null) return;

    const stamp = (timestamp) => {
      return new Date(timestamp)
        .toISOString()
        .replace(/[-:]/g, '')
        .replace(/\.\d{3}/, '');
    };

    const ics = [
      'BEGIN:VCALENDAR',
      'VERSION:2.0',
      'PRODID:-//Bookly//Appointment Booking//EN',
      'BEGIN:VEVENT',
      `UID:${state.slot}@bookly.example`,
      `DTSTAMP:${stamp(Date.now())}`,
      `DTSTART:${stamp(state.slot)}`,
      `DTEND:${stamp(state.slot + LENGTH * 60000)}`,
      'SUMMARY:Appointment',
      'LOCATION:Video call',
      'END:VEVENT',
      'END:VCALENDAR'
    ].join('\r\n');

    const url = URL.createObjectURL(
      new Blob([ics], {
        type: 'text/calendar'
      })
    );

    const link = document.createElement('a');

    link.href = url;
    link.download = 'appointment.ics';

    document.body.appendChild(link);

    link.click();

    link.remove();

    setTimeout(() => {
      URL.revokeObjectURL(url);
    }, 1000);
  };

  // Details form and final booking.
  const initDetails = () => {
    const form = views.details;

    const button = $('[data-submit]');
    const label = $('[data-submit-label]');

    let busy = false;

    form.addEventListener('focusout', (event) => {
      if (
        event.relatedTarget &&
        event.relatedTarget.type === 'submit'
      ) {
        return;
      }

      const element = event.target;

      if (
        !element.matches ||
        !element.matches('input')
      ) {
        return;
      }

      if (
        element.value !== '' ||
        element.dataset.touched
      ) {
        element.dataset.touched = '1';

        validate(element);
      }
    });

    form.addEventListener('input', (event) => {
      if (
        event.target.dataset &&
        event.target.dataset.touched
      ) {
        validate(event.target);
      }
    });

    // Back to calendar.
    $('[data-back]').addEventListener('click', () => {
      go('pick');

      const selectedButton = timesList.querySelector(
        `[data-ts="${state.slot}"]`
      );

      if (selectedButton) {
        selectedButton.focus();
      }
    });

    // Submit real reservation request.
    form.addEventListener('submit', async (event) => {
      event.preventDefault();

      if (busy) return;

      const fields = Array.from(
        form.querySelectorAll('input[required]')
      );

      const invalidFields = fields.filter((element) => {
        element.dataset.touched = '1';

        return !validate(element);
      });

      if (invalidFields.length) {
        invalidFields[0].focus();

        announce(
          `Please fix ${invalidFields.length} ` +
          `${invalidFields.length === 1 ? 'field' : 'fields'}.`
        );

        return;
      }

      if (state.slot === null) {
        announce(
          'Your selected time is missing. Please select a time again.'
        );

        go('pick');

        return;
      }

      const reservation = reservationByTimestamp.get(
        state.slot
      );

      if (!reservation) {
        announce(
          'Your selected reservation could not be found. Please select again.'
        );

        go('pick');

        return;
      }

      busy = true;

      button.disabled = true;

      button.setAttribute(
        'aria-disabled',
        'true'
      );

      form.setAttribute('aria-busy', 'true');

      label.textContent = 'Scheduling…';

      try {
        const fullName = $('#cl-appt04-name').value.trim();
        const email = $('#cl-appt04-email').value.trim();
        const meetingTopic = $('#cl-appt04-notes').value.trim();

        const result = await postJson(availabilityUrl, {
            reservation_id: reservation.id,
            customer_name: fullName,
            customer_email: email,
            meeting_topic: meetingTopic
        });

        // Booking succeeded.
        heldReservationId = null;

        const firstName = fullName.split(/\s+/)[0];

        $('[data-done-text]').textContent =
          `Thanks, ${firstName}. Your appointment has been confirmed.`;

        $('[data-done-when]').textContent = whenText();

        $('[data-done-zone]').textContent =
          `${zone}${fmt.zoneName ? ` (${fmt.zoneName})` : ''}`;

        go('done');

        views.done.focus();

        announce(
          result.message ||
          'Your appointment has been confirmed.'
        );

      } catch (error) {
        console.error(
          'Could not confirm reservation:',
          error
        );

        announce(
          error.message ||
          'Could not schedule your appointment.'
        );

        alert(
          error.message ||
          'Could not schedule your appointment.'
        );

        try {
          await loadAvailableSlots();

          renderMonth();
          renderTimes();

        } catch (refreshError) {
          console.error(
            'Could not refresh availability:',
            refreshError
          );
        }

        go('pick');

      } finally {
        busy = false;

        button.disabled = false;

        button.removeAttribute('aria-disabled');

        form.removeAttribute('aria-busy');

        label.textContent = 'Schedule call';
      }
    });

    $('[data-ics]').addEventListener(
      'click',
      downloadIcs
    );

    // Start another booking.
    $('[data-again]').addEventListener('click', async () => {
      form.reset();

      form.querySelectorAll('input, textarea').forEach(
        (element) => {
          delete element.dataset.touched;

          element.removeAttribute('aria-invalid');
        }
      );

      form.querySelectorAll('.is-error').forEach(
        (element) => {
          element.classList.remove('is-error');
        }
      );

      form.querySelectorAll('[data-error]').forEach(
        (element) => {
          element.textContent = '';
        }
      );

      state.slot = null;
      state.selected = null;

      go('pick');

      try {
        await loadAvailableSlots();

        const firstAvailableDay = keys()[0];

        if (firstAvailableDay) {
          showMonthOf(firstAvailableDay, false);

          selectDay(firstAvailableDay);
        } else {
          renderMonth();
          renderTimes();
        }

      } catch (error) {
        console.error(
          'Could not reload available reservations:',
          error
        );
      }

      const selectedDay = daysBody.querySelector(
        '[aria-pressed="true"]'
      );

      if (selectedDay) {
        selectedDay.focus();
      }
    });
  };

  // Load available reservations from Django.
  const loadAvailableSlots = async () => {
    if (!availabilityUrl) {
      throw new Error(
        'Availability API URL is missing.'
      );
    }

    const response = await fetch(availabilityUrl, {
      credentials: 'same-origin',
      headers: {
        Accept: 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error(
        `Availability API returned HTTP ${response.status}.`
      );
    }

    const reservations = await response.json();

    if (!Array.isArray(reservations)) {
      throw new Error(
        'Availability API must return a JSON array.'
      );
    }

    state.slots.clear();

    reservationByTimestamp.clear();

    reservations.forEach((reservation) => {
      const date = reservation?.day?.date;

      const time = reservation?.time;

      if (
        typeof date !== 'string' ||
        typeof time !== 'string'
      ) {
        console.warn(
          'Skipping reservation with unexpected data:',
          reservation
        );

        return;
      }

      const dateMatch = date.match(
        /^(\d{4})-(\d{2})-(\d{2})$/
      );

      const timeMatch = time.match(
        /^(\d{2}):(\d{2})(?::\d{2}(?:\.\d+)?)?$/
      );

      if (!dateMatch || !timeMatch) {
        console.warn(
          'Skipping reservation with invalid date/time:',
          reservation
        );

        return;
      }

      const year = Number(dateMatch[1]);

      const month = Number(dateMatch[2]);

      const day = Number(dateMatch[3]);

      const hours = Number(timeMatch[1]);

      const minutes = Number(timeMatch[2]);

      if (
        month < 1 ||
        month > 12 ||
        day < 1 ||
        day > 31 ||
        hours > 23 ||
        minutes > 59
      ) {
        console.warn(
          'Skipping reservation with out-of-range date/time:',
          reservation
        );

        return;
      }

      // Django DateField and TimeField are wall-clock values.
      const timestamp = Date.UTC(
        year,
        month - 1,
        day,
        hours,
        minutes
      );

      if (!state.slots.has(date)) {
        state.slots.set(date, []);
      }

      state.slots.get(date).push(timestamp);

      reservationByTimestamp.set(
        timestamp,
        reservation
      );
    });

    state.slots.forEach((slots) => {
      slots.sort((a, b) => a - b);
    });

    return keys()[0] || null;
  };

  // Initialize application.
  const init = async () => {
    const zoneElement = $('[data-zone]');

    if (zoneElement) {
      zoneElement.textContent = 'the appointment time zone';
    }

    initCalendar();

    initTimes();

    initDetails();

    showMonthOf(todayKey, false);

    renderTimes();

    try {
      const firstAvailableDay = await loadAvailableSlots();

      const params = new URLSearchParams(
        window.location.search
      );

      const requestedReservationId = params.get(
        'reservation_id'
      );

      // User has returned from login.
      if (requestedReservationId) {
        const heldReservation = Array.from(
          reservationByTimestamp.entries()
        ).find(([, reservation]) => {
          return (
            String(reservation.id) ===
            String(requestedReservationId)
          );
        });

        if (heldReservation) {
          const [timestamp, reservation] = heldReservation;

          state.selected = reservation.day.date;

          state.slot = timestamp;

          heldReservationId = reservation.id;

          showMonthOf(state.selected, false);

          renderMonth();

          renderTimes();

          // Go directly to details form.
          go('details');

          // Remove reservation_id from browser address.
          const cleanUrl = new URL(window.location.href);

          cleanUrl.searchParams.delete('reservation_id');

          window.history.replaceState(
            {},
            '',
            cleanUrl.toString()
          );

        } else {
          // Hold has expired or is no longer available.
          showMonthOf(
            firstAvailableDay || todayKey,
            false
          );

          if (firstAvailableDay) {
            selectDay(firstAvailableDay);
          } else {
            state.selected = null;

            renderTimes();
          }

          go('pick');

          announce(
            'Your previous reservation hold is no longer active. Please select another time.'
          );
        }

      } else {
        // Normal first page load.
        showMonthOf(
          firstAvailableDay || todayKey,
          false
        );

        if (firstAvailableDay) {
          selectDay(firstAvailableDay);
        } else {
          state.selected = null;

          renderTimes();

          announce(
            'No available reservations were returned by the API.'
          );
        }

        go('pick');
      }

    } catch (error) {
      console.error(
        'Appointment calendar initialization failed:',
        error
      );

      announce(
        'Could not load available reservations. ' +
        'Check the browser console and API response.'
      );

      showMonthOf(todayKey, false);

      renderTimes();

      go('pick');
    }
  };

  // Start the application.
  init();

})();
