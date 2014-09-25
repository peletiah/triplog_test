from pyramid.config import Configurator
from sqlalchemy import engine_from_config

from .models.db_model import (
    DBSession,
    Base,
    )

from pyramid.session import UnencryptedCookieSessionFactoryConfig #TODO update to pyramid 1.5

from pyramid.config import Configurator


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    
    map_session_factory = UnencryptedCookieSessionFactoryConfig('LanjenyocUcFish3')

    config = Configurator(settings=settings, session_factory = map_session_factory)
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('home', '/')
    config.add_route('track', '/track')
    config.add_route('track_json', '/track_json')
    config.add_route('set_mode', '/set_mode')
    config.add_route('add_track', '/add_track')
    config.add_route('track_extent:trackid', '/track_extent/{trackid}')
    config.add_route('track_extent', '/track_extent')
    config.add_route('features_in_extent', '/features_in_extent')
    config.add_route('reduce_trackpoints', '/reduce_trackpoints')
    config.scan()
    return config.make_wsgi_app()
