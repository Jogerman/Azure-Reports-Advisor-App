# This will make Python treat the directory as a package

# Version
__version__ = '1.4.0'

# Import Celery app to ensure it's loaded when Django starts
from .celery import app as celery_app

__all__ = ('celery_app',)