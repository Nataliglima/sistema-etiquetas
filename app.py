from flask import Flask, render_template, request, redirect, url_for, send_file, flash
import sqlite3
from datetime import datetime
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib import colors
import qrcode
from io import BytesIO

from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui_2024'

# ==================== FLASK LOGIN ====================

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class User(UserMixin):
    def __init__(self, id, username, email):
        self.id = id
        self.username = username
        self.email = email


@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    user = conn.execute(
        'SELECT * FROM usuarios WHERE id = ?',
        (user_id,)
    ).fetchone()
    conn.close()

    if user:
        return User(user['id'], user['username'], user['email'])
    return None


# ==================== CONFIGURAÇÕES ====================

DATABASE = 'etiquetas.db'
UPLOAD_FOLDER = 'static/uploads'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


# ==================== BANCO DE DADOS ====================

def get_db_connection():
    """Cria conexão com banco de dados SQLite"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Inicializa o banco de dados com as tabelas necessárias"""
    try:
        conn = get_db_connection()
        conn.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS etiquetas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                descricao TEXT,
                codigo TEXT UNIQUE NOT NULL,
                categoria TEXT,
                preco REAL,
                tamanho TEXT DEFAULT 'medio',
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ativo INTEGER DEFAULT 1,
                user_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES usuarios (id)
            )
        ''')
        conn.commit()
        conn.close()
        print("✅ Banco de dados inicializado com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao inicializar banco: {e}")

# Garantir que o banco existe a cada conexão
def ensure_db():
    """Garante que as tabelas existem antes de qualquer operação"""
    init_db()




# ==================== AUTENTICAÇÃO ====================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM usuarios WHERE username = ?',
            (username,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            user_obj = User(user['id'], user['username'], user['email'])
            login_user(user_obj)
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Usuário ou senha incorretos!', 'error')

    return render_template('login.html')


@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        password_confirm = request.form['password_confirm']

        if password != password_confirm:
            flash('As senhas não coincidem!', 'error')
            return render_template('registro.html')

        password_hash = generate_password_hash(password)

        try:
            conn = get_db_connection()
            conn.execute(
                'INSERT INTO usuarios (username, email, password) VALUES (?, ?, ?)',
                (username, email, password_hash)
            )
            conn.commit()
            conn.close()

            flash('Registro realizado com sucesso! Faça login.', 'success')
            return redirect(url_for('login'))

        except sqlite3.IntegrityError:
            flash('Usuário ou email já existem!', 'error')

    return render_template('registro.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout realizado com sucesso!', 'success')
    return redirect(url_for('login'))


# ==================== ROTAS PRINCIPAIS ====================

@app.route('/')
@login_required
def index():
    conn = get_db_connection()

    etiquetas = conn.execute(
        'SELECT * FROM etiquetas WHERE ativo = 1 AND user_id = ? ORDER BY data_criacao DESC',
        (current_user.id,)
    ).fetchall()

    conn.close()

    return render_template('index.html', etiquetas=etiquetas)


@app.route('/criar', methods=['GET', 'POST'])
@login_required
def criar():
    if request.method == 'POST':
        nome = request.form['nome']
        descricao = request.form.get('descricao', '')
        codigo = request.form['codigo']
        categoria = request.form.get('categoria', '')
        preco = request.form.get('preco', 0.0)
        tamanho = request.form.get('tamanho', 'medio')

        try:
            conn = get_db_connection()
            conn.execute(
                '''INSERT INTO etiquetas 
                   (nome, descricao, codigo, categoria, preco, tamanho, user_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (nome, descricao, codigo, categoria, preco, tamanho, current_user.id)
            )
            conn.commit()
            conn.close()

            flash('Etiqueta criada com sucesso!', 'success')
            return redirect(url_for('index'))

        except sqlite3.IntegrityError:
            flash('Erro: Código já existe!', 'error')

        except Exception as e:
            flash(f'Erro ao criar etiqueta: {str(e)}', 'error')

    return render_template('criar.html')


@app.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    conn = get_db_connection()

    etiqueta = conn.execute(
        'SELECT * FROM etiquetas WHERE id = ? AND user_id = ?',
        (id, current_user.id)
    ).fetchone()

    if etiqueta is None:
        conn.close()
        flash('Etiqueta não encontrada!', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        nome = request.form['nome']
        descricao = request.form.get('descricao', '')
        codigo = request.form['codigo']
        categoria = request.form.get('categoria', '')
        preco = request.form.get('preco', 0.0)
        tamanho = request.form.get('tamanho', 'medio')

        try:
            conn.execute(
                '''UPDATE etiquetas 
                   SET nome = ?, descricao = ?, codigo = ?, categoria = ?, preco = ?, tamanho = ?
                   WHERE id = ? AND user_id = ?''',
                (nome, descricao, codigo, categoria, preco, tamanho, id, current_user.id)
            )
            conn.commit()
            conn.close()

            flash('Etiqueta atualizada com sucesso!', 'success')
            return redirect(url_for('index'))

        except sqlite3.IntegrityError:
            flash('Erro: Código já existe!', 'error')

        except Exception as e:
            flash(f'Erro ao atualizar etiqueta: {str(e)}', 'error')

    conn.close()
    return render_template('editar.html', etiqueta=etiqueta)

@app.route('/deletar/<int:id>')
@login_required
def deletar(id):
    conn = get_db_connection()
    conn.execute(
        'UPDATE etiquetas SET ativo = 0 WHERE id = ? AND user_id = ?',
        (id, current_user.id)
    )
    conn.commit()
    conn.close()

    flash('Etiqueta deletada com sucesso!', 'success')
    return redirect(url_for('index'))


@app.route('/buscar')
@login_required
def buscar():
    termo = request.args.get('q', '')

    conn = get_db_connection()
    etiquetas = conn.execute(
        '''SELECT * FROM etiquetas 
           WHERE ativo = 1 AND user_id = ? 
           AND (nome LIKE ? OR codigo LIKE ? OR categoria LIKE ?)
           ORDER BY data_criacao DESC''',
        (current_user.id, f'%{termo}%', f'%{termo}%', f'%{termo}%')
    ).fetchall()
    conn.close()

    return render_template('index.html', etiquetas=etiquetas, termo_busca=termo)


# ==================== GERAÇÃO DE PDF ====================

@app.route('/gerar_pdf/<int:id>')
@login_required
def gerar_pdf(id):
    conn = get_db_connection()
    etiqueta = conn.execute(
        'SELECT * FROM etiquetas WHERE id = ? AND user_id = ?',
        (id, current_user.id)
    ).fetchone()
    conn.close()

    if etiqueta is None:
        flash('Etiqueta não encontrada!', 'error')
        return redirect(url_for('index'))

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)

    tamanhos = {
        'pequeno': (50 * mm, 30 * mm),
        'medio': (80 * mm, 50 * mm),
        'grande': (100 * mm, 70 * mm)
    }

    largura, altura = tamanhos.get(etiqueta['tamanho'], tamanhos['medio'])

    x_start = 50
    y_start = 750

    pdf.setStrokeColor(colors.black)
    pdf.setLineWidth(1)
    pdf.rect(x_start, y_start - altura, largura, altura)

    padding = 8

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(x_start + padding, y_start - padding - 10, etiqueta['nome'][:30])

    pdf.setFont("Helvetica", 9)
    pdf.drawString(x_start + padding, y_start - padding - 25, f"Código: {etiqueta['codigo']}")

    if etiqueta['categoria']:
        pdf.drawString(x_start + padding, y_start - padding - 38, f"Categoria: {etiqueta['categoria']}")

    if etiqueta['preco'] and float(etiqueta['preco']) > 0:
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(x_start + padding, y_start - altura + 20, f"R$ {float(etiqueta['preco']):.2f}")

    qr = qrcode.QRCode(version=1, box_size=2, border=1)
    qr.add_data(f"Código: {etiqueta['codigo']}\nNome: {etiqueta['nome']}")
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")

    qr_path = os.path.join(UPLOAD_FOLDER, f'qr_{id}.png')
    qr_img.save(qr_path)

    qr_size = altura * 0.6

    pdf.drawImage(
        qr_path,
        x_start + largura - qr_size - padding,
        y_start - altura + padding,
        qr_size,
        qr_size
    )

    pdf.save()
    buffer.seek(0)

    if os.path.exists(qr_path):
        os.remove(qr_path)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f'etiqueta_{etiqueta['codigo']}.pdf',
        mimetype='application/pdf'
    )



@app.route('/gerar_pdf_todas')
@login_required
def gerar_pdf_todas():
    conn = get_db_connection()
    etiquetas = conn.execute(
        'SELECT * FROM etiquetas WHERE ativo = 1 AND user_id = ? ORDER BY nome',
        (current_user.id,)
    ).fetchall()
    conn.close()

    if not etiquetas:
        flash('Nenhuma etiqueta encontrada!', 'warning')
        return redirect(url_for('index'))

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)

    x_margin = 50
    y_start = 750
    etiqueta_altura = 100
    y_current = y_start

    for etiqueta in etiquetas:
        if y_current < 100:
            pdf.showPage()
            y_current = y_start

        pdf.setStrokeColor(colors.black)
        pdf.setLineWidth(0.5)
        pdf.rect(x_margin, y_current - etiqueta_altura, 500, etiqueta_altura)

        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(x_margin + 10, y_current - 25, etiqueta['nome'])

        pdf.setFont("Helvetica", 9)
        pdf.drawString(x_margin + 10, y_current - 45, f"Código: {etiqueta['codigo']}")

        if etiqueta['categoria']:
            pdf.drawString(x_margin + 10, y_current - 60, f"Categoria: {etiqueta['categoria']}")

        if etiqueta['preco'] and float(etiqueta['preco']) > 0:
            pdf.setFont("Helvetica-Bold", 14)
            pdf.drawString(x_margin + 10, y_current - 85, f"R$ {float(etiqueta['preco']):.2f}")

        y_current -= (etiqueta_altura + 10)

    pdf.save()
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name='todas_etiquetas.pdf',
        mimetype='application/pdf'
    )


# ==================== INICIALIZAÇÃO ====================

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
else:
    # Em produção (Render), inicializar o banco automaticamente
    init_db()