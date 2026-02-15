from flask import Flask, render_template, request, redirect, url_for, send_file, flash
import sqlite3
from datetime import datetime
import os
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib import colors
import qrcode
from io import BytesIO

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui_2024'

# Configurações
DATABASE = 'etiquetas.db'
UPLOAD_FOLDER = 'static/uploads'

# Criar pasta para uploads se não existir
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ==================== FUNÇÕES DO BANCO DE DADOS ====================

def get_db_connection():
    """Conecta ao banco de dados SQLite"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inicializa o banco de dados com as tabelas necessárias"""
    conn = get_db_connection()
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
            ativo INTEGER DEFAULT 1
        )
    ''')
    conn.commit()
    conn.close()

# ==================== ROTAS PRINCIPAIS ====================

@app.route('/')
def index():
    """Página inicial - Lista todas as etiquetas"""
    conn = get_db_connection()
    etiquetas = conn.execute('SELECT * FROM etiquetas WHERE ativo = 1 ORDER BY data_criacao DESC').fetchall()
    conn.close()
    return render_template('index.html', etiquetas=etiquetas)

@app.route('/criar', methods=['GET', 'POST'])
def criar():
    """Criar nova etiqueta"""
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
                'INSERT INTO etiquetas (nome, descricao, codigo, categoria, preco, tamanho) VALUES (?, ?, ?, ?, ?, ?)',
                (nome, descricao, codigo, categoria, preco, tamanho)
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
def editar(id):
    """Editar etiqueta existente"""
    conn = get_db_connection()
    etiqueta = conn.execute('SELECT * FROM etiquetas WHERE id = ?', (id,)).fetchone()
    
    if etiqueta is None:
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
                'UPDATE etiquetas SET nome = ?, descricao = ?, codigo = ?, categoria = ?, preco = ?, tamanho = ? WHERE id = ?',
                (nome, descricao, codigo, categoria, preco, tamanho, id)
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
def deletar(id):
    """Deletar etiqueta (soft delete)"""
    conn = get_db_connection()
    conn.execute('UPDATE etiquetas SET ativo = 0 WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Etiqueta deletada com sucesso!', 'success')
    return redirect(url_for('index'))

@app.route('/buscar')
def buscar():
    """Buscar etiquetas"""
    termo = request.args.get('q', '')
    conn = get_db_connection()
    etiquetas = conn.execute(
        'SELECT * FROM etiquetas WHERE ativo = 1 AND (nome LIKE ? OR codigo LIKE ? OR categoria LIKE ?) ORDER BY data_criacao DESC',
        (f'%{termo}%', f'%{termo}%', f'%{termo}%')
    ).fetchall()
    conn.close()
    return render_template('index.html', etiquetas=etiquetas, termo_busca=termo)

# ==================== GERAÇÃO DE PDF ====================

@app.route('/gerar_pdf/<int:id>')
def gerar_pdf(id):
    """Gerar PDF de uma etiqueta específica"""
    conn = get_db_connection()
    etiqueta = conn.execute('SELECT * FROM etiquetas WHERE id = ?', (id,)).fetchone()
    conn.close()
    
    if etiqueta is None:
        flash('Etiqueta não encontrada!', 'error')
        return redirect(url_for('index'))
    
    # Criar PDF
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    
    # Configurar tamanhos baseados na escolha
    tamanhos = {
        'pequeno': (50*mm, 30*mm),
        'medio': (80*mm, 50*mm),
        'grande': (100*mm, 70*mm)
    }
    
    largura, altura = tamanhos.get(etiqueta['tamanho'], tamanhos['medio'])
    
    # Posição inicial
    x_start = 50
    y_start = 750
    
    # Desenhar etiqueta
    pdf.setStrokeColor(colors.black)
    pdf.setLineWidth(1)
    pdf.rect(x_start, y_start - altura, largura, altura)
    
    # Nome do produto
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(x_start + 10, y_start - 30, etiqueta['nome'][:30])
    
    # Código
    pdf.setFont("Helvetica", 10)
    pdf.drawString(x_start + 10, y_start - 50, f"Código: {etiqueta['codigo']}")
    
    # Categoria
    if etiqueta['categoria']:
        pdf.drawString(x_start + 10, y_start - 65, f"Categoria: {etiqueta['categoria']}")
    
    # Preço
    if etiqueta['preco'] and float(etiqueta['preco']) > 0:
        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(x_start + 10, y_start - 90, f"R$ {float(etiqueta['preco']):.2f}")
    
    # Gerar QR Code
    qr = qrcode.QRCode(version=1, box_size=3, border=1)
    qr.add_data(f"Código: {etiqueta['codigo']}\nNome: {etiqueta['nome']}")
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # Salvar QR Code temporariamente
    qr_path = os.path.join(UPLOAD_FOLDER, f'qr_{id}.png')
    qr_img.save(qr_path)
    
    # Adicionar QR Code ao PDF
    pdf.drawImage(qr_path, x_start + largura - 70, y_start - altura + 10, 60, 60)
    
    # Descrição
    if etiqueta['descricao']:
        pdf.setFont("Helvetica", 8)
        texto = etiqueta['descricao'][:100]
        pdf.drawString(x_start + 10, y_start - altura + 15, texto)
    
    # Finalizar PDF
    pdf.save()
    buffer.seek(0)
    
    # Limpar QR Code temporário
    if os.path.exists(qr_path):
        os.remove(qr_path)
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f'etiqueta_{etiqueta["codigo"]}.pdf',
        mimetype='application/pdf'
    )

@app.route('/gerar_pdf_todas')
def gerar_pdf_todas():
    """Gerar PDF com todas as etiquetas ativas"""
    conn = get_db_connection()
    etiquetas = conn.execute('SELECT * FROM etiquetas WHERE ativo = 1 ORDER BY nome').fetchall()
    conn.close()
    
    if not etiquetas:
        flash('Nenhuma etiqueta encontrada!', 'warning')
        return redirect(url_for('index'))
    
    # Criar PDF
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    
    # Configurações
    x_margin = 50
    y_start = 750
    etiqueta_altura = 100
    y_current = y_start
    
    for etiqueta in etiquetas:
        if y_current < 100:
            pdf.showPage()
            y_current = y_start
        
        # Desenhar etiqueta
        pdf.setStrokeColor(colors.black)
        pdf.setLineWidth(0.5)
        pdf.rect(x_margin, y_current - etiqueta_altura, 500, etiqueta_altura)
        
        # Conteúdo
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
    app.run(debug=True, host='0.0.0.0', port=5000)