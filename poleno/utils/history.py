# vim: expandtab
# -*- coding: utf-8 -*-
import simple_history

def register_history(model=None, **kwargs):
    u"""
    Wrapper for ``simple_history.register`` to work as a decorator.
    """
    def actual_decorator(model):
        simple_history.register(model, **kwargs)
        return model
    if model:
        return actual_decorator(model)
    return actual_decorator
