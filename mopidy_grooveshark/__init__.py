from __future__ import unicode_literals

import os
import logging

from mopidy import ext
from mopidy import config


__version__ = '1.0.4'

logger = logging.getLogger(__name__)


class Extension(ext.Extension):

    dist_name = 'Mopidy-Grooveshark'
    ext_name = 'grooveshark'
    version = __version__

    def get_default_config(self):
        conf_file = os.path.join(os.path.dirname(__file__), 'ext.conf')
        return config.read(conf_file)

    def get_config_schema(self):
        schema = super(Extension, self).get_config_schema()
        return schema

    def setup(self, registry):
        from .backend import GroovesharkBackend
        registry.add('backend', GroovesharkBackend)
