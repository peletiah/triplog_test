#import re
#
#from pyramid.paster import bootstrap
#from pyramid.request import Request
#env = bootstrap('development.ini')
#
#from models.db_model import *
#from sqlalchemy import engine_from_config
#engine = engine_from_config(env['registry'].settings, 'sqlalchemy.')
#DBSession.configure(bind=engine)
#log=DBSession.query(Log).filter(Log.id == 2).one()
#
#import uuid
#log.uuid=str(uuidlib.uuid4())
#
#log.uuid
#
#m=re.search(r'\bwhere\b',log.content)
#
#log.content[m.start()-20:m.end()+20]

