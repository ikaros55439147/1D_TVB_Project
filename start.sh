#!/bin/bash
pip install psycopg2
pip install flask-mail
pip install PyJWT==2.3.0
pip install aiosmtpd
pip install flask
pip install flask-wtf
pip install flask-migrate
pip install flask-sqlalchemy
pip install flask-babel==2.0.0
pip install -U djlint
pip freeze > requirements.txt
flask db migrate -m "following"
flask db upgrade
flask --debug run --host=0.0.0.0