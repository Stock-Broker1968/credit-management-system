#!/usr/bin/env python3
"""
Simulador de Gestión de Crédito - Herramienta Educativa Hotmart
Versión simplificada para despliegue en Render
"""

import os
from flask import Flask, render_template

# Inicializar Flask
app = Flask(__name__)

# Configuración básica
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'simulador-credito-hotmart-2024')

@app.route('/')
def index():
    """Página principal del simulador educativo"""
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Simulador de Gestión de Crédito - Hotmart</title>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.0/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        <style>
            .hero-section {
                background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                color: white;
                padding: 4rem 2rem;
                border-radius: 15px;
                margin-bottom: 2rem;
            }
            .feature-card {
                transition: transform 0.3s ease;
                border: none;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                border-radius: 10px;
            }
            .feature-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 8px 15px rgba(0,0,0,0.2);
            }
            .instructor-badge {
                background: rgba(255,255,255,0.1);
                padding: 2rem;
                border-radius: 10px;
                margin-top: 2rem;
            }
        </style>
    </head>
    <body>
        <!-- Navegación -->
        <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
            <div class="container">
                <a class="navbar-brand" href="#">
                    <i class="fas fa-graduation-cap me-2"></i>
                    Simulador de Crédito
                </a>
                <div class="navbar-nav ms-auto">
                    <span class="navbar-text">
                        <i class="fas fa-user-shield"></i> Curso Profesional
                    </span>
                </div>
            </div>
        </nav>

        <div class="container mt-4">
            <!-- Hero Section -->
            <div class="hero-section text-center">
                <h1 class="display-4 mb-3">
                    <i class="fas fa-chart-line me-3"></i>
                    Simulador de Gestión de Crédito
                </h1>
                <p class="lead mb-3">
                    Herramienta educativa para el curso de <strong>"Gestión Avanzada de Riesgos Crediticios"</strong>
                </p>
                <p class="mb-4">
                    Desarrollado por un especialista certificado con Maestría en Gestión de Riesgos
                </p>
                <button class="btn btn-light btn-lg" onclick="scrollToFeatures()">
                    <i class="fas fa-play me-2"></i>
                    Explorar Herramientas
                </button>
            </div>

            <!-- Estadísticas -->
            <div class="row mb-5">
                <div class="col-md-3">
                    <div class="card bg-primary text-white feature-card">
                        <div class="card-body text-center">
                            <i class="fas fa-users fa-3x mb-3"></i>
                            <h3>500+</h3>
                            <p>Estudiantes Activos</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card bg-success text-white feature-card">
                        <div class="card-body text-center">
                            <i class="fas fa-calculator fa-3x mb-3"></i>
                            <h3>1,200+</h3>
                            <p>Simulaciones Realizadas</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card bg-info text-white feature-card">
                        <div class="card-body text-center">
                            <i class="fas fa-book fa-3x mb-3"></i>
                            <h3>5</h3>
                            <p>Módulos Disponibles</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card bg-warning text-white feature-card">
                        <div class="card-body text-center">
                            <i class="fas fa-star fa-3x mb-3"></i>
                            <h3>720</h3>
                            <p>Score Promedio</p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Características del Curso -->
            <div id="features" class="row mb-5">
                <div class="col-12 text-center mb-4">
                    <h2><i class="fas fa-lightbulb text-warning me-2"></i> ¿Qué Aprenderás?</h2>
                </div>
                
                <div class="col-md-4">
                    <div class="card feature-card h-100">
                        <div class="card-body text-center">
                            <i class="fas fa-balance-scale fa-3x text-primary mb-3"></i>
                            <h4>Evaluación de Riesgo</h4>
                            <p>Aprende a evaluar el riesgo crediticio usando modelos profesionales y metodologías probadas en la industria financiera.</p>
                            <button class="btn btn-primary" onclick="showDemo('risk')">Ver Demo</button>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-4">
                    <div class="card feature-card h-100">
                        <div class="card-body text-center">
                            <i class="fas fa-calculator fa-3x text-success mb-3"></i>
                            <h4>Scoring Crediticio</h4>
                            <p>Domina las técnicas de scoring crediticio, factores de evaluación y cálculos utilizados por instituciones financieras.</p>
                            <button class="btn btn-success" onclick="showDemo('scoring')">Ver Demo</button>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-4">
                    <div class="card feature-card h-100">
                        <div class="card-body text-center">
                            <i class="fas fa-shield-alt fa-3x text-info mb-3"></i>
                            <h4>Cumplimiento Normativo</h4>
                            <p>Conoce las regulaciones financieras, mejores prácticas y requisitos de cumplimiento en gestión de riesgos.</p>
                            <button class="btn btn-info" onclick="showDemo('compliance')">Ver Demo</button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Simulador Interactivo -->
            <div class="row mb-5">
                <div class="col-12">
                    <div class="card feature-card">
                        <div class="card-header bg-gradient text-white" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
                            <h3 class="mb-0">
                                <i class="fas fa-laptop-code me-2"></i>
                                Simulador Interactivo de Crédito
                            </h3>
                        </div>
                        <div class="card-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <h5>Practica con Casos Reales</h5>
                                    <ul class="list-unstyled">
                                        <li><i class="fas fa-check text-success me-2"></i> Evaluación paso a paso</li>
                                        <li><i class="fas fa-check text-success me-2"></i> Explicación de cada factor</li>
                                        <li><i class="fas fa-check text-success me-2"></i> Reportes detallados</li>
                                        <li><i class="fas fa-check text-success me-2"></i> Casos de estudio reales</li>
                                    </ul>
                                    <button class="btn btn-primary btn-lg" onclick="startSimulator()">
                                        <i class="fas fa-play me-2"></i>
                                        Comenzar Simulación
                                    </button>
                                </div>
                                <div class="col-md-6">
                                    <div id="demo-area" class="bg-light p-4 rounded">
                                        <h6>Demo: Evaluación de Crédito</h6>
                                        <div class="mb-2">
                                            <strong>Cliente:</strong> María González
                                        </div>
                                        <div class="mb-2">
                                            <strong>Ingresos:</strong> $45,000 mensuales
                                        </div>
                                        <div class="mb-2">
                                            <strong>Historial:</strong> Bueno
                                        </div>
                                        <div class="mb-3">
                                            <strong>Monto solicitado:</strong> $300,000
                                        </div>
                                        <div class="text-center">
                                            <div class="bg-success text-white rounded p-3">
                                                <h4 class="mb-0">Score: 720</h4>
                                                <small>Riesgo Bajo - APROBADO</small>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Instructor -->
            <div class="instructor-badge bg-gradient text-white text-center" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
                <h3><i class="fas fa-user-tie me-2"></i> Tu Instructor</h3>
                <p class="lead">Profesional certificado con amplia experiencia en el sector financiero</p>
                <div class="row">
                    <div class="col-md-3">
                        <i class="fas fa-graduation-cap fa-2x mb-2"></i>
                        <p>Maestría en Gestión de Riesgos</p>
                    </div>
                    <div class="col-md-3">
                        <i class="fas fa-certificate fa-2x mb-2"></i>
                        <p>Oficial de Cumplimiento Certificado</p>
                    </div>
                    <div class="col-md-3">
                        <i class="fas fa-chart-line fa-2x mb-2"></i>
                        <p>Especialista en Finanzas</p>
                    </div>
                    <div class="col-md-3">
                        <i class="fas fa-cogs fa-2x mb-2"></i>
                        <p>Experto en IA Financiera</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Scripts -->
        <script src="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.0/js/bootstrap.bundle.min.js"></script>
        <script>
            function scrollToFeatures() {
                document.getElementById('features').scrollIntoView({behavior: 'smooth'});
            }
            
            function showDemo(type) {
                const demoArea = document.getElementById('demo-area');
                let content = '';
                
                switch(type) {
                    case 'risk':
                        content = `
                            <h6>Demo: Análisis de Riesgo</h6>
                            <div class="progress mb-2">
                                <div class="progress-bar bg-success" style="width: 75%">Ingresos: 75/100</div>
                            </div>
                            <div class="progress mb-2">
                                <div class="progress-bar bg-warning" style="width: 60%">Historial: 60/100</div>
                            </div>
                            <div class="progress mb-3">
                                <div class="progress-bar bg-info" style="width: 85%">Estabilidad: 85/100</div>
                            </div>
                            <div class="alert alert-success">Riesgo: BAJO</div>
                        `;
                        break;
                    case 'scoring':
                        content = `
                            <h6>Demo: Cálculo de Score</h6>
                            <div class="mb-2">• Base: 500 puntos</div>
                            <div class="mb-2">• Ingresos: +150 puntos</div>
                            <div class="mb-2">• Historial: +100 puntos</div>
                            <div class="mb-2">• Estabilidad: +70 puntos</div>
                            <hr>
                            <div class="text-center">
                                <h4 class="text-success">Score Final: 820</h4>
                            </div>
                        `;
                        break;
                    case 'compliance':
                        content = `
                            <h6>Demo: Verificación de Cumplimiento</h6>
                            <div class="mb-2">✅ Documentos KYC completos</div>
                            <div class="mb-2">✅ Verificación de identidad</div>
                            <div class="mb-2">✅ Validación de ingresos</div>
                            <div class="mb-2">✅ Consulta en listas restrictivas</div>
                            <div class="alert alert-success mt-3">Estado: COMPLIANT</div>
                        `;
                        break;
                }
                
                demoArea.innerHTML = content;
            }
            
            function startSimulator() {
                alert('¡Simulador próximamente disponible!\\n\\nEsta herramienta será parte del curso completo de Gestión de Riesgos Financieros en Hotmart.');
            }
        </script>
    </body>
    </html>
    """

@app.route('/health')
def health():
    """Health check para Render"""
    return {"status": "ok", "service": "simulador-credito-hotmart"}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
