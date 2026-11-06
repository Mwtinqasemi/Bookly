# Bookly – Online Appointment Booking System

Bookly is a full-stack appointment booking platform built with Django and Django REST Framework. It provides a simple and reliable way for users to browse available time slots, reserve appointments, and manage their bookings.

The platform includes a RESTful API, interactive API documentation, automated appointment scheduling, and a temporary booking lock mechanism to prevent multiple users from booking the same time slot.

## 🌐 Live Demo

**[Visit Bookly](https://bookly-bulc.onrender.com/)**

## ✨ Features

### Appointment Booking
- Browse available appointment dates and time slots.
- Book appointments through an intuitive web interface.
- View and manage personal bookings.
- Cancel existing appointments.
- Prevent duplicate bookings for the same time slot.

### Temporary Booking Lock
- Available time slots are temporarily locked for **10 minutes** when a user starts the booking process.
- During this period, other users cannot reserve the same time slot.
- The user can complete the booking or cancel the reservation.
- If the booking is not completed within 10 minutes, the temporary lock expires automatically, making the time slot available again.

### Automated Appointment Scheduling
- New appointment slots are generated automatically every week.
- The scheduling process runs every **Saturday at 11:00 PM (Europe/Berlin time)**.
- New slots are created for the upcoming working week (Monday to Friday).
- Available appointment times are generated between 09:00–13:00 and 17:00–22:00, at 30-minute intervals.
- GitHub Actions automates the weekly scheduling process without requiring manual intervention.
- The generation process avoids creating duplicate dates or time slots.

### User Accounts
- User registration and authentication.
- Secure login and logout.
- User profile management.
- Personal appointment management.

### REST API
- Built with Django REST Framework.
- Structured API endpoints for booking operations.
- API documentation generated with Django REST Framework Spectacular.
- Interactive Swagger UI and ReDoc documentation.

## 🛠️ Tech Stack

| Category | Technologies |
|---|---|
| Backend | Python, Django |
| REST API | Django REST Framework |
| Database | PostgreSQL |
| API Documentation | DRF Spectacular, Swagger UI, ReDoc |
| Frontend | HTML, CSS, JavaScript |
| Deployment | Render |
| Database Hosting | Neon |
| Automation | GitHub Actions |
| Static Files | WhiteNoise |

## ⚙️ Automated Weekly Scheduling

Bookly uses GitHub Actions to automatically generate appointment slots every Saturday at 11:00 PM Berlin time.

The workflow executes the Django management command:

```bash
python manage.py generate_weekly_slots
```

This command:
1. Calculates the upcoming working week.
2. Creates appointment dates for Monday through Friday.
3. Generates available time slots for each working day.
4. Prevents duplicate entries using Django's `get_or_create()` mechanism.

The scheduling workflow is configured to run automatically, and it can also be triggered manually when needed.

## 📅 Appointment Schedule

| Working Days | Appointment Hours |
|---|---|
| Monday – Friday | 09:00 – 13:00 |
| Monday – Friday | 17:00 – 22:00 |

- Slot duration: 30 minutes
- Total available slots: 18 per working day
- Weekly availability: 90 appointment slots

## 🔌 API Documentation

Bookly provides interactive API documentation through Django REST Framework Spectacular.

- **Swagger UI:** `/api/docs/`
- **ReDoc:** `/api/redoc/`
- **OpenAPI Schema:** `/api/schema/`

You can explore the API endpoints and test requests directly through Swagger UI on the live website.

## 🔒 Security & Reliability

- Environment variables for sensitive configuration.
- PostgreSQL database in production.
- Secure authentication and authorization.
- Temporary appointment locks to reduce booking conflicts.
- Automated weekly scheduling.
- Database-level protection against duplicate appointment slots.

## 🚀 Deployment

The application is deployed on **Render**, with **Neon PostgreSQL** providing the production database.

GitHub Actions handles the automatic weekly appointment generation.

The live application is available through the link above, so you can explore and test Bookly directly without downloading or running the source code.

## 👨‍💻 Developer

**Matin Qasemi**

Backend Developer | Python & Django

- **GitHub:** [@Mwtinqasemi](https://github.com/Mwtinqasemi)
- **LinkedIn:** [Matin Qasemi](https://www.linkedin.com/in/matin-qasemi-81370b392/)

---

*Bookly – A practical appointment booking system powered by Django.*
