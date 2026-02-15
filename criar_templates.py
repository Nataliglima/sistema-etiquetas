import os

# Criar pasta templates se não existir
if not os.path.exists('templates'):
    os.makedirs('templates')
    print("✅ Pasta 'templates' criada!")

# Template base.html
base_html = '''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Sistema de Etiquetas{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css">
    <style>
        body { background-color: #f8f9fa; }
        .navbar { background-color: #2c3e50 !important; box-shadow: 0 2px 4px rgba(0,0,0,.1); }
        .card { border: none; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,.1); transition: transform 0.2s; }
        .card:hover { transform: translateY(-5px); }
        .btn-primary { background-color: #3498db; border: none; }
        .btn-primary:hover { background-color: #2980b9; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark mb-4">
        <div class="container">
            <a class="navbar-brand" href="{{ url_for('index') }}">
                <i class="bi bi-tag-fill"></i> Sistema de Etiquetas
            </a>
            <div class="collapse navbar-collapse">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item"><a class="nav-link" href="{{ url_for('index') }}"><i class="bi bi-house-door"></i> Início</a></li>
                    <li class="nav-item"><a class="nav-link" href="{{ url_for('criar') }}"><i class="bi bi-plus-circle"></i> Nova Etiqueta</a></li>
                    <li class="nav-item"><a class="nav-link" href="{{ url_for('gerar_pdf_todas') }}"><i class="bi bi-file-earmark-pdf"></i> Exportar Todas</a></li>
                </ul>
            </div>
        </div>
    </nav>
    <div class="container">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ 'success' if category == 'success' else 'danger' }} alert-dismissible fade show">
                        {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        {% block content %}{% endblock %}
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>'''

# Template index.html
index_html = '''{% extends "base.html" %}
{% block title %}Início - Sistema de Etiquetas{% endblock %}
{% block content %}
<div class="row mb-4">
    <div class="col-md-8"><h2><i class="bi bi-tags"></i> Minhas Etiquetas</h2></div>
    <div class="col-md-4">
        <form action="{{ url_for('buscar') }}" method="get" class="d-flex">
            <input class="form-control me-2" type="search" name="q" placeholder="Buscar...">
            <button class="btn btn-outline-primary" type="submit"><i class="bi bi-search"></i></button>
        </form>
    </div>
</div>
{% if etiquetas %}
<div class="row">
    {% for etiqueta in etiquetas %}
    <div class="col-md-4 mb-4">
        <div class="card h-100">
            <div class="card-body">
                <h5 class="card-title"><i class="bi bi-tag"></i> {{ etiqueta['nome'] }}</h5>
                <p class="card-text"><strong>Código:</strong> <span class="badge bg-secondary">{{ etiqueta['codigo'] }}</span></p>
                {% if etiqueta['categoria'] %}<p><strong>Categoria:</strong> {{ etiqueta['categoria'] }}</p>{% endif %}
                {% if etiqueta['preco'] and etiqueta['preco'] > 0 %}
                    <p><strong>Preço:</strong> <span class="text-success fw-bold">R$ {{ "%.2f"|format(etiqueta['preco']) }}</span></p>
                {% endif %}
                <div class="d-flex gap-2 mt-3">
                    <a href="{{ url_for('gerar_pdf', id=etiqueta['id']) }}" class="btn btn-sm btn-success flex-fill"><i class="bi bi-file-earmark-pdf"></i> PDF</a>
                    <a href="{{ url_for('editar', id=etiqueta['id']) }}" class="btn btn-sm btn-primary flex-fill"><i class="bi bi-pencil"></i> Editar</a>
                    <a href="{{ url_for('deletar', id=etiqueta['id']) }}" class="btn btn-sm btn-danger flex-fill" onclick="return confirm('Deletar?')"><i class="bi bi-trash"></i></a>
                </div>
            </div>
        </div>
    </div>
    {% endfor %}
</div>
{% else %}
<div class="alert alert-warning text-center">
    <h4>Nenhuma etiqueta encontrada</h4>
    <a href="{{ url_for('criar') }}" class="btn btn-primary mt-2"><i class="bi bi-plus-circle"></i> Criar Primeira Etiqueta</a>
</div>
{% endif %}
{% endblock %}'''

# Template criar.html
criar_html = '''{% extends "base.html" %}
{% block title %}Criar Etiqueta{% endblock %}
{% block content %}
<div class="row justify-content-center">
    <div class="col-md-8">
        <div class="card">
            <div class="card-header bg-primary text-white">
                <h4 class="mb-0"><i class="bi bi-plus-circle"></i> Criar Nova Etiqueta</h4>
            </div>
            <div class="card-body">
                <form method="POST">
                    <div class="mb-3">
                        <label class="form-label">Nome do Produto <span class="text-danger">*</span></label>
                        <input type="text" class="form-control" name="nome" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Código <span class="text-danger">*</span></label>
                        <input type="text" class="form-control" name="codigo" required>
                    </div>
                    <div class="row">
                        <div class="col-md-6 mb-3">
                            <label class="form-label">Categoria</label>
                            <input type="text" class="form-control" name="categoria">
                        </div>
                        <div class="col-md-6 mb-3">
                            <label class="form-label">Preço (R$)</label>
                            <input type="number" class="form-control" name="preco" step="0.01">
                        </div>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Tamanho</label>
                        <select class="form-select" name="tamanho">
                            <option value="pequeno">Pequeno</option>
                            <option value="medio" selected>Médio</option>
                            <option value="grande">Grande</option>
                        </select>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Descrição</label>
                        <textarea class="form-control" name="descricao" rows="3"></textarea>
                    </div>
                    <div class="d-flex gap-2">
                        <button type="submit" class="btn btn-primary flex-fill"><i class="bi bi-save"></i> Salvar</button>
                        <a href="{{ url_for('index') }}" class="btn btn-secondary">Cancelar</a>
                    </div>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}'''

# Template editar.html
editar_html = '''{% extends "base.html" %}
{% block title %}Editar Etiqueta{% endblock %}
{% block content %}
<div class="row justify-content-center">
    <div class="col-md-8">
        <div class="card">
            <div class="card-header bg-warning text-dark">
                <h4 class="mb-0"><i class="bi bi-pencil"></i> Editar Etiqueta</h4>
            </div>
            <div class="card-body">
                <form method="POST">
                    <div class="mb-3">
                        <label class="form-label">Nome do Produto <span class="text-danger">*</span></label>
                        <input type="text" class="form-control" name="nome" value="{{ etiqueta['nome'] }}" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Código <span class="text-danger">*</span></label>
                        <input type="text" class="form-control" name="codigo" value="{{ etiqueta['codigo'] }}" required>
                    </div>
                    <div class="row">
                        <div class="col-md-6 mb-3">
                            <label class="form-label">Categoria</label>
                            <input type="text" class="form-control" name="categoria" value="{{ etiqueta['categoria'] or '' }}">
                        </div>
                        <div class="col-md-6 mb-3">
                            <label class="form-label">Preço (R$)</label>
                            <input type="number" class="form-control" name="preco" step="0.01" value="{{ etiqueta['preco'] or '0' }}">
                        </div>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Tamanho</label>
                        <select class="form-select" name="tamanho">
                            <option value="pequeno" {% if etiqueta['tamanho']=='pequeno' %}selected{% endif %}>Pequeno</option>
                            <option value="medio" {% if etiqueta['tamanho']=='medio' %}selected{% endif %}>Médio</option>
                            <option value="grande" {% if etiqueta['tamanho']=='grande' %}selected{% endif %}>Grande</option>
                        </select>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Descrição</label>
                        <textarea class="form-control" name="descricao" rows="3">{{ etiqueta['descricao'] or '' }}</textarea>
                    </div>
                    <div class="d-flex gap-2">
                        <button type="submit" class="btn btn-warning flex-fill"><i class="bi bi-save"></i> Atualizar</button>
                        <a href="{{ url_for('index') }}" class="btn btn-secondary">Cancelar</a>
                    </div>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}'''

# Salvar arquivos
arquivos = {
    'templates/base.html': base_html,
    'templates/index.html': index_html,
    'templates/criar.html': criar_html,
    'templates/editar.html': editar_html
}

for arquivo, conteudo in arquivos.items():
    with open(arquivo, 'w', encoding='utf-8') as f:
        f.write(conteudo)
    print(f"✅ {arquivo} criado!")

print("\n🎉 TODOS OS TEMPLATES FORAM CRIADOS COM SUCESSO!")
print("\nAgora execute: python app.py")