from django_project.settings import BASE_DIR

# Collected in the Docker image, served by Django (admin, Swagger: low load)
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
# Found before app files: ours replace the DMR Swagger ones of the same path
STATICFILES_DIRS = [BASE_DIR / "static"]
