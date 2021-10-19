"""Import related utilities."""

import importlib
import os
import sys
from contextlib import contextmanager


@contextmanager
def cwd_in_path():
    """Context adding the current working directory to sys.path."""
    cwd = os.getcwd()
    if cwd in sys.path:
        yield
    else:
        sys.path.insert(0, cwd)
        try:
            yield cwd
        finally:
            try:
                sys.path.remove(cwd)
            except ValueError:  # pragma: no cover
                pass


def import_from_cwd(module, imp=None, package=None):
    """Import module, temporarily including modules in the current directory.
    Modules located in the current directory has
    precedence over modules located in `sys.path`.
    """
    if imp is None:
        imp = importlib.import_module
    with cwd_in_path():
        return imp(module, package=package)


def symbol_by_name(name, aliases=None, imp=None, package=None,
                   sep='.', default=None, **kwargs):
    """Get symbol by qualified name.
    The name should be the full dot-separated path to the class::
        modulename.ClassName
    Example::
        amqp_framework.loaders.default.Loader
                                       ^- class name
    or using ':' to separate module and symbol::
        amqp_framework.loaders.default:Loader
    If `aliases` is provided, a dict containing short name/long name
    mappings, the name is looked up in the aliases first.
    """
    aliases = {} if not aliases else aliases
    if imp is None:
        imp = importlib.import_module

    if not isinstance(name, str):
        return name  # already a class

    name = aliases.get(name) or name
    sep = ':' if ':' in name else sep
    module_name, _, cls_name = name.rpartition(sep)
    if not module_name:
        cls_name, module_name = None, package if package else cls_name
    try:
        module = imp(module_name, package=package, **kwargs)  # noqa
    except ValueError as exc:
        raise ValueError(f"Couldn't import {name!r}: {exc}")
    except (ImportError, AttributeError):
        if default is None:
            raise
        return default
    else:
        return getattr(module, cls_name) if cls_name else module
