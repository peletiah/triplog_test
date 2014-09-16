from pyramid.config import Configurator
from sqlalchemy import engine_from_config

from .models import (
    DBSession,
    Base,
    )


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    config = Configurator(settings=settings)
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('home', '/')
    config.add_route('track', '/track')
    config.add_route('track_json', '/track_json')
    config.add_route('set_mode', '/set_mode')
    config.add_route('add_track', '/add_track')
    config.add_route('track_extent:trackid', '/track_extent/{trackid}')
    config.add_route('track_extent', '/track_extent')
    config.scan()
    return config.make_wsgi_app()
