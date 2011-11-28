from pyramid.config import Configurator
from sqlalchemy import engine_from_config

from genwebmanager.models import initialize_sql

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    initialize_sql(engine)
    config = Configurator(settings=settings)
    config.add_static_view('static', 'genwebmanager:static')
    config.add_route('home', '/')
    config.add_view('genwebmanager.views.main',
                    route_name='home',
                    renderer='templates/main.pt')
    config.add_route('purge', '/purge')
    config.add_view('genwebmanager.views.purge',
                    route_name='purge',
                    renderer='templates/ajax.pt')
    config.add_route('export','/export')
    config.add_view('genwebmanager.views.export',
                    route_name='export')
                    
    return config.make_wsgi_app()

