import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'this-is-a-long-secret-key'

    # setting database, for saving session ID, and running files / results
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://'
    REDIS_IP = '127.0.0.1'
    REDIS_PORT = '6379'
    HOME_DIR="/home/clustervw"
    #HOME_DIR = "/autofs/bal31/jhsu/home/projects/HIV/web_repo_clean/"

    OUTPUT_PATH = "{}/web_upload/".format(HOME_DIR)
    BASE_STATIC = "{}/app/static".format(HOME_DIR)

    APP_DATA_PATH = "{}/app_data/".format(HOME_DIR)
    BASE_REF_PATH = "{}/HIV_1.fasta".format(APP_DATA_PATH)
    MAX_BAM_ALLOW = 200
    CV_PATH="{}/ClusterV/cv.py".format(HOME_DIR)
