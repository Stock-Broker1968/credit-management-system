#!/usr/bin/env python3
"""
Sistema de Gestión de Crédito - Servidor Principal
Versión corregida para despliegue en Render
"""

import os
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import logging
from datetime import datetime

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar Flask
app = Flask(__name__, 
           template_folder='ui_templates', 
           static_folder='web_assets')

# Configuración para producción
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'credit-system-hotmart-2024')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar extensiones
db = SQLAlchemy(app)

# Modelos básicos
class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class CreditApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Rutas principales
@app.route('/')
def index():
    """Página principal del simulador educativo"""
    try:
        stats = {
            'total_customers': Customer.query.count(),
            'pending_applications': CreditApplication.query.filter_by(status='pending').count(),
            'active_loans': CreditApplication.query.filter_by(status='approved').count(),
            'risk_alerts': 0
        }
        return render_template('index.html', stats=stats)
    except Exception as e:
        logger.error(f"Error en página principal: {e}")
        # Página de bienvenida básica si hay problemas
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Simulador de Gestión de Crédito - Hotmart</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.0/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container mt-5">
                <div class="jumbotron bg-primary text-white p-5 rounded">
                    <h1 class="display-4">🎓 Simulador de Gestión de Crédito</h1>
                    <p class="lead">Herramienta educativa para el curso de Gestión de Riesgos Financieros</p>
                    <hr class="my-4">
                    <p>Sistema diseñado por un especialista certificado en Gestión de Riesgos</p>
                    <div class="mt-4">
                        <h3>Características del Curso:</h3>
                        <ul class="list-unstyled">
                            <li>✅ Análisis de Riesgo Crediticio</li>
                            <li>✅ Modelos de Scoring</li>
                            <li>✅ Cumplimiento Normativo</li>
                            <li>✅ Casos Prácticos Reales</li>
                        </ul>
                    </div>
                </div>
                
                <div class="row mt-4">
                    <div class="col-md-4">
                        <div class="card">
                            <div class="card-body text-center">
                                <h5 class="card-title">Simulación de Crédito</h5>
                                <p class="card-text">Practica evaluaciones de riesgo con casos reales</p>
                                <button class="btn btn-primary" onclick="alert('Funcionalidad disponible próximamente')">Comenzar</button>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card">
                            <div class="card-body text-center">
                                <h5 class="card-title">Análisis de Riesgo</h5>
                                <p class="card-text">Herramientas de evaluación crediticia</p>
                                <button class="btn btn-success" onclick="alert('Funcionalidad disponible próximamente')">Analizar</button>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card">
                            <div class="card-body text-center">
                                <h5 class="card-title">Reportes</h5>
                                <p class="card-text">Generación de informes profesionales</p>
                                <button class="btn btn-info" onclick="alert('Funcionalidad disponible próximamente')">Generar</button>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="row mt-5">
                    <div class="col-12">
                        <div class="alert alert-info">
                            <h5>📚 Sobre el Instructor</h5>
                            <p class="mb-0">
                                Profesional con Maestría en Gestión de Riesgos, especialidad en Finanzas,
                                certificado como Oficial de Cumplimiento y Evaluador de Competencias.
                                Experto en administración de riesgos, normatividad financiera y auditoría.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

@app.route('/dashboard')
def dashboard():
    """Dashboard del simulador"""
    return "<h1>Dashboard - Simulador de Crédito</h1><p>Herramienta educativa para Hotmart</p>"

@app.route('/health')
def health():
    """Health check para Render"""
    return jsonify({"status": "ok", "service": "credit-management-system"})

# Crear tablas
def create_tables():
    try:
        with app.app_context():
            db.create_all()
            logger.info("✅ Base de datos inicializada")
    except Exception as e:
        logger.error(f"Error creando tablas: {e}")

if __name__ == '__main__':
    # Inicializar base de datos
    create_tables()
    
    # Configurar para producción
    port = int(os.environ.get('PORT', 5000))
    host = '0.0.0.0'
    
    logger.info(f"🚀 Iniciando Simulador de Crédito para Hotmart")
    logger.info(f"🌐 Servidor en puerto: {port}")
    
    app.run(host=host, port=port, debug=False)
