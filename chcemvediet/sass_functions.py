# vim: expandtab
# -*- coding: utf-8 -*-

def static(path):
    # Copied from ``django_libsass.static`` as there is no way to reference their method in
    # LIBSASS_CUSTOM_FUNCTIONS in settings.py. The setting does not accept function paths. It
    # expects reference to the real function, but ``django_libsass`` module may not be imported in
    # ``settings.py``, because it requires settings already configured.
    from django.templatetags.static import static as django_static
    return django_static(path)

def md5(path):
    import hashlib
    from django.contrib.staticfiles.finders import find
    with open(find(path), 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()
