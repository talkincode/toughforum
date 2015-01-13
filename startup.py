#!/usr/bin/env python3

from mako.lookup import TemplateLookup
import os
import db_models
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker 


def init(app,**config):
    if config['debug']:
        sqlite_file = config["sqlite_file"]
        db_models.engine = create_engine('sqlite:///' + sqlite_file)
        if sqlite_file == ":memory:":
            db_models.rebuild_db()
            db_models.init_db()
        else:
            db_models.build_db()
            db_models.init_db()
    else:
        db_models.engine = create_engine(
            config['db_url'],
            echo=config['db_echo'],
            pool_size=config['db_pool'],
            max_overflow=5
        )

    app.g.db = scoped_session(sessionmaker(
        bind=db_models.engine,
        autocommit=False,
        autoflush=False
    ))

    app.g.tp_lookup = TemplateLookup(
        directories=[os.path.join(config['app_dir'], config['templates'])],
        default_filters=['decode.utf8'],
        input_encoding='utf-8',
        output_encoding='utf-8',
        encoding_errors='replace',
        module_directory=os.path.join(config['app_dir'], 'tmp')
    )