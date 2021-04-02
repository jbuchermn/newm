from __future__ import annotations
from typing import TypeVar, Optional, Callable, Any, Generic, Union, cast

import pathlib
import importlib
import logging
import sys
import os

_provider = {}
_consumer: dict[str, Any] = {}

logger = logging.getLogger(__name__)


T = TypeVar('T')
class _ConfiguredValue(Generic[T]):
    def __init__(self, name: str, value: T, default: Optional[T]):
        self._name = name
        self._value: Optional[T] = None
        self._default = default

        self.update(value)

    def update(self, value: T) -> None:
        self._value = value if value is not None else self._default

    def __call__(self) -> Optional[T]:
        return self._value

    def __str__(self) -> str:
        return "%-60s %-40s %s" % (self._name, self._value, ("(default: %s)" % self._default) if self._default != self._value else "")

def _update_config(at_c: Union[_ConfiguredValue[T], dict[str, Any]], at_p: Union[Any, dict[str, Any]]) -> None:
    if isinstance(at_c, _ConfiguredValue):
        at_c.update(cast(T, at_p))
    else:
        if isinstance(at_c, dict):
            for k in at_c.keys():
                _update_config(at_c[k], at_p[k] if (at_p is not None and k in at_p) else None)
        else:
            logger.warn("Config: Unexpected")

def print_config(at_c: Optional[dict[str, Any]]=None) -> str:
    if at_c is None:
        at_c = _consumer

    if isinstance(at_c, _ConfiguredValue):
        return str(at_c)
    else:
        if isinstance(at_c, dict):
            return "\n".join([print_config(at_c[k]) for k in at_c.keys()])
        else:
            logger.warn("Config: Unexpected")
            return ""

def load_config(fallback: bool=True) -> None:
    global _provider

    home = os.environ['HOME'] if 'HOME' in os.environ else '/'
    path = pathlib.Path(home) / '.config' / 'newm' / 'config.py'
    path_default = pathlib.Path(__file__).parent.absolute() / 'default_config.py'

    if not path.is_file():
        path = pathlib.Path('/etc') / 'newm' / 'config.py'

    if not path.is_file():
        path = path_default

    logger.info("Loading config at %s", path)

    def load(path: pathlib.Path) -> dict[str, Any]:
        module = path.stem

        try:
            del sys.modules[module]
        except KeyError:
            pass

        sys.path.insert(0, str(path.parent))
        return importlib.import_module(module).__dict__

    try:
        _provider = load(path)
    except:
        if fallback:
            logger.exception("Error loading config - falling back to default")
            try:
                _provider = load(path_default)
            except:
                logger.exception("Error loading default config")
                _provider = {}
        else:
            logger.exception("Error loading config")

    _update_config(_consumer, _provider)



def configured_value(path: str, default: Optional[T]=None) -> Callable[[], T]:
    global _consumer

    result = None
    try:
        v = _provider
        for k in path.split("."):
            v = v[k]

        result = v
    except KeyError:
        pass

    c = _consumer
    for k in path.split(".")[:-1]:
        try:
            c = c[k]
        except KeyError:
            c[k] = {}
            c = c[k]

    k = path.split(".")[-1]
    if k in c and isinstance(c[k], _ConfiguredValue):
        return c[k]

    res = _ConfiguredValue(path, result, default)
    c[k] = res
    return cast(Callable[[], T], res)



if __name__ == '__main__':
    scale = configured_value('output_scale', 1.0)
    pywm = configured_value('pywm', cast(dict[str, Any], {}))

    while True:
        print("Scale is %f" % scale())
        print("PyWM is %s" % pywm())
        input("Update? ")
        load_config()
