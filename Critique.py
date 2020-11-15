import os
import sqlite3
import click
import functools
import datetime
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
        if session.get('id_user') is None:
            return redirect(url_for('index'))
        return view(**kwargs)
    return wrapped_view



@app.route('/')
def index():
     return render_template('index.html', films='')

@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        db_connect = get_db()
        error = None

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

@app.route('/add', methods=['GET','POST'])
@login_required
def add():
    
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
            return redirect(url_for('index'))

        flash(error)

    return render_template('add.html')

@app.route('/show_research',methods=['POST', 'GET'])
def show_research():

    db_film = get_db()
    error = None
    film_title = request.form['film_title']
    if not film_title:
        error = 'Veuillez renseigner un titre dans la barre de recherche'

    if error is None:
        search_data = db_film.execute(
            'SELECT * FROM film WHERE title like ?',
            ('%'+film_title+'%',)
        ).fetchall()

    flash(error)
    return render_template('index.html', films=search_data)

@app.route('/show_all')
def show_all():
    db_film = get_db()
    film_data = db_film.execute(
        'SELECT * FROM film'
    ).fetchall()

    return render_template('index.html', films=film_data)

@app.route('/film/<int:id_film>')
def show_one(id_film = None):
    db_film = get_db()
    film = db_film.execute(
        'SELECT * FROM film WHERE id_film = ?',
        (id_film,)
    ).fetchone()

    return render_template('film.html', film = film)

@app.route('/delete/<int:id_film>', methods=['POST', 'GET'])
@login_required
def delete(id_film = None):
    db_film = get_db()
    db_film.execute(
        'DELETE FROM film WHERE id_film = ? ',
        (id_film,)
    )
    db_film.commit()
    success = "Le film a bien été supprimé"
    flash(success)
    return render_template('index.html')

@app.route('/update/<int:id_film>', methods=['POST', 'GET'])
@login_required
def update(id_film = None):
    db_film = get_db()

    error = None
    if request.method == 'POST' :
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
        flash(error)
        flash(success)

    return render_template('index.html')