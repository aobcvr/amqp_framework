import os
import uuid
from dynaconf import Dynaconf, Validator
from pathlib import Path

from amqp_framework.exc import ImproperlyConfigured
from amqp_framework.utils.functional import LazyObject, empty

BASE_DIR = Path(__file__).parent.parent

ENVIRONMENT_VARIABLE = 'AMQP_FRAMEWORK_SETTINGS_FILE'

VALIDATORS = [
    Validator(
        'service_name',
        'workers',
        'broker_url',
        required=True,
    ),
    Validator(
        'connection_options.heartbeat_interval',
        default=10,
    ),
    Validator(
        'connection_options.timeout',
        default=15,
    ),
    Validator(
        'service_hash_key',
        default=uuid.uuid4().hex[0:7],
    ),
    Validator(
        'connection_options.client_properties.connection_name',
        default='@format {this.service_name}_{this.service_hash_key}',
    ),
    Validator(
        'debug',
        default=False,
    ),
]


class LazySettings(LazyObject):
    """
    A lazy proxy for settings module.
    """

    def _setup(self, name=None):
        if settings_file := os.environ.get(ENVIRONMENT_VARIABLE):
            self.configure(settings_files=[settings_file])
        else:
            desc = ("setting %s" % name) if name else "settings"
            raise ImproperlyConfigured(
                "Requested %s, but settings are not configured. "
                "You must either define the environment variable %s "
                "or call settings.configure() before accessing settings."
                % (desc, ENVIRONMENT_VARIABLE))

    def __repr__(self):
        # Hardcode the class name as otherwise it yields 'Settings'.
        if self._wrapped is empty:
            return '<LazySettings [Unevaluated]>'
        return '<LazySettings "%(settings_module)s">' % {
            'settings_module': self._wrapped,
        }

    def __getattr__(self, name):
        """Return the value of a setting and cache it in self.__dict__."""
        if self._wrapped is empty:
            self._setup(name)
        val = getattr(self._wrapped, name)
        self.__dict__[name] = val
        return val

    def __setattr__(self, name, value):
        """
        Set the value of setting. Clear all cached values if _wrapped changes
        (@override_settings does this) or clear single values when set.
        """
        if name == '_wrapped':
            self.__dict__.clear()
        else:
            self.__dict__.pop(name, None)
        super().__setattr__(name, value)

    def __delattr__(self, name):
        """Delete a setting and clear it from cache if needed."""
        super().__delattr__(name)
        self.__dict__.pop(name, None)

    def configure(self, **options):
        """Called to manually configure the settings."""
        if self._wrapped is not empty:
            raise RuntimeError('Settings already configured.')

        self._wrapped = Dynaconf(
            validators=VALIDATORS,
            **options,
        )

    def configured(self):
        """Return True if the settings have already been configured."""
        return self._wrapped is not empty


settings = LazySettings()
