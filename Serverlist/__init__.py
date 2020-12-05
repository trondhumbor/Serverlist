import os
from datetime import datetime

from flask import Flask
from flask_apscheduler import APScheduler
from flask_caching import Cache

cache = Cache()
scheduler = APScheduler()

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev",
        MASTER_SERVER=("master.xlabs.dev", 20810),
        MASTER_QUERY="getservers IW6 1 full empty",
        #MASTER_SERVER=("cod4master.activision.com", 20810),
        #MASTER_QUERY="getservers IW3 full empty",
        SERVER_INFO="getinfo {challenge}",
        SCHEDULER_API_ENABLED=True,
        JOBS=[
            {
                "id": "job1", "func": "Serverlist.task:reloadServers",
                "args": (), "trigger": "interval", "seconds": 60*3
            }
        ],
        CACHE_TYPE="simple", # Flask-Caching related configs
        CACHE_DEFAULT_TIMEOUT=0 # We manage the cache ourselves.
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)

    cache.init_app(app)
    scheduler.init_app(app)
    scheduler.start()

    for job in scheduler.get_jobs():
        job.modify(next_run_time=datetime.now())

    with app.app_context():
        from . import routes

    return app
