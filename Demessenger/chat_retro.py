import os
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from flask_socketio import SocketIO, join_room, leave_room, emit
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secreto_muy_secreto'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # max 5MB

socketio = SocketIO(app)

# Permitir solo imágenespip install flask flask-socketio eventlet


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Página principal: menú para crear o unirse a sala
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        room = request.form.get('room').strip()
        if not username or not room:
            return render_template('index.html', error="Por favor completa ambos campos")
        return redirect(url_for('chat_room', room=room, username=username))
    return render_template('index.html')

# Página de chat de la sala
@app.route('/chat/<room>')
def chat_room(room):
    username = request.args.get('username')
    if not username:
        return redirect(url_for('index'))
    return render_template('chat.html', room=room, username=username)

# Ruta para subir imágenes
@app.route('/upload', methods=['POST'])
def upload():
    if 'image' not in request.files:
        return {'error': 'No file part'}, 400
    file = request.files['image']
    if file.filename == '':
        return {'error': 'No selected file'}, 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        # Evitar sobreescribir
        base, ext = os.path.splitext(filename)
        i = 1
        while os.path.exists(path):
            filename = f"{base}_{i}{ext}"
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            i += 1
        file.save(path)
        return {'url': url_for('static', filename='uploads/' + filename)}
    else:
        return {'error': 'Formato no permitido'}, 400

# SocketIO Events
@socketio.on('join')
def on_join(data):
    username = data['username']
    room = data['room']
    join_room(room)
    emit('message', {'username': 'Sistema', 'msg': f'{username} se ha unido a la sala.'}, room=room)

@socketio.on('leave')
def on_leave(data):
    username = data['username']
    room = data['room']
    leave_room(room)
    emit('message', {'username': 'Sistema', 'msg': f'{username} ha salido de la sala.'}, room=room)

@socketio.on('send_message')
def handle_message(data):
    room = data['room']
    username = data['username']
    msg = data['msg']
    img_url = data.get('img_url')
    # Emitir a todos en la sala el mensaje (texto o imagen)
    emit('message', {'username': username, 'msg': msg, 'img_url': img_url}, room=room)

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    socketio.run(app, debug=True)
