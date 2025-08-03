#!/usr/bin/env python3
"""
Sistema de Gestión de Crédito - Servidor Principal
Diseñado para profesionales en gestión de riesgos financieros
"""

import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
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

# Configuración de la aplicación
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///data/database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar extensiones
db = SQLAlchemy(app)

# Importar módulos después de inicializar db para evitar importaciones circulares
try:
    from modules.core.customer_management import Customer
    from modules.core.credit_application import CreditApplication
    from modules.core.loan_management import Loan
    from modules.analysis.risk_analysis import RiskAnalyzer
    from modules.analysis.scoring import CreditScoring
    from modules.utils.database import init_database
except ImportError as e:
    logger.warning(f"Algunos módulos no están disponibles aún: {e}")
    # Definir modelos básicos temporalmente
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
    """Página principal del sistema"""
    try:
        # Obtener estadísticas básicas
        total_customers = Customer.query.count()
        pending_applications = CreditApplication.query.filter_by(status='pending').count()
        
        stats = {
            'total_customers': total_customers,
            'pending_applications': pending_applications,
            'active_loans': 0,  # Se implementará con el módulo de préstamos
            'risk_alerts': 0    # Se implementará con el análisis de riesgo
        }
        
        return render_template('index.html', stats=stats)
    except Exception as e:
        logger.error(f"Error en página principal: {e}")
        return render_template('index.html', stats={
            'total_customers': 0,
            'pending_applications': 0,
            'active_loans': 0,
            'risk_alerts': 0
        })

@app.route('/dashboard')
def dashboard():
    """Dashboard principal de gestión de riesgos"""
    return render_template('dashboard/main_dashboard.html')

@app.route('/customers')
def customers():
    """Gestión de clientes"""
    customers_list = Customer.query.all()
    return render_template('forms/customer_form.html', customers=customers_list)

@app.route('/applications')
def applications():
    """Gestión de solicitudes de crédito"""
    applications_list = CreditApplication.query.all()
    return render_template('forms/credit_application.html', applications=applications_list)

@app.route('/risk-analysis')
def risk_analysis():
    """Análisis de riesgo crediticio"""
    return render_template('reports/risk_report.html')

@app.route('/compliance')
def compliance():
    """Reportes de cumplimiento normativo"""
    return render_template('reports/compliance_report.html')

# API endpoints
@app.route('/api/customer', methods=['POST'])
def create_customer():
    """Crear nuevo cliente"""
    try:
        data = request.get_json()
        
        customer = Customer(
            name=data.get('name'),
            email=data.get('email')
        )
        
        db.session.add(customer)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Cliente creado exitosamente',
            'customer_id': customer.id
        }), 201
        
    except Exception as e:
        logger.error(f"Error creando cliente: {e}")
        return jsonify({
            'success': False,
            'message': 'Error al crear cliente'
        }), 400

@app.route('/api/credit-application', methods=['POST'])
def create_credit_application():
    """Crear nueva solicitud de crédito"""
    try:
        data = request.get_json()
        
        application = CreditApplication(
            customer_id=data.get('customer_id'),
            amount=data.get('amount')
        )
        
        db.session.add(application)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Solicitud de crédito creada exitosamente',
            'application_id': application.id
        }), 201
        
    except Exception as e:
        logger.error(f"Error creando solicitud: {e}")
        return jsonify({
            'success': False,
            'message': 'Error al crear solicitud de crédito'
        }), 400

@app.route('/api/risk-score/<int:customer_id>')
def get_risk_score(customer_id):
    """Obtener score de riesgo de un cliente"""
    try:
        # Implementar cuando esté disponible el módulo de scoring
        return jsonify({
            'customer_id': customer_id,
            'risk_score': 750,  # Valor temporal
            'risk_level': 'medium',
            'factors': ['Historial crediticio', 'Ingresos estables', 'Antiguedad laboral']
        })
    except Exception as e:
        logger.error(f"Error calculando risk score: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

# Manejadores de errores
@app.errorhandler(404)
def not_found(error):
    return render_template('base.html', error="Página no encontrada"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('base.html', error="Error interno del servidor"), 500

# Funciones de inicialización
def create_tables():
    """Crear tablas de la base de datos"""
    try:
        with app.app_context():
            db.create_all()
            logger.info("Tablas de base de datos creadas exitosamente")
    except Exception as e:
        logger.error(f"Error creando tablas: {e}")

def init_app():
    """Inicializar la aplicación"""
    logger.info("Iniciando Sistema de Gestión de Crédito...")
    
    # Crear directorio de datos si no existe
    os.makedirs('data', exist_ok=True)
    os.makedirs('reports/generated', exist_ok=True)
    
    # Crear tablas
    create_tables()
    
    logger.info("Sistema inicializado correctamente")

if __name__ == '__main__':
    # Inicializar aplicación
    init_app()
    
    # Configurar servidor
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    logger.info(f"Servidor ejecutándose en http://{host}:{port}")
    logger.info("Sistema de Gestión de Crédito - Listo para usar")
    
    # Ejecutar servidor
    app.run(host=host, port=port, debug=debug)