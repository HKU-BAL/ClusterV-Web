from flask import Flask
from flask_bootstrap import Bootstrap
from app.config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from redis import Redis
import rq


app = Flask(__name__, static_url_path='/static', static_folder='static')

bootstrap = Bootstrap(app)
app.config.from_object(Config)

app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 400

db = SQLAlchemy(app, session_options={'expire_on_commit': False})

migrate = Migrate(app, db)

app.redis = Redis(app.config['REDIS_IP'], app.config['REDIS_PORT'])
app.task_queue = rq.Queue('clusterv-tasks', connection=app.redis, default_timeout=60 * 60 * 12)



from app import routes, models

# def create_app(config_class=Config):
#     app.redis = Redis(app.config['REDIS_IP'], app.config['REDIS_PORT'])
#     app.task_queue = rq.Queue('clusterv-tasks', connection=app.redis)