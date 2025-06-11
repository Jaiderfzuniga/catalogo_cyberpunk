from flask import Flask, render_template, request, redirect, url_for, session
import os
import sqlite3
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'clave_predeterminada')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin**')

app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['DATABASE'] = 'catalog.db'

# Asegura que la carpeta para imágenes exista
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def get_db_connection():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    items = conn.execute('SELECT * FROM prendas ORDER BY categoria').fetchall()
    conn.close()
    return render_template('catalog.html', items=items, admin=session.get('admin'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['password'] == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('index'))

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if not session.get('admin'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        image = request.files['image']
        categoria = request.form['categoria']
        precio = request.form['precio']
        talla = request.form['talla']
        if image:
            filename = secure_filename(image.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(filepath)
            conn = get_db_connection()
            conn.execute('INSERT INTO prendas (imagen, categoria, precio, talla) VALUES (?, ?, ?, ?)',
                         (filename, categoria, precio, talla))
            conn.commit()
            conn.close()
            return redirect(url_for('index'))
    return render_template('upload.html')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    if not session.get('admin'):
        return redirect(url_for('login'))
    conn = get_db_connection()
    item = conn.execute('SELECT * FROM prendas WHERE id = ?', (id,)).fetchone()
    if request.method == 'POST':
        categoria = request.form['categoria']
        precio = request.form['precio']
        talla = request.form['talla']
        image = request.files.get('image')
        if image and image.filename:
            filename = secure_filename(image.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(filepath)
            conn.execute('UPDATE prendas SET imagen=?, categoria=?, precio=?, talla=? WHERE id=?',
                         (filename, categoria, precio, talla, id))
        else:
            conn.execute('UPDATE prendas SET categoria=?, precio=?, talla=? WHERE id=?',
                         (categoria, precio, talla, id))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    conn.close()
    return render_template('edit.html', item=item)

@app.route('/delete/<int:id>')
def delete(id):
    if not session.get('admin'):
        return redirect(url_for('login'))
    conn = get_db_connection()
    item = conn.execute('SELECT * FROM prendas WHERE id = ?', (id,)).fetchone()
    if item:
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], item['imagen'])
        if os.path.exists(image_path):
            os.remove(image_path)
        conn.execute('DELETE FROM prendas WHERE id = ?', (id,))
        conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with sqlite3.connect(app.config['DATABASE']) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS prendas (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            imagen TEXT NOT NULL,
                            categoria TEXT NOT NULL,
                            precio TEXT NOT NULL,
                            talla TEXT NOT NULL
                        )''')
    app.run(debug=True)
