"""
Django settings for portfoliomgr project.

Generated by 'django-admin startproject' using Django 2.0.7.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.0/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#print(f'BASE_DIR {BASE_DIR}')

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'uuoc10!bp#0bkgq2oyh3s@sd^8%^k3(q8poba@onqv)@9zy(*4'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = eval(str(os.environ['DJANGO_ENABLE_DEBUG']).capitalize())
ALLOWED_HOSTS = ['*', '127.0.0.1', 'localhost'] if DEBUG==False else ['*']

# Database declarations
DB_ENGINE = str(os.environ['DB_ENGINE'])
DB_HOST = str(os.environ['DB_HOST'])
DB_NAME = str(os.environ['DB_NAME'])
DB_USER = str(os.environ['DB_USER'])
DB_PASSWORD = str(os.environ['DB_PASSWORD'])
DB_PORT = int(os.environ['DB_PORT'])

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'channels',
    'rest_framework',
    'huey.contrib.djhuey',
    'solo',
    # own
    'ppf',
    'ssy',
    'epf',
    'espp',
    'rsu',
    'goal',
    'users',
    'shares',
    'mutualfunds',
    'fixed_deposit',
    'reports',
    'common',
    'calculator',
    'tasks',
    'alerts',
    'pages',
    'markets',
    'retirement_401k',
    'tax',
    'insurance',
    'gold',
    'bankaccounts',
    "crypto",
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'portfoliomgr.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'libraries':{
                'template_filters': 'portfoliomgr.template_filters',

            }
        },
    },
]

WSGI_APPLICATION = 'portfoliomgr.wsgi.application'
ASGI_APPLICATION = "portfoliomgr.routing.application"

# Database
# See Database declarations above
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': f'django.db.backends.{DB_ENGINE}',
        'NAME': DB_NAME,
	'USER': DB_USER,
	'PASSWORD': DB_PASSWORD,
	'HOST': DB_HOST,
	'PORT': DB_PORT,
    }
}


# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/2.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]

STATIC_URL = '/static/'

STATIC_ROOT = os.path.join(BASE_DIR, 'collected_files')

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

MEDIA_URL = '/media/'

HUEY = {
    'huey_class': 'huey.SqliteHuey',
    'name': DATABASES['default']['NAME'],
    'results': True,  # Store return values of tasks.
    'store_none': False,  # If a task returns None, do not save to results.
    'immediate': False,
    'consumer': {
        'workers': 1,
        'worker_type': 'thread',
        'initial_delay': 0.1,  # Smallest polling interval, same as -d.
        'backoff': 1.15,  # Exponential backoff using this rate, -b.
        'max_delay': 10.0,  # Max possible polling interval, -m.
        'scheduler_interval': 1,  # Check schedule every second, -s.
        'periodic': True,  # Enable crontab feature.
        'check_worker_health': True,  # Enable worker health checks.
        'health_check_interval': 1,  # Check worker health every second.
    },
}
# Channels
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}

'''
LOGGING = {
    'version': 1,
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
        }
    },
    'loggers': {
        'django.db.backends': {
            'level': 'DEBUG',
            'handlers': ['console'],
        }
    }
}
'''

#EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
#EMAIL_HOST = 'smtp.gmail.com'
#EMAIL_USE_TLS = True
#EMAIL_PORT = 587
#EMAIL_HOST_USER = 'your_account@gmail.com'
#EMAIL_HOST_PASSWORD = 'your accounts password'
