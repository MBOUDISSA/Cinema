import os
import sqlite3
import click
import functools
import datetime
from flask.cli import with_appcontext
from flask import (
    Flask, render_template, request,
    abort, redirect, url_for,

    session, flash, g, current_app,

)
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config.from_mapping(
    SECRET_KEY='dev'
)


def get_db():
    """Function to get the database"""
    if 'db' not in g:
        g.db = sqlite3.connect(
            os.path.join(app.instance_path, 'schema.sql'),
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(e=None):
    """Function to close the database"""
    db = g.pop('db', None)

    if db is not None:
        db.close()


def init_db():
    """Function to initialize the database"""
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
    """Check if the user is connected if not ask him to"""
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if session.get('id_user') is None:
            error = "Vous devez être connecté pour acceder à cette fonctionnalité"
            flash(error, 'danger')
            return redirect(url_for('index'))
        return view(**kwargs)

    return wrapped_view


@app.route('/')
def index():
    return render_template('index.html', films='')


@app.route('/register', methods=['POST', 'GET'])
def register():
    """Add a new user to the database and check if he's not already register"""
    db_connect = get_db()
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
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
                (username, generate_password_hash(password), email)
            )
            db_connect.commit()
            success = 'Le nouvel utilisateur a été créé vous pouvez vous connecter'
            flash(success, 'success')
            return redirect(url_for('index'))

        flash(error, 'danger')

    return render_template('register.html')


@app.route('/login', methods=['POST', 'GET'])
def login():
    """Check if the user and password entered in the form is in the database"""
    db_user = get_db()
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
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
            success = "Bonjour " + session['username'] + " !"
            flash(success, 'success')
            return redirect(url_for('index'))

        flash(error, 'danger')

    return redirect(url_for('index'))


@app.route('/logout')
def logout():
    """Reset the session"""
    session.clear()
    return redirect(url_for('index'))


@app.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    """Add a movie in the table film in the database. Also check if all the field are entered"""
    db_connect = get_db()
    error = None

    if request.method == 'POST':
        film_title = request.form['film_title']
        film_author = request.form['film_author']
        film_date = request.form['film_date']
        film_synopsis = request.form['film_synopsis']

        if not film_title:
            error = 'Veuillez saisir le titre !'
        elif not film_author:
            error = 'Veuillez saisir le réalisateur !'
        elif not film_date:
            error = 'Veuillez saisir la date de sortie !'
        elif not film_synopsis:
            error = 'Veuillez saisir le synopsis !'

        if error is None:
            db_connect.execute(
                'INSERT INTO film (author_id,created,title,realisateur,date_sortie,synopsis) VALUES (?, ?, ?, ?, ?, ?)',
                (session['username'], datetime.datetime.now(), film_title, film_author, film_date, film_synopsis)
            )
            db_connect.commit()
            success = "Le film " + film_title + " a bien été enregistré !"
            flash(success, 'success')
            return redirect(url_for('index'))

        flash(error, 'danger')

    return render_template('add.html')


@app.route('/show_research', methods=['POST', 'GET'])
def show_research():
    """Show all movies containing the characters entered by the user"""
    db_film = get_db()
    error = None
    if request.method == 'POST':
        film_title = request.form['film_title']
        if not film_title:
            error = 'Veuillez renseigner un titre dans la barre de recherche'
            flash(error, 'danger')
        if error is None:
            search_data = db_film.execute(
                'SELECT * FROM film WHERE title like ?',
                ('%' + film_title + '%',)
            ).fetchall()
        return render_template('index.html', films=search_data)


@app.route('/show_all')
def show_all():
    """Show all the movies"""
    db_film = get_db()
    film_data = db_film.execute(
        'SELECT * FROM film'
    ).fetchall()

    return render_template('index.html', films=film_data)


@app.route('/film/<int:id_film>')
def show_one(id_film=None):
    """Show a specific movie based on its id"""
    db_film = get_db()
    film = db_film.execute(
        'SELECT * FROM film WHERE id_film = ?',
        (id_film,)
    ).fetchone()

    return render_template('film.html', film=film)


@app.route('/delete/<int:id_film>', methods=['POST', 'GET'])
@login_required
def delete(id_film=None):
    """Delete a movie from the database"""
    db_film = get_db()
    db_film.execute(
        'DELETE FROM film WHERE id_film = ? ',
        (id_film,)
    )
    db_film.commit()
    success = "Le film a bien été supprimé"
    flash(success, 'success')
    return render_template('index.html')


@app.route('/update/<int:id_film>', methods=['POST', 'GET'])
@login_required
def update(id_film=None):
    """Update an existing movie in the database via a form"""
    db_film = get_db()
    error = None

    if request.method == 'POST':
        title = request.form['title']
        realisateur = request.form['realisateur']
        date_sortie = request.form['date_sortie']
        synopsis = request.form['synopsis']

        if not title:
            error = 'Veuillez saisir le titre !'
        elif not realisateur:
            error = 'Veuillez saisir le réalisateur !'
        elif not date_sortie:
            error = 'Veuillez saisir la date de sortie !'
        elif not synopsis:
            error = 'Veuillez saisir le synopsis !'

        if error is None:
            db_film.execute(
                'UPDATE film SET title = ?, realisateur = ?, date_sortie = ?, synopsis = ?, modify_by = ?, modified = ? WHERE id_film = ?',
                (title, realisateur, date_sortie, synopsis, session['id_user'], datetime.datetime.now(), id_film,)
            )
            db_film.commit()
            success = "La modification a été effectué"
            flash(success, 'success')
            return show_one(id_film)

        flash(error, 'danger')

    return show_one(id_film)
