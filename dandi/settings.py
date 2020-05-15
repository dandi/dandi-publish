import os
from typing import Type

from configurations import Configuration, values


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
# TODO: BASE_DIR is not an actual Django setting, remove it
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# When "environ_name" is specified or "environ=False", a Value will immediately bind (and so
# cannot be tweaked effectively in "before_binding"), unless "late_binding=True"
values.Value.late_binding = True


class ComposedConfiguration(Configuration):
    """
    Abstract base for composed Configuration.

    This must always be specified as a base class after Config mixins.
    """

    @classmethod
    def pre_setup(cls):
        super().pre_setup()

        # For every class in the inheritance hierarchy
        # Reverse order allows more base classes to run first
        for base_cls in reversed(cls.__mro__):
            # If the class has "before_binding" as its own (non-inherited) method
            if 'before_binding' in base_cls.__dict__:
                base_cls.before_binding(cls)

    @classmethod
    def post_setup(cls):
        super().post_setup()

        for base_cls in reversed(cls.__mro__):
            if 'after_binding' in base_cls.__dict__:
                base_cls.after_binding(cls)


class Config:
    """Abstract mixin for composable Config sections."""

    @staticmethod
    def before_binding(configuration: Type[ComposedConfiguration]) -> None:
        """
        Run before values are fully bound with environment variables.

        `configuration` refers to the final Configuration class, so settings from
        other Configs in the final hierarchy may be referenced.
        """
        pass

    @staticmethod
    def after_binding(configuration: Type[ComposedConfiguration]) -> None:
        """
        Run after values are fully bound with environment variables.

        `configuration` refers to the final Configuration class, so settings from
        other Configs in the final hierarchy may be referenced.
        """
        pass


class DjangoConfig(Config):
    SECRET_KEY = values.SecretValue(environ_prefix='DANDI')
    ALLOWED_HOSTS = values.ListValue(environ_prefix='DANDI', environ_required=True)

    WSGI_APPLICATION = 'dandi.wsgi.application'
    ROOT_URLCONF = 'dandi.urls'

    INSTALLED_APPS = [
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'corsheaders',
        'publish',
    ]

    MIDDLEWARE = [
        'corsheaders.middleware.CorsMiddleware',
        'django.middleware.security.SecurityMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
    ]

    TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [],
            'APP_DIRS': True,
            'OPTIONS': {
                'context_processors': [
                    'django.template.context_processors.debug',
                    'django.template.context_processors.request',
                    'django.contrib.auth.context_processors.auth',
                    'django.contrib.messages.context_processors.messages',
                ],
            },
        },
    ]

    # Password validation
    # https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators
    AUTH_PASSWORD_VALIDATORS = [
        {
            'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        },
        {
            'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        },
        {
            'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
        },
        {
            'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
        },
    ]

    # Internationalization
    # https://docs.djangoproject.com/en/3.0/topics/i18n/
    LANGUAGE_CODE = 'en-us'
    USE_TZ = True # TODO: should either USE_TZ or TIME_ZONE be set?
    TIME_ZONE = 'UTC'
    USE_I18N = True # TODO: why?
    USE_L10N = True # TODO: why?


class LoggingConfig(Config):
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            # Based on https://stackoverflow.com/a/20983546
            # TODO: Do we like this format?
            'verbose': {
                'format': ('%(asctime)s [%(process)d] [%(levelname)s] ' +
                            'pathname=%(pathname)s lineno=%(lineno)s ' +
                            'funcname=%(funcName)s %(message)s'),
                'datefmt': '%Y-%m-%d %H:%M:%S',
            },
        },
        'handlers': {
            'console': {
                # Unlike the Django default "console" handler, this works during production,
                # has a level of DEBUG, and uses a different formatter
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'verbose',
            },
            'mail_admins': {
                # Disable Django's default "mail_admins" handler
                'class': 'logging.NullHandler',
            }
        },
    }


class StaticFileConfig(Config):
    """
    Static file serving config.

    This could be used directly, but typically is included implicitly by
    WhitenoiseStaticFileConfig.
    """
    STATIC_URL = '/static/'
    STATIC_ROOT = values.PathValue(os.path.join(BASE_DIR, 'staticfiles'), environ=False, check_exists=False) # TODO: How does this work in development if collectstatic isn't run?

    @staticmethod
    def before_binding(configuration: Type[ComposedConfiguration]):
        configuration.INSTALLED_APPS += ['django.contrib.staticfiles']

    @staticmethod
    def after_binding(configuration: Type[ComposedConfiguration]):
        os.makedirs(configuration.STATIC_ROOT, exist_ok=True)


class WhitenoiseStaticFileConfig(StaticFileConfig):
    @staticmethod
    def before_binding(configuration: Type[ComposedConfiguration]):
        # Insert immediately before staticfiles app
        staticfiles_index = configuration.INSTALLED_APPS.index('django.contrib.staticfiles')
        configuration.INSTALLED_APPS.insert(staticfiles_index, 'whitenoise.runserver_nostatic')

        # Insert immediately after SecurityMiddleware
        security_index = configuration.MIDDLEWARE.index('django.middleware.security.SecurityMiddleware')
        configuration.MIDDLEWARE.insert(security_index + 1, 'whitenoise.middleware.WhiteNoiseMiddleware')

    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


class RestFrameworkConfig(Config):
    @staticmethod
    def before_binding(configuration: Type[ComposedConfiguration]):
        configuration.INSTALLED_APPS += ['rest_framework', 'rest_framework.authtoken']

    REST_FRAMEWORK = {
        'DEFAULT_AUTHENTICATION_CLASSES': [
            'rest_framework.authentication.TokenAuthentication',
        ]
    }


class DatabaseConfig(Config):
    @staticmethod
    def before_binding(configuration: Type[ComposedConfiguration]):
        configuration.INSTALLED_APPS += ['django.contrib.postgres']

    # This cannot have a default value, since the password and database name are always
    # set by the service admin
    DATABASES = values.DatabaseURLValue(
        environ_prefix='DANDI', environ_name='DATABASE_URL', environ_required=True,
        # Additional kwargs to DatabaseURLValue are passed to dj-database-url
        engine='django.db.backends.postgresql',
        conn_max_age=600)


class CeleryConfig(Config):
    @staticmethod
    def before_binding(configuration: Type[ComposedConfiguration]):
        configuration.INSTALLED_APPS += ['django_celery_results'] # TODO: Do we want this, or just configure to not use results?

    CELERY_BROKER_URL = values.Value('amqp://localhost:5672/', environ_prefix='DANDI')
    CELERY_RESULT_BACKEND = None
    # Only acknowledge a task being done after the function finishes
    CELERY_TASK_ACKS_LATE = True
    # CloudAMQP-suggested settings
    # https://www.cloudamqp.com/docs/celery.html
    CELERY_BROKER_POOL_LIMIT = 1
    CELERY_BROKER_HEARTBEAT = None
    CELERY_BROKER_CONNECTION_TIMEOUT = 30
    CELERY_EVENT_QUEUE_EXPIRES = 60
    CELERY_WORKER_PREFETCH_MULTIPLIER = 1
    # TODO: concurrency could be increased for non-memory intensive tasks
    CELERY_WORKER_CONCURRENCY = 1


class StorageConfig(Config):
    """Abstract base for storage configs."""
    pass
    # For unity, subclasses should use "environ_name='STORAGE_BUCKET_NAME'" for
    # whatever particular setting is used to store the bucket name


class MinioStorageConfig(StorageConfig):
    DEFAULT_FILE_STORAGE = 'minio_storage.storage.MinioMediaStorage'
    MINIO_STORAGE_ENDPOINT = values.Value('localhost:9000', environ_prefix='DANDI')
    MINIO_STORAGE_USE_HTTPS = False
    MINIO_STORAGE_MEDIA_BUCKET_NAME = values.Value(
        environ_prefix='DANDI',
        environ_name='STORAGE_BUCKET_NAME',
        environ_required=True)
    MINIO_STORAGE_ACCESS_KEY = values.SecretValue(environ_prefix='DANDI')
    MINIO_STORAGE_SECRET_KEY = values.SecretValue(environ_prefix='DANDI')
    MINIO_STORAGE_MEDIA_USE_PRESIGNED = True
    # TODO: Boto config for minio?


class S3StorageConfig(StorageConfig):
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    # This exact environ_name is important, as direct use of Boto will also use it
    AWS_S3_REGION_NAME = values.Value(environ_prefix=None, environ_name='AWS_DEFAULT_REGION',
        environ_required=True) # TODO: this is also used by Boto directly
    AWS_STORAGE_BUCKET_NAME = values.Value(
        environ_prefix='DANDI',
        environ_name='STORAGE_BUCKET_NAME',
        environ_required=True)
    AWS_S3_MAX_MEMORY_SIZE = 5 * 1024 * 1024
    AWS_S3_FILE_OVERWRITE = False
    AWS_AUTO_CREATE_BUCKET = False
    AWS_QUERYSTRING_EXPIRE = 3600 * 6  # 6 hours
    AWS_DEFAULT_ACL = None


class EmailConfig(Config):
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    # TODO: Production


class DebugToolbarConfig(Config):
    @staticmethod
    def before_binding(configuration: Type[ComposedConfiguration]):
        configuration.INSTALLED_APPS += ['debug_toolbar']
        configuration.MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
        # TODO: 'django_extensions' ?


class DandiConfig(Config):
    # TODO: should this setting's internal name start with DANDI_
    DANDISETS_BUCKET_NAME = values.Value(environ_prefix='DANDI', environ_required=True)


class BaseConfiguration(DjangoConfig, LoggingConfig, WhitenoiseStaticFileConfig,
    RestFrameworkConfig, DatabaseConfig, CeleryConfig, EmailConfig, DandiConfig,
    ComposedConfiguration):
    # Does not include a StorageConfig, since that varies
    # significantly from development to production
    pass


class DevelopmentConfiguration(MinioStorageConfig, DebugToolbarConfig,
    BaseConfiguration):
    @staticmethod
    def before_binding(configuration: Type[ComposedConfiguration]):
        configuration.ALLOWED_HOSTS.environ_required = False
        configuration.ALLOWED_HOSTS.default = ['localhost', '127.0.0.1']

    DEBUG = True
    INTERNAL_IPS = ['127.0.0.1']
    SECRET_KEY = 'insecuresecret'
    CORS_ORIGIN_ALLOW_ALL = True


class ProductionConfiguration(S3StorageConfig, BaseConfiguration):
    CORS_ORIGIN_WHITELIST = ["https://gui.dandiarchive.org"]
    # TODO this should allow us to test publishes from branch previews
    # TODO this might be a bad idea
    CORS_ORIGIN_REGEX_WHITELIST = [r"^https://[0-9a-f]+--gui-dandiarchive-org\.netlify\.app$"]


class HerokuProductionConfiguration(ProductionConfiguration):
    @staticmethod
    def before_binding(configuration: Type[ComposedConfiguration]):
        # Use different env var names for services that Heroku auto-injects
        configuration.DATABASES.environ_prefix = None
        configuration.DATABASES._params['ssl_require'] = True

        configuration.CELERY_BROKER_URL.environ_name = 'CLOUDAMQP_URL'
        configuration.CELERY_BROKER_URL.environ_prefix = None
        configuration.CELERY_BROKER_URL.environ_required = True
