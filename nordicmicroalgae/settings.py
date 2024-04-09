"""
Django settings for nordicmicroalgae project.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""

import os
import yaml

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.environ.get(
    'NORDICMICROALGAE_DATA_DIR',
    os.path.join(os.path.dirname(BASE_DIR), 'shared')
)

CONTENT_DIR = os.path.join(DATA_DIR, 'content')

MEDIA_ROOT = os.path.join(DATA_DIR, 'media')

STATIC_ROOT = os.environ.get(
    'DJANGO_STATIC_ROOT',
    os.path.join(os.path.dirname(BASE_DIR), 'static')
)

# Load environment specific configuration from file in DATA_DIR
try:
    with open(
        os.path.join(DATA_DIR, 'config', 'environment.yaml'),
        encoding='utf8'
    ) as fid:
        config = yaml.safe_load(fid)
except OSError:
    config = {}


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    config.get('secret_key')
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get(
    'DJANGO_DEBUG',
    str(config.get('debug', 'no'))
).lower() in ['yes', 'on', 'true']

ALLOWED_HOSTS = os.environ.get(
    'DJANGO_ALLOWED_HOSTS',
    str(config.get('allowed_hosts', '.nordicmicroalgae.org'))
).split(' ')


# Application definition

INSTALLED_APPS = [
    'nordicmicroalgae.apps.NordicMicroalgaeAdminConfig',
    'taxa',
    'facts',
    'media',
    'contributors',
    'synchronization',
    'openapi',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'nordicmicroalgae.middleware.CorsMiddleware',
]

ROOT_URLCONF = 'nordicmicroalgae.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'nordicmicroalgae', 'templates'),
        ],
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

WSGI_APPLICATION = 'nordicmicroalgae.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get(
            'DJANGO_DATABASE_NAME',
            config.get('database_name')
        ),
        'USER': os.environ.get(
            'DJANGO_DATABASE_USER',
            config.get('database_user')
        ),
        'PASSWORD': os.environ.get(
            'DJANGO_DATABASE_PASSWORD',
            config.get('database_password')
        ),
        'HOST': os.environ.get(
            'DJANGO_DATABASE_HOST',
            config.get('database_host', '127.0.0.1')
        ),
        'PORT': os.environ.get(
            'DJANGO_DATABASE_PORT',
            config.get('database_port', '5432')
        ),
    }
}


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

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'nordicmicroalgae', 'static'),
]

MEDIA_URL = os.environ.get(
    'DJANGO_MEDIA_URL',
    config.get('media_url', '/media/')
)


# Authentication
LOGIN_URL = '/admin/login/'

LOGOUT_REDIRECT_URL = '/'


# E-mail
DEFAULT_FROM_EMAIL = os.environ.get(
    'DJANGO_DEFAULT_FROM_EMAIL',
    config.get('default_from_email', 'webmaster@localhost')
)

EMAIL_HOST = os.environ.get(
    'DJANGO_EMAIL_HOST',
    config.get('email_host', 'localhost')
)

EMAIL_PORT = os.environ.get(
    'DJANGO_EMAIL_PORT',
    config.get('email_port', '25')
)

EMAIL_HOST_USER = os.environ.get(
    'DJANGO_EMAIL_HOST_USER',
    config.get('email_host_user', '')
)

EMAIL_HOST_PASSWORD = os.environ.get(
    'DJANGO_EMAIL_HOST_PASSWORD',
    config.get('email_host_password', '')
)

EMAIL_USE_TLS = os.environ.get(
    'DJANGO_EMAIL_USE_TLS',
    str(config.get('email_use_tls', 'no'))
).lower() in ['yes', 'on', 'true']

EMAIL_USE_SSL = os.environ.get(
    'DJANGO_EMAIL_USE_SSL',
    str(config.get('email_use_ssl', 'no'))
).lower() in ['yes', 'on', 'true']
