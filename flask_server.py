from functools import wraps, update_wrapper
from datetime import datetime
import logging as log
import os
import sys
if not sys.platform.startswith('win'):
    from pwd import getpwnam

import flask
from flask import request
from flask_social import Social, SQLAlchemyConnectionDatastore, \
     login_failed
from flask_social.utils import get_connection_values_from_oauth_response
from flask_social.views import connect_handler
from flask_sqlalchemy import SQLAlchemy
from flask_security import SQLAlchemyUserDatastore, UserMixin, \
     RoleMixin, Security, login_required, current_user, \
     login_user, logout_user


import ion_provider
import ion_secret

app = flask.Flask(__name__)
app.gm = None
app.args = None

app.config['SOCIAL_ION'] = {
    'id': 'ion',
    'module': 'ion_provider',
    'consumer_key': ion_secret.ION_OAUTH_KEY,
    'consumer_secret': ion_secret.ION_OAUTH_SECRET
}
app.config['SOCIAL_REDIRECT_URI_OVERRIDE'] = 'https://activities.tjhsst.edu/othello/login/ion'

app.config['DEBUG'] = True
app.config['SECRET_KEY'] = ion_secret.FLASK_SECRET
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'

db = SQLAlchemy(app)

roles_users = db.Table('roles_users',
        db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
        db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))

class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    name = db.Column(db.String(255))
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))
    

class Connection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    provider_id = db.Column(db.String(255))
    provider_user_id = db.Column(db.String(255))
    access_token = db.Column(db.String(255))
    secret = db.Column(db.String(255))
    display_name = db.Column(db.String(255))
    profile_url = db.Column(db.String(512))
    image_url = db.Column(db.String(512))
    rank = db.Column(db.Integer)

security = Security(app, SQLAlchemyUserDatastore(db, User, Role))
social = Social(app, SQLAlchemyConnectionDatastore(db, Connection))

@app.route('/')
def index():
    return flask.render_template('index.html')

@app.route('/index')
def index2():
    return flask.render_template('index.html')

@app.route('/about')
def about():
    return flask.render_template('about.html')

@app.route('/play')
def play():
    return flask.render_template('othello.html')
    
@app.route('/watch')
def watch():
    return flask.render_template('watch.html')

def nocache(view):
    @wraps(view)
    def no_cache(*args, **kwargs):
        response = flask.make_response(view(*args, **kwargs))
        response.headers['Last-Modified'] = datetime.now()
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
        return response
        
    return update_wrapper(no_cache, view)
    
@app.route('/list/ais')
@nocache
def ailist():
    pn = sorted(app.gm.possible_names)
    log.debug(pn)
    return "\n".join(pn)
    
@app.route('/list/games')
@nocache
def gamelist():
    log.debug(app.gm.games.items())
    return "\n".join(','.join(map(str,(sid, game.BLACK, game.WHITE, game.timelimit))) for sid, game in app.gm.games.items() if game.playing)

@app.route('/ion-login')
def login():
    if current_user.is_authenticated:
        return flask.redirect(flask.url_for('upload'))
    return flask.render_template('login.html')

# Apparently the name of the method???
security.login_manager.login_view = 'login'

@login_failed.connect_via(app)
def on_login_failed(sender, provider, oauth_response):
    app.logger.debug('Social Login did a thing via %s; '
                     '&oauth_response=%s' % (provider.name, oauth_response))

    # I know the above stuff says failed but they did manage to log in with their ion account
    # The user here gets assigned a password of the oauth access token, making flask_security happy
    # This way there is no way to log in w/o using ion, which is the intention
    ds = security.datastore
    user_info = ion_provider.get_api(oauth_response)
    user = ds.find_user(email=user_info['tj_email'])
    if user:
        user.password = oauth_response['access_token']
    else:
        user = ds.create_user(email=user_info['tj_email'], \
                              password=oauth_response['access_token'], \
                              name=user_info['ion_username'])

    ds.commit()
    login_user(user)
    log.debug("{} logged in".format(user.name))
    return flask.redirect(flask.url_for('upload'))

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        name = current_user.name
        
        fdir = os.path.join(app.args.base_folder, 'private/Students', name)
        os.makedirs(fdir, mode=0o750, exist_ok=True)
        if 'code' not in request.files:
            flask.flash('You submitted without code')
            return flask.redirect(request.url)
        
        f = request.files['code']
        if f.filename == '':
            flask.flash('You did not select a file')
            return flask.redirect(request.url)
            
        fname = os.path.join(fdir, 'strategy.py')
        f.save(fname)
        if not sys.platform.startswith('win'):
            # Make the files owned by the user so only they can edit them
            #os.chown(fdir,)
            #os.chown(fname,)
            #os.chmod(fdir,0o750)
            #os.chmod(fname,0o750)
            pass
        app.gm.write_ai()
        return flask.render_template('upload_complete.html')
    else:
        return flask.render_template('upload.html')

@app.route('/logout')
@login_required
def logout():
    logout_user(current_user)
    return flask.redirect(flask.url_for('/'))

@app.before_first_request
def create_db():
    db.create_all()
    db.session.commit()