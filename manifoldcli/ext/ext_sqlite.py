import os
from cement.utils import fs
from cement import minimal_logger
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, aliased
from sqlalchemy.ext.declarative import declarative_base
from ..models.database import *

LOG = minimal_logger(__name__)

def db_extension(app):
    app.log.debug('extending application with sqlite')
    db_file = app.config.get('manifoldcli', 'db_file')
    
    # ensure that we expand the full path
    db_file = fs.abspath(db_file)
    app.log.debug('sqlite database file is: %s' % db_file)
    
    # ensure our parent directory exists
    db_dir = os.path.dirname(db_file)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)

    engine = create_engine("sqlite:///" + db_file)
    DBBase.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    app.extend('session', Session(bind=engine))

# def load(app):
#     app.handler.register(db_extension)