from injector import Injector
from nesis.rag.core.settings.settings import Settings


def create_application_injector(settings: Settings = None) -> Injector:

    _injector = Injector(auto_bind=True)
    _injector.binder.bind(Settings, to=settings)
    return _injector


"""
Global injector for the application.

Avoid using this reference, it will make your code harder to test.

Instead, use the `request.state.injector` reference, which is bound to every request
"""
# global_injector: Injector = _create_application_injector()
