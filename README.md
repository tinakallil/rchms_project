# RCHMS – Remote Community Housing Management System

ICT712 Assessment 3 Part B reference implementation.

## 1. Prerequisites

| Tool | Version | Notes |
| --- | --- | --- |
| Python | 3.9 or higher | https://www.python.org/downloads/ |
| MySQL Server | 8.x Community | Free from https://dev.mysql.com/downloads/mysql/ |
| Redis | 7.x | On Windows use Memurai or the WSL2 Redis package |
| Visual Studio Code | latest | Mandatory IDE for the assessment |
| Git | latest | https://git-scm.com/ |

## 2. Installation steps

```bash
# 1. Clone or extract the project
cd rchms_project

# 2. Create a virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create the MySQL database (login to MySQL first)
#    mysql -u root -p
#    > CREATE DATABASE rchms_db CHARACTER SET utf8mb4;
#    > exit

# 5. Apply migrations
python manage.py makemigrations housing
python manage.py migrate

# 6. (Optional) Seed demo data
python manage.py seed_data

# 7. Create your own superuser
python manage.py createsuperuser
```

> **Tip for quick testing without MySQL:** open `config/settings.py`,
> comment out the MySQL `DATABASES` block, and uncomment the SQLite
> block underneath. Migrations and tests will work immediately.

## 3. Running the application

You need three terminal windows (or VS Code split terminals):

```bash
# Terminal 1 – Redis (skip on Windows if Redis runs as a service)
redis-server

# Terminal 2 – Celery worker + beat (development mode)
celery -A config worker --beat -l info --scheduler django

# Terminal 3 – Django dev server
python manage.py runserver
```

Open http://127.0.0.1:8000/ and sign in.

## 4. Demo users (created by `seed_data`)

| Username | Role | Password |
| --- | --- | --- |
| admin_user | System Administrator | Passw0rd! |
| helen_officer | Housing Officer | Passw0rd! |
| sam_supervisor | Maintenance Supervisor | Passw0rd! |
| mia_manager | Community Manager | Passw0rd! |
| tom_tenant | Tenant | Passw0rd! |
| alice_tenant | Tenant | Passw0rd! |

## 5. Running unit tests

```bash
python manage.py test housing -v 2
```

You should see all tests pass (~10 tests covering models, RBAC views, and Celery tasks).

## 6. Triggering the urgent-repair email

1. Log in as `tom_tenant`.
2. Create a new repair request with priority **URGENT**.
3. Watch the Celery worker terminal — the email body is printed via the
   console email backend.

## 7. Triggering the weekly summary manually

```bash
python manage.py shell
>>> from housing.tasks import send_weekly_maintenance_summary
>>> send_weekly_maintenance_summary.delay()
```

## 8. Project layout

```
rchms_project/
├── manage.py
├── requirements.txt
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── celery.py
│   └── wsgi.py
├── housing/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── forms.py
│   ├── admin.py
│   ├── tasks.py
│   ├── signals.py
│   ├── decorators.py
│   ├── tests.py
│   └── management/commands/seed_data.py
├── templates/
│   ├── base.html
│   ├── registration/login.html
│   └── housing/*.html
└── static/css/style.css
```
