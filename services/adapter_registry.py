"""Shim adapter registry for integration adapter tests."""

from __future__ import annotations


class _Registry:
    def __init__(self):
        self.adapters = {}

    def register_adapter(self, name, adapter_cls):
        self.adapters[name] = adapter_cls

    def get_adapter(self, name):
        return self.adapters.get(name)


_registry = _Registry()


def get_adapter_registry() -> _Registry:
    return _registry

