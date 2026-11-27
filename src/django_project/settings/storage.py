from django_project.settings import BASE_DIR

# Collected in the Docker image, served by Django (admin only, low traffic)
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
