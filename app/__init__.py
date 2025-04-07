import logging
from logging.handlers import RotatingFileHandler, SMTPHandler
import os
from flask import Flask, request,redirect  
from app.config import Config,AWSConfig
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_babel import Babel
from flask_s3 import FlaskS3



app = Flask(__name__)
app.config['FLASKS3_BUCKET_NAME'] = 'mytvbprojectbucket-oj'
s3 = FlaskS3(app)
app.config.from_object(AWSConfig)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager()
login.login_view = "login"
login.init_app(app)
mail = Mail(app)
bootstrap = Bootstrap(app)
moment = Moment(app)
babel = Babel(app)
# from datetime import datetime



@app.route('/asset/<path:filename>')
def serve_asset(filename):
    return redirect(s3.url_for(filename))

if not app.debug:
    root = logging.getLogger()
    if app.config["MAIL_SERVER"]:
        auth = None
        if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
            auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        secure = None
        if app.config['MAIL_USE_TLS']:
            secure = ()
        mail_handler = SMTPHandler(
            mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
            fromaddr='no-reply@' + app.config['MAIL_SERVER'],
            toaddrs=app.config['ADMINS'], subject='Microblog Failure',
            credentials=auth, secure=secure)
        mail_handler.setLevel(logging.ERROR)
        root.addHandler(mail_handler)

    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/microblog.log', maxBytes=10240,
                                       backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    file_handler.setLevel(logging.INFO)
    root.addHandler(file_handler)
    root.setLevel(logging.INFO)
    root.info('Microblog startup')



# @app.template_filter('time_ago')
# def time_ago_filter(dt):
#     now = datetime.utcnow()
#     diff = now - dt
    
#     if diff.days > 365:
#         return f"{diff.days // 365}年前"
#     if diff.days > 30:
#         return f"{diff.days // 30}个月前"
#     if diff.days > 0:
#         return f"{diff.days}天前"
#     if diff.seconds > 3600:
#         return f"{diff.seconds // 3600}小时前"
#     if diff.seconds > 60:
#         return f"{diff.seconds // 60}分钟前"
#     return "刚刚"

# @babel.localeselector
# def get_locale():
#     return request.accept_languages.best_match(app.config['LANGUAGES'])


# You must keep the routes at the end.
from app import routes, errors