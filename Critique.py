import os
import sqlite3
import click
from flask.cli import with_appcontext
from flask import(
     Flask, render_template, request,
     abort, redirect, url_for,
     session, flash, g, current_app,
)
from markupsafe import escape
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config.from_mapping(
    SECRET_KEY = 'dev'
)

@app.route('/')
def index():
    return render_template('index.html')


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


# It's the route for our main page, the user have to connect
# with his logs to get farther
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
    return render_template('index.html')
