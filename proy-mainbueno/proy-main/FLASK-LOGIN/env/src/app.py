from io import BytesIO
import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from flask_mysqldb import MySQL
from flask_login import LoginManager, login_user, logout_user, login_required
from werkzeug.utils import secure_filename
from config import config
from modelos.ModelUser import ModelUser
from modelos.entities.User import User
from datetime import datetime

def get_habitacion(id):
    cursor = db.connection.cursor()
    cursor.execute("SELECT * FROM habitaciones WHERE id = %s", (id,))
    habitacion = cursor.fetchone()
    cursor.close()
    if habitacion:
        return {
            'id': habitacion[0],
            'nombre': habitacion[1],
            'tipo': habitacion[2],
            'estado': habitacion[3],
            'imagen': habitacion[4],
            'tiempo_reservacion': habitacion[5],
            'precio': habitacion[6],
            'metodo_pago': habitacion[7],
            'numero_personas': habitacion[8],
            'id_orden': habitacion[9],
            'estado_pago': habitacion[10]
        }
    else:
        return None

def update_habitacion(id, data):
    cursor = db.connection.cursor()
    cursor.execute("""
        UPDATE habitaciones SET nombre=%s, tipo=%s, estado=%s, tiempo_reservacion=%s, 
        precio=%s, metodo_pago=%s, numero_personas=%s, id_orden=%s, estado_pago=%s 
        WHERE id=%s
    """, (
        data['nombre'], data['tipo'], data['estado'], data['tiempo_reservacion'], 
        data['precio'], data['metodo_pago'], data['numero_personas'], 
        data['id_orden'], data['estado_pago'], id
    ))
    db.connection.commit()
    cursor.close()

def registrar_evento_historial(id_habitacion, id_orden, imagen, accion='agregar'):
    cursor = db.connection.cursor()
    cursor.execute("""
        INSERT INTO habitaciones_historial (id_habitacion, id_orden, imagen, accion, fecha_eliminacion)
        VALUES (%s, %s, %s, %s, %s)
    """, (id_habitacion, id_orden, imagen, accion, datetime.now()))
    db.connection.commit()
    cursor.close()




app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Configuración del directorio de subida de archivos
app.config['UPLOAD_FOLDER'] = 'proy-main//FLASK-LOGIN/env/src/static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limitar el tamaño de archivo a 16MB

# Configuración de la base de datos
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'hotel_gestor'
db = MySQL(app)

login_manager_app = LoginManager(app)
login_manager_app.login_view = 'login'  # Redirige a la página de login si no está autenticado

@login_manager_app.user_loader
def load_user(id):
    return ModelUser.get_by_id(db, id)

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User(0, request.form['username'], request.form['password'])
        logged_user = ModelUser.login(db, user)
        if logged_user is not None:
            if logged_user.password:
                login_user(logged_user)
                return redirect(url_for('home'))
            else:
                flash("Contraseña incorrecta...")
                return render_template('auth/login.html')
        else:
            flash("Usuario no encontrado...")
            return render_template('auth/login.html')
    else:
        return render_template('auth/login.html')

@app.route('/layout')
@login_required
def layout():
    return render_template('layout.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/home')
@login_required
def home():
    return render_template('home.html')

@app.route('/registro')
def registro():
    return render_template('registro.html')

@app.route('/configuracion', methods=['GET', 'POST'])
def configuracion():
    if request.method == 'POST':
        if 'agregar' in request.form:
            nombre = request.form['nombre']
            tipo = request.form['tipo']
            imagen = request.files['imagen']
            if imagen and allowed_file(imagen.filename):
                filename = secure_filename(imagen.filename)
                imagen.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                cursor = db.connection.cursor()
                cursor.execute(
                    "INSERT INTO habitaciones (nombre, tipo, estado, imagen) VALUES (%s, %s, %s, %s)",
                    (nombre, tipo, 'libre', filename)
                )
                db.connection.commit()
                id_habitacion = cursor.lastrowid
                cursor.close()

                registrar_evento_historial(id_habitacion, None, filename, 'agregar')

        elif 'eliminar' in request.form:
            habitacion_id = int(request.form['id'])
            eliminar_habitacion(habitacion_id)

    cursor = db.connection.cursor()
    cursor.execute("SELECT * FROM habitaciones")
    habitaciones = cursor.fetchall()
    cursor.close()
    return render_template('configuracion.html', habitaciones=habitaciones)
def eliminar_habitacion(id_habitacion):
    cursor = db.connection.cursor()
    cursor.execute("UPDATE ordenes SET habitacion_id = NULL WHERE habitacion_id = %s", (id_habitacion,))
    cursor.execute("DELETE FROM habitaciones WHERE id = %s", (id_habitacion,))
    db.connection.commit()
    cursor.close()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

@app.route('/editar_habitacion/<int:id>', methods=['GET', 'POST'])
def editar_habitacion(id):
    cursor = db.connection.cursor()
    cursor.execute("SELECT * FROM habitaciones WHERE id = %s", (id,))
    habitacion = cursor.fetchone()
    cursor.close()
    
    if not habitacion:
        return redirect(url_for('configuracion'))

    if request.method == 'POST':
        estado = request.form['estado']
        precio = request.form['precio']
        metodo_pago = request.form['metodo_pago']
        numero_personas = request.form['numero_personas']
        estado_pago = request.form['estado_pago']
        tiempo_reservacion = request.form['tiempo_reservacion']
        cursor = db.connection.cursor()
        cursor.execute("""
            UPDATE habitaciones SET estado=%s, tiempo_reservacion=%s, 
            precio=%s, metodo_pago=%s, numero_personas=%s, estado_pago=%s 
            WHERE id=%s
        """, (
            estado, tiempo_reservacion, precio, metodo_pago, 
            numero_personas, estado_pago, id
        ))
        db.connection.commit()
        cursor.close()

        registrar_evento_historial(id, None, None, 'editar')

        return redirect(url_for('configuracion'))
    return render_template('editar_habitacion.html', habitacion=habitacion)




@app.route('/habitaciones')
@login_required
def habitaciones():
    tipo = request.args.get('tipo')
    estado = request.args.get('estado')
    metodo_pago = request.args.get('metodo_pago')
    
    query = "SELECT * FROM habitaciones WHERE 1=1"
    filters = []

    if tipo:
        query += " AND tipo = %s"
        filters.append(tipo)
    
    if estado:
        query += " AND estado = %s"
        filters.append(estado)

    if metodo_pago:
        query += " AND metodo_pago = %s"
        filters.append(metodo_pago)
    
    cursor = db.connection.cursor()
    cursor.execute(query, filters)
    habitaciones = cursor.fetchall()

    habitaciones_dicts = []
    for habitacion in habitaciones:
        habitacion_dict = {
            'id': habitacion[0],
            'nombre': habitacion[1],
            'tipo': habitacion[2],
            'estado': habitacion[3],
            'imagen': habitacion[4],
            'tiempo_reservacion': habitacion[5],
            'metodo_pago': habitacion[7]
        }
        habitaciones_dicts.append(habitacion_dict)

    return render_template('habitaciones.html', habitaciones=habitaciones_dicts, active_page='habitaciones')


@app.route('/historial_habitaciones', methods=['GET'])
def historial_habitaciones():
    cursor = db.connection.cursor()
    cursor.execute("""
        SELECT hh.id, hh.id_habitacion, hh.id_orden, hh.imagen, hh.fecha_eliminacion, h.nombre, hh.accion 
        FROM habitaciones_historial hh
        JOIN habitaciones h ON hh.id_habitacion = h.id
    """)
    historial = cursor.fetchall()
    cursor.close()
    return render_template('historial.html', historial=historial)

@app.route('/habitacion/<int:id>', methods=['GET', 'POST'])
@login_required
def habitacion_detalle(id):
    cursor = db.connection.cursor()
    if request.method == 'POST':
        nombre = request.form['nombre']
        tipo = request.form['tipo']
        estado = request.form['estado']
        tiempo_reservacion = request.form['tiempo_reservacion']
        precio = request.form['precio']
        metodo_pago = request.form['metodo_pago']
        numero_personas = request.form['numero_personas']
        id_orden = request.form['id_orden']
        estado_pago = request.form['estado_pago']

        cursor.execute("""
            UPDATE habitaciones SET nombre=%s, tipo=%s, estado=%s, tiempo_reservacion=%s, 
            precio=%s, metodo_pago=%s, numero_personas=%s, id_orden=%s, estado_pago=%s 
            WHERE id=%s
        """, (nombre, tipo, estado, tiempo_reservacion, precio, metodo_pago, numero_personas, id_orden, estado_pago, id))
        db.connection.commit()

    cursor.execute("SELECT * FROM habitaciones WHERE id = %s", (id,))
    habitacion = cursor.fetchone()

    if habitacion:
        habitacion_dict = {
            'id': habitacion[0],
            'nombre': habitacion[1],
            'tipo': habitacion[2],
            'estado': habitacion[3],
            'imagen': habitacion[4],
            'tiempo_reservacion': habitacion[5],
            'precio': habitacion[6],
            'metodo_pago': habitacion[7],
            'numero_personas': habitacion[8],
            'id_orden': habitacion[9],
            'estado_pago': habitacion[10]
        }
    else:
        habitacion_dict = None

    return render_template('habitacion_detalle.html', habitacion=habitacion_dict)



@app.route('/get_user_photo')
def get_user_photo():
    user_id = request.args.get('user_id')
    cursor = db.connection.cursor()
    cursor.execute("SELECT photo FROM user WHERE id=%s", (user_id,))
    user = cursor.fetchone()
    cursor.close()

    if user and user[0]:  # Verificar si se ha encontrado el usuario y si tiene una foto
        return send_file(BytesIO(user[0]), mimetype='image/jpeg')
    else:
        return "Usuario no encontrado o sin foto asociada", 404
    

@app.route('/upload_photo', methods=['POST'])
def upload_photo():
    if 'photo' not in request.files:
        flash('No file part')
        return redirect(request.url)

    file = request.files['photo']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        with open(os.path.join(app.config['UPLOAD_FOLDER'], filename), 'rb') as f:
            photo_data = f.read()

        user_id = request.form['user_id']
        cursor = db.connection.cursor()
        cursor.execute("UPDATE user SET photo=%s WHERE id=%s", (photo_data, user_id))
        db.connection.commit()
        cursor.close()
    
        return redirect(url_for('some_view'))
    else:
        flash('Invalid file format')
        return redirect(request.url)

    
if __name__ == '__main__':
    app.config.from_object(config['development'])
    app.run(debug=True)