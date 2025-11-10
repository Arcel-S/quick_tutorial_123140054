from pyramid.config import Configurator

def main(global_config, **settings):
    """This function returns a Pyramid WSGI application."""
    with Configurator(settings=settings) as config:
        config.include('pyramid_debugtoolbar')
        config.add_static_view(name='static', path='tutorial:static')
        config.add_route('home', '/')
        # Register a view for the 'home' route. When running under pserve
        # the package's modules are not executed as a script, so the
        # view defined in app.py won't be automatically registered.
        # Import and register the view here so the root path ('/') works.
        try:
            from .app import hello_world
        except Exception:
            # If import fails, continue — config.scan() may still find views
            # in other modules. We avoid failing startup for import errors.
            hello_world = None
        if hello_world is not None:
            config.add_view(hello_world, route_name='home')
        config.scan()
        return config.make_wsgi_app()
