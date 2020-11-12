import os
import sqlite3
import click
import functools
from flask.cli import with_appcontext
from flask import(
     Flask, render_template, request,
     abort, redirect, url_for,

     session, flash, g, current_app,

)
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config.from_mapping(
    SECRET_KEY = 'dev'
)

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            os.path.join(app.instance_path, 'schema.sql'),
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()


def init_db():
    db = get_db()

    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))


@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables"""
    init_db()
    click.echo('Initialized the database.')


app.teardown_appcontext(close_db)
app.cli.add_command(init_db_command)


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if session.get('id') is None:
            return redirect(url_for('index'))
        return view(**kwargs)
    return wrapped_view



@app.route('/')
def index():
     return render_template('index.html')

@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        db_connect = get_db()
        error=None

        if not username:
            error = 'Vous devez inscrire un nom d\'utilisateur !'
        elif not password:
            error = 'Vous devez définir un mot de passe pour cet utilisateur !'
        elif not email:
            error = 'Vous devez renseigner un email pour cet utilisateur !'    
        elif db_connect.execute(
            'SELECT id_user FROM user WHERE username = ?', (username,)
            ).fetchone() is not None:
            error = 'Ce nom d\'utilisateur est déjà utilisé !'
        elif db_connect.execute(
                'SELECT id_user FROM user WHERE mail = ?', (email,)
            ).fetchone() is not None:
                error = 'l\'adresse mail est déjà utilisée!'
        if error is None:
            db_connect.execute(
                'INSERT INTO user(username, password, mail) VALUES (?, ?, ?)',
                (username,generate_password_hash(password), email)
            )
            db_connect.commit()
            flash('Le compte est désormais inscrit, vous pouvez vous connecter')
            #The user is redirected to the index page
            return redirect(url_for('index'))
        
        flash(error)

    return render_template('register.html')



@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db_user = get_db()
        error = None
        checkUser = db_user.execute(
            'SELECT * FROM user WHERE username = ?',
            (username,)
        ).fetchone()
        if checkUser is None:
            error = 'Erreur : le nom d\'utilisateur renseigné n\'existe pas !'
        elif not check_password_hash(checkUser['password'], password):
            error = 'Erreur : Le mot de passe renseigné est incorrect pour cet utilisateur'
        if error is None:
            session.clear()
            session['username'] = checkUser['username']
            session['id_user'] = checkUser['id_user']
            return redirect(url_for('index'))

        flash(error)
    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))
