import os


class Parse:
    """Class of utility functions to parse environment variables"""

    @staticmethod
    def bool(field):
        """Parse booleans (defaults to False)"""
        return os.getenv(field, '').lower() in ['true', '1']


class Settings:

    # General
    DEV = Parse.bool('DEV')
    REDIS_HOST = os.getenv('REDIS_HOST', 'localstack')
    REDIS_PORT = os.getenv('REDIS_PORT', 4513)
    REDIS_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}'

    # Database
    AES_SECRET_KEY = os.getenv('AES_SECRET_KEY', 'fake-aes-key')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')

    # Celery
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL
    CELERY_CONFIG = {
        'beat_schedule': {
            'do_something': {
                'task': 'src.tasks.do_something',
                'args': (10,),
                'schedule': 5.0,
            },
        }
    }
