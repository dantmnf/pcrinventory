import logging
import contextlib
from collections.abc import Mapping
from typing import Sequence
from . import schema, schemadef
logger = logging.getLogger(__name__)

_migrate_actions = {}

def migrate_from(version):
    def decorator(f):
        _migrate_actions[version] = f
        return f
    return decorator

def migrate(ydoc: Mapping):
    old_version = ydoc.get('__version__', None)
    while old_version != schema.root.__version__:
        action = _migrate_actions.get(old_version, None)
        if action is None:
            raise ValueError(f'No migration from version {old_version}')
        ydoc = action(ydoc)
        old_version = ydoc.get('__version__', None)
    return ydoc

@migrate_from(None)
def migrate_from_legacy(ydoc: Mapping):
    logger.info('Migrating from legacy config schema')
    return ydoc
