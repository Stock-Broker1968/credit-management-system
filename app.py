#!/usr/bin/env python3
"""
Simulador Completo de Gestión de Crédito - Hotmart
Con Panel de Administración para Reglas de Negocio
"""

import os
import json
import math
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'simulador-credito-hotmart-2024')

# Configuración de reglas de negocio (ajustables por admin)
REGLAS_NEGOCIO = {
    'SCORE_MINIMO_APROBACION': 250,  # Reducido para más aprobaciones
    'INGRESO_MINIMO': 8000,
    'MONTO_MAXIMO_CREDITO': 150000,
    'PLAZOS_AUTORIZADOS': [3, 6, 9, 12],
    'TASA_MINIMA': 0.22,
    'TASA_MAXIMA': 0.38,
    'TDSR_MAXIMO': 0.45,  # Aumentado para más flexibilidad
    'FICO_MINIMO_APROBACION': 500,  # Reducido para más aprobaciones
    'FACTOR_SCORING': 1.2  # Multiplicador para aumentar scores
}

class ModeloScoringCrediticio:
    """Modelo de scoring crediticio integrado con reglas ajustables"""
    
    def __init__(self):
        self.reglas = REGLAS_NEGOCIO.copy()
    
    def actualizar_reglas(self, nuevas_reglas):
        """Actualiza las reglas de negocio"""
        self.reglas.update(nuevas_reglas)
    
    def calcular_variables_generales(self, datos):
        puntos = 0
        detalles = []
        
        # Antigüedad Domicilio (30 puntos)
        antiguedad_domicilio = float(datos.get('antiguedad_domicilio', 0))
        if antiguedad_domicilio >= 6:
            puntos_domicilio = 30
        elif antiguedad_domicilio >= 3:
            puntos_domicilio = 25
        elif antiguedad_domicilio >= 1:
            puntos_domicilio = 15
        else:
            puntos_domicilio = 5  # Mínimo aumentado
        
        puntos += puntos_domicilio
        detalles.append({
            'factor': 'Antigüedad en Domicilio',
            'valor': f"{antiguedad_domicilio} años",
            'puntos': puntos_domicilio,
            'maximo': 30
        })
        
        # Estado Civil (20 puntos)
        estado_civil = datos.get('estado_civil', 'soltero')
        puntos_civil = 20 if estado_civil == 'casado' else 15  # Aumentado base
        puntos += puntos_civil
        detalles.append({
            'factor': 'Estado Civil',
            'valor': estado_civil.replace('_', ' ').title(),
            'puntos': puntos_civil,
            'maximo': 20
        })
        
        # Dependientes (15 puntos)
        dependientes = int(datos.get('dependientes', 0))
        puntos_dep = 15 if dependientes <= 2 else 10  # Aumentado penalización menor
        puntos += puntos_dep
        detalles.append({
            'factor': 'Dependientes',
            'valor': str(dependientes),
            'puntos': puntos_dep,
            'maximo': 15
        })
        
        # Nivel de Estudios (20 puntos)
        nivel_estudios = datos.get('nivel_estudios', 'secundaria')
        estudios_puntos = {
            'universidad': 20,
            'preparatoria': 17,  # Aumentado
            'secundaria': 14,    # Aumentado
            'primaria': 10       # Aumentado
        }
        puntos_estudios = estudios_puntos.get(nivel_estudios, 10)
        puntos += puntos_estudios
        detalles.append({
            'factor': 'Nivel de Estudios',
            'valor': nivel_estudios.title(),
            'puntos': puntos_estudios,
            'maximo': 20
        })
        
        # Ocupación (25 puntos)
        ocupacion = datos.get('ocupacion', 'empleado_privado')
        ocupacion_puntos = {
            'empleado_publico': 25,
            'empleado_privado': 22,  # Aumentado
            'independiente': 18,     # Aumentado
            'comerciante': 15        # Aumentado
        }
        puntos_ocupacion = ocupacion_puntos.get(ocupacion, 15)
        puntos += puntos_ocupacion
        detalles.append({
            'factor': 'Ocupación',
            'valor': ocupacion.replace('_', ' ').title(),
            'puntos': puntos_ocupacion,
            'maximo': 25
        })
        
        # Antigüedad Empleo (20 puntos)
        antiguedad_empleo = float(datos.get('antiguedad_empleo', 0))
        if antiguedad_empleo >= 3:
            puntos_emp = 20
        elif antiguedad_empleo >= 1:
            puntos_emp = 16  # Aumentado
        else:
            puntos_emp = 10  # Aumentado base
        
        puntos += puntos_emp
        detalles.append({
            'factor': 'Antigüedad en Empleo',
            'valor': f"{antiguedad_empleo} años",
            'puntos': puntos_emp,
            'maximo': 20
        })
        
        # Edad (30 puntos)
        edad = int(datos.get('edad', 25))
        if edad > 45:
            puntos_edad = 30
        elif edad >= 35:
            puntos_edad = 28  # Aumentado
        elif edad >= 25:
            puntos_edad = 25  # Aumentado
        else:
            puntos_edad = 20  # Aumentado base
        
        puntos += puntos_edad
        detalles.append({
            'factor': 'Edad',
            'valor': f"{edad} años",
            'puntos': puntos_edad,
            'maximo': 30
        })
        
        # Validaciones (20 puntos)
        comprobante_domicilio = datos.get('comprobante_domicilio') == 'si'
        comprobante_ingresos = datos.get('comprobante_ingresos') == 'si'
        puntos_validaciones = 0
        if comprobante_domicilio and comprobante_ingresos:
            puntos_validaciones = 20
        elif comprobante_domicilio or comprobante_ingresos:
            puntos_validaciones = 15  # Aumentado
        else:
            puntos_validaciones = 8   # Base para sin documentos
        
        puntos += puntos_validaciones
        detalles.append({
            'factor': 'Validaciones Documentales',
            'valor': f"Domicilio: {'Sí' if comprobante_domicilio else 'No'}, Ingresos: {'Sí' if comprobante_ingresos else 'No'}",
            'puntos': puntos_validaciones,
            'maximo': 20
        })
        
        # Aplicar factor de scoring
        puntos = int(puntos * self.reglas['FACTOR_SCORING'])
        
        return {
            'categoria': 'Variables Generales',
            'puntos_obtenidos': min(puntos, 180),  # Máximo 180
            'puntos_maximos': 180,
            'peso': 0.30,
            'puntos_ponderados': min(puntos, 180) * 0.30,
            'detalles': detalles
        }
    
    def calcular_historial_crediticio(self, datos):
        puntos = 0
        detalles = []
        
        # Última Calificación (50 puntos)
        ultima_calificacion = int(datos.get('ultima_calificacion', 2))
        if ultima_calificacion == 1:
            puntos_calif = 50
        elif ultima_calificacion == 2:
            puntos_calif = 40  # Aumentado
        elif ultima_calificacion == 3:
            puntos_calif = 25  # Aumentado
        else:
            puntos_calif = 15  # Aumentado
        
        puntos += puntos_calif
        detalles.append({
            'factor': 'Última Calificación',
            'valor': str(ultima_calificacion),
            'puntos': puntos_calif,
            'maximo': 50
        })
        
        # Número de Consultas (30 puntos)
        num_consultas = int(datos.get('numero_consultas', 0))
        if num_consultas <= 5:
            puntos_consultas = 30
        elif num_consultas <= 10:
            puntos_consultas = 25  # Aumentado
        elif num_consultas <= 15:
            puntos_consultas = 20  # Nueva banda
        else:
            puntos_consultas = 15  # Aumentado
        
        puntos += puntos_consultas
        detalles.append({
            'factor': 'Número de Consultas',
            'valor': str(num_consultas),
            'puntos': puntos_consultas,
            'maximo': 30
        })
        
        # FICO Score (50 puntos)
        fico_score = int(datos.get('fico_score', 650))
        if fico_score >= 750:
            puntos_fico = 50
        elif fico_score >= 700:
            puntos_fico = 45  # Aumentado
        elif fico_score >= 650:
            puntos_fico = 38  # Aumentado
        elif fico_score >= 600:
            puntos_fico = 30  # Aumentado
        elif fico_score >= 550:
            puntos_fico = 25  # Aumentado
        else:
            puntos_fico = 18  # Aumentado base
        
        puntos += puntos_fico
        detalles.append({
            'factor': 'FICO Score',
            'valor': str(fico_score),
            'puntos': puntos_fico,
            'maximo': 50
        })
        
        # Aplicar factor de scoring
        puntos = int(puntos * self.reglas['FACTOR_SCORING'])
        
        return {
            'categoria': 'Historial Crediticio',
            'puntos_obtenidos': min(puntos, 130),
            'puntos_maximos': 130,
            'peso': 0.30,
            'puntos_ponderados': min(puntos, 130) * 0.30,
            'detalles': detalles
        }
    
    def calcular_capacidad_pago(self, datos):
        puntos = 0
        detalles = []
        
        # Tipo de Comprobante (35 puntos)
        tipo_comprobante = datos.get('tipo_comprobante', 'otros')
        if tipo_comprobante in ['nomina', 'estados_cuenta']:
            puntos_comprobante = 35
        elif tipo_comprobante == 'declaracion':
            puntos_comprobante = 30  # Aumentado
        else:
            puntos_comprobante = 20  # Aumentado
        
        puntos += puntos_comprobante
        detalles.append({
            'factor': 'Tipo de Comprobante',
            'valor': tipo_comprobante.replace('_', ' ').title(),
            'puntos': puntos_comprobante,
            'maximo': 35
        })
        
        # Estabilidad (25 puntos)
        ocupacion = datos.get('ocupacion', 'empleado_privado')
        if ocupacion == 'empleado_publico':
            puntos_estabilidad = 25
        elif ocupacion == 'empleado_privado':
            puntos_estabilidad = 22  # Aumentado
        else:
            puntos_estabilidad = 18  # Aumentado
        
        puntos += puntos_estabilidad
        detalles.append({
            'factor': 'Estabilidad de Ingresos',
            'valor': ocupacion.replace('_', ' ').title(),
            'puntos': puntos_estabilidad,
            'maximo': 25
        })
        
        # TDSR (30 puntos)
        ingresos_mensuales = float(datos.get('ingresos_mensuales', self.reglas['INGRESO_MINIMO']))
        deuda_mensual = float(datos.get('deuda_mensual', 0))
        tdsr = deuda_mensual / ingresos_mensuales if ingresos_mensuales > 0 else 0
        
        if tdsr < 0.25:
            puntos_tdsr = 30
        elif tdsr <= 0.35:
            puntos_tdsr = 28  # Aumentado
        elif tdsr <= 0.45:
            puntos_tdsr = 25  # Aumentado
        else:
            puntos_tdsr = 15  # Base para casos extremos
        
        puntos += puntos_tdsr
        detalles.append({
            'factor': 'TDSR (Ratio Deuda-Ingreso)',
            'valor': f"{tdsr:.1%}",
            'puntos': puntos_tdsr,
            'maximo': 30
        })
        
        # Aplicar factor de scoring
        puntos = int(puntos * self.reglas['FACTOR_SCORING'])
        
        return {
            'categoria': 'Capacidad de Pago',
            'puntos_obtenidos': min(puntos, 90),
            'puntos_maximos': 90,
            'peso': 0.40,
            'puntos_ponderados': min(puntos, 90) * 0.40,
            'detalles': detalles,
            'tdsr': tdsr
        }
    
    def calcular_condiciones_credito(self, score_final, ingresos_mensuales, tdsr):
        # Monto máximo
        if score_final >= 350:
            factor_monto = 4.0  # Aumentado
        elif score_final >= 300:
            factor_monto = 3.5  # Aumentado
        elif score_final >= 250:
            factor_monto = 3.0  # Aumentado
        else:
            factor_monto = 2.5  # Aumentado
        
        monto_calculado = ingresos_mensuales * factor_monto * (1 - min(tdsr, 0.4))
        monto_final = min(monto_calculado, self.reglas['MONTO_MAXIMO_CREDITO'])
        monto_final = max(monto_final, 10000)  # Mínimo más alto
        
        # Tasa de interés
        if score_final >= 350:
            tasa = self.reglas['TASA_MINIMA']
        elif score_final >= 300:
            tasa = self.reglas['TASA_MINIMA'] + 0.04  # Reducido
        elif score_final >= 250:
            tasa = self.reglas['TASA_MINIMA'] + 0.08  # Reducido
        else:
            tasa = self.reglas['TASA_MINIMA'] + 0.12  # Reducido
        
        tasa = min(tasa, self.reglas['TASA_MAXIMA'])
        
        # Calcular opciones de plazo
        opciones_plazo = []
        for plazo in self.reglas['PLAZOS_AUTORIZADOS']:
            tasa_mensual = tasa / 12
            if tasa_mensual > 0:
                pago_mensual = monto_final * (tasa_mensual * (1 + tasa_mensual)**plazo) / ((1 + tasa_mensual)**plazo - 1)
            else:
                pago_mensual = monto_final / plazo
            
            porcentaje_ingreso = (pago_mensual / ingresos_mensuales) * 100
            
            opciones_plazo.append({
                'plazo': plazo,
                'pago_mensual': round(pago_mensual, 2),
                'porcentaje_ingreso': round(porcentaje_ingreso, 1),
                'factible': pago_mensual <= (ingresos_mensuales * 0.35)  # Más flexible
            })
        
        return {
            'monto_aprobado': round(monto_final, -2),
            'tasa_anual': tasa,
            'opciones_plazo': opciones_plazo
        }
    
    def evaluar_solicitud(self, datos):
        # Validaciones básicas
        ingresos = float(datos.get('ingresos_mensuales', 0))
        if ingresos < self.reglas['INGRESO_MINIMO']:
            return {
                'aprobado': False,
                'razon': f'Ingresos insuficientes (mínimo ${self.reglas["INGRESO_MINIMO"]:,})',
                'score': 0
            }
        
        fico = int(datos.get('fico_score', 600))
        if fico < self.reglas['FICO_MINIMO_APROBACION']:
            return {
                'aprobado': False,
                'razon': f'FICO Score insuficiente (mínimo {self.reglas["FICO_MINIMO_APROBACION"]})',
                'score': 0
            }
        
        # Calcular categorías
        generales = self.calcular_variables_generales(datos)
        historial = self.calcular_historial_crediticio(datos)
        capacidad = self.calcular_capacidad_pago(datos)
        
        # Score final
        score_final = (
            generales['puntos_ponderados'] +
            historial['puntos_ponderados'] +
            capacidad['puntos_ponderados']
        )
        
        # Verificar TDSR
        if capacidad['tdsr'] > self.reglas['TDSR_MAXIMO']:
            return {
                'aprobado': False,
                'razon': f'TDSR excesivo ({capacidad["tdsr"]:.1%}, máximo {self.reglas["TDSR_MAXIMO"]:.1%})',
                'score': score_final
            }
        
        # Verificar score mínimo
        if score_final < self.reglas['SCORE_MINIMO_APROBACION']:
            return {
                'aprobado': False,
                'razon': f'Score insuficiente ({score_final:.1f}, mínimo {self.reglas["SCORE_MINIMO_APROBACION"]})',
                'score': score_final
            }
        
        # Calcular condiciones
        condiciones = self.calcular_condiciones_credito(score_final, ingresos, capacidad['tdsr'])
        
        # Nivel de riesgo
        if score_final >= 350:
            nivel_riesgo = 'Bajo'
            color = 'success'
        elif score_final >= 300:
            nivel_riesgo = 'Medio'
            color = 'warning'
        else:
            nivel_riesgo = 'Alto'
            color = 'danger'
        
        return {
            'aprobado': True,
            'score': round(score_final, 1),
            'nivel_riesgo': nivel_riesgo,
            'color_riesgo': color,
            'monto_aprobado': condiciones['monto_aprobado'],
            'tasa_anual': condiciones['tasa_anual'],
            'opciones_plazo': condiciones['opciones_plazo'],
            'desglose': {
                'generales': generales,
                'historial': historial,
                'capacidad': capacidad
            },
            'tdsr': capacidad['tdsr'],
            'fecha': datetime.now().strftime('%d/%m/%Y %H:%M')
        }

# Instancia del modelo
modelo = ModeloScoringCrediticio()

# Casos de estudio predefinidos
CASOS_ESTUDIO = {
    'perfil_alto': {
        'nombre': 'María González - Empleada Pública',
        'descripcion': 'Funcionaria con estabilidad laboral y buen historial',
        'datos': {
            'ingresos_mensuales': '35000',
            'edad': '38',
            'estado_civil': 'casado',
            'dependientes': '2',
            'nivel_estudios': 'universidad',
            'ocupacion': 'empleado_publico',
            'antiguedad_empleo': '5',
            'antiguedad_domicilio': '8',
            'comprobante_domicilio': 'si',
            'comprobante_ingresos': 'si',
            'fico_score': '720',
            'ultima_calificacion': '1',
            'numero_consultas': '2',
            'tipo_comprobante': 'nomina',
            'deuda_mensual': '8000'
        }
    },
    'perfil_medio': {
        'nombre': 'Carlos Rodríguez - Empleado Privado',
        'descripcion': 'Profesional con historial regular',
        'datos': {
            'ingresos_mensuales': '22000',
            'edad': '32',
            'estado_civil': 'soltero',
            'dependientes': '1',
            'nivel_estudios': 'preparatoria',
            'ocupacion': 'empleado_privado',
            'antiguedad_empleo': '3',
            'antiguedad_domicilio': '4',
            'comprobante_domicilio': 'si',
            'comprobante_ingresos': 'si',
            'fico_score': '650',
            'ultima_calificacion': '2',
            'numero_consultas': '6',
            'tipo_comprobante': 'nomina',
            'deuda_mensual': '5500'
        }
    },
    'perfil_basico': {
        'nombre': 'Ana Martínez - Trabajadora Independiente',
        'descripcion': 'Profesional independiente con historial limitado',
        'datos': {
            'ingresos_mensuales': '15000',
            'edad': '28',
            'estado_civil': 'soltero',
            'dependientes': '0',
            'nivel_estudios': 'universidad',
            'ocupacion': 'independiente',
            'antiguedad_empleo': '2',
            'antiguedad_domicilio': '2',
            'comprobante_domicilio': 'si',
            'comprobante_ingresos': 'no',
            'fico_score': '600',
            'ultima_calificacion': '2',
            'numero_consultas': '8',
            'tipo_comprobante': 'declaracion',
            'deuda_mensual': '3000'
        }
    }
}

# Funciones de autenticación admin
def is_admin():
    return session.get('admin_logged_in', False)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == 'RAG123':
            session['admin_logged_in'] = True
            return redirect(url_for('admin_reglas'))
        else:
            return render_template_string(TEMPLATE_ADMIN_LOGIN, error="Contraseña incorrecta")
    
    return render_template_string(TEMPLATE_ADMIN_LOGIN)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('home'))

@app.route('/admin/reglas')
def admin_reglas():
    if not is_admin():
        return redirect(url_for('admin_login'))
    
    return render_template_string(TEMPLATE_ADMIN_REGLAS, reglas=modelo.reglas)

@app.route('/api/admin/actualizar-reglas', methods=['POST'])
def actualizar_reglas():
    if not is_admin():
        return jsonify({'success': False, 'error': 'No autorizado'}), 401
    
    try:
        nuevas_reglas = request.get_json()
        
        # Validar y convertir tipos
        reglas_validadas = {}
        for key, value in nuevas_reglas.items():
            if key in REGLAS_NEGOCIO:
                if key == 'PLAZOS_AUTORIZADOS':
                    reglas_validadas[key] = [int(x) for x in str(value).split(',')]
                elif isinstance(REGLAS_NEGOCIO[key], int):
                    reglas_validadas[key] = int(value)
                elif isinstance(REGLAS_NEGOCIO[key], float):
                    reglas_validadas[key] = float(value)
                else:
                    reglas_validadas[key] = value
        
        # Actualizar reglas globales y del modelo
        REGLAS_NEGOCIO.update(reglas_validadas)
        modelo.actualizar_reglas(reglas_validadas)
        
        return jsonify({'success': True, 'message': 'Reglas actualizadas correctamente'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

# Rutas principales
@app.route('/')
def home():
    return render_template_string(TEMPLATE_HOME)

@app.route('/simulador')
def simulador():
    return render_template_string(TEMPLATE_SIMULADOR)

@app.route('/casos-estudio')
def casos_estudio():
    return render_template_string(TEMPLATE_CASOS, casos=CASOS_ESTUDIO)

@app.route('/api/evaluar', methods=['POST'])
def evaluar_credito():
    try:
        datos = request.get_json()
        resultado = modelo.evaluar_solicitud(datos)
        return jsonify({'success': True, 'data': resultado})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/caso/<caso_id>')
def obtener_caso(caso_id):
    if caso_id in CASOS_ESTUDIO:
        return jsonify(CASOS_ESTUDIO[caso_id])
    return jsonify({'error': 'Caso no encontrado'}), 404

# Template para login de admin
TEMPLATE_ADMIN_LOGIN = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Acceso Administrador</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <div class="container">
        <div class="row justify-content-center mt-5">
            <div class="col-md-4">
                <div class="card">
                    <div class="card-header bg-danger text-white text-center">
                        <h4><i class="fas fa-shield-alt me-2"></i>Acceso Administrador</h4>
                    </div>
                    <div class="card-body">
                        {% if error %}
                        <div class="alert alert-danger">{{ error }}</div>
                        {% endif %}
                        
                        <form method="POST">
                            <div class="mb-3">
                                <label class="form-label">Contraseña de Administrador:</label>
                                <input type="password" class="form-control" name="password" required>
                            </div>
                            <div class="d-grid">
                                <button type="submit" class="btn btn-danger">
                                    <i class="fas fa-sign-in-alt me-2"></i>Acceder
                                </button>
                            </div>
                        </form>
                        
                        <div class="text-center mt-3">
                            <a href="/" class="btn btn-outline-secondary btn-sm">
                                <i class="fas fa-arrow-left me-1"></i>Volver al Simulador
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
'''

# Template para reglas de negocio
TEMPLATE_ADMIN_REGLAS = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reglas de Negocio - Administrador</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-dark bg-danger">
        <div class="container">
            <span class="navbar-brand">
                <i class="fas fa-cogs me-2"></i>Panel de Administración - Reglas de Negocio
            </span>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/admin/logout">
                    <i class="fas fa-sign-out-alt me-1"></i>Cerrar Sesión
                </a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="row">
            <div class="col-md-8">
                <div class="card">
                    <div class="card-header bg-primary text-white">
                        <h5><i class="fas fa-sliders-h me-2"></i>Configuración de Reglas de Negocio</h5>
                    </div>
                    <div class="card-body">
                        <form id="reglas-form">
                            <div class="row">
                                <div class="col-md-6">
                                    <h6 class="text-primary">Parámetros de Scoring</h6>
                                    
                                    <div class="mb-3">
                                        <label class="form-label">Score Mínimo para Aprobación:</label>
                                        <input type="number" class="form-control" name="SCORE_MINIMO_APROBACION" 
                                               value="{{ reglas.SCORE_MINIMO_APROBACION }}" min="100" max="400">
                                        <small class="text-muted">Rango: 100-400 puntos</small>
                                    </div>
                                    
                                    <div class="mb-3">
                                        <label class="form-label">FICO Score Mínimo:</label>
                                        <input type="number" class="form-control" name="FICO_MINIMO_APROBACION" 
                                               value="{{ reglas.FICO_MINIMO_APROBACION }}" min="300" max="650">
                                        <small class="text-muted">Rango: 300-650</small>
                                    </div>
                                    
                                    <div class="mb-3">
                                        <label class="form-label">Factor de Scoring:</label>
                                        <input type="number" class="form-control" name="FACTOR_SCORING" 
                                               value="{{ reglas.FACTOR_SCORING }}" min="0.5" max="2.0" step="0.1">
                                        <small class="text-muted">Multiplicador para aumentar/disminuir scores</small>
                                    </div>
                                </div>
                                
                                <div class="col-md-6">
                                    <h6 class="text-success">Parámetros Financieros</h6>
                                    
                                    <div class="mb-3">
                                        <label class="form-label">Ingreso Mínimo (MXN):</label>
                                        <input type="number" class="form-control" name="INGRESO_MINIMO" 
                                               value="{{ reglas.INGRESO_MINIMO }}" min="5000" max="20000">
                                        <small class="text-muted">Ingreso mínimo requerido</small>
                                    </div>
                                    
                                    <div class="mb-3">
                                        <label class="form-label">Monto Máximo de Crédito (MXN):</label>
                                        <input type="number" class="form-control" name="MONTO_MAXIMO_CREDITO" 
                                               value="{{ reglas.MONTO_MAXIMO_CREDITO }}" min="50000" max="500000">
                                        <small class="text-muted">Límite máximo de crédito</small>
                                    </div>
                                    
                                    <div class="mb-3">
                                        <label class="form-label">TDSR Máximo (%):</label>
                                        <input type="number" class="form-control" name="TDSR_MAXIMO" 
                                               value="{{ (reglas.TDSR_MAXIMO * 100)|int }}" min="30" max="60">
                                        <small class="text-muted">Ratio máximo deuda-ingreso</small>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="row">
                                <div class="col-md-6">
                                    <h6 class="text-info">Tasas de Interés</h6>
                                    
                                    <div class="mb-3">
                                        <label class="form-label">Tasa Mínima (% anual):</label>
                                        <input type="number" class="form-control" name="TASA_MINIMA" 
                                               value="{{ (reglas.TASA_MINIMA * 100)|int }}" min="15" max="30" step="1">
                                        <small class="text-muted">Tasa más baja disponible</small>
                                    </div>
                                    
                                    <div class="mb-3">
                                        <label class="form-label">Tasa Máxima (% anual):</label>
                                        <input type="number" class="form-control" name="TASA_MAXIMA" 
                                               value="{{ (reglas.TASA_MAXIMA * 100)|int }}" min="25" max="50" step="1">
                                        <small class="text-muted">Tasa más alta disponible</small>
                                    </div>
                                </div>
                                
                                <div class="col-md-6">
                                    <h6 class="text-warning">Plazos Disponibles</h6>
                                    
                                    <div class="mb-3">
                                        <label class="form-label">Plazos Autorizados (meses):</label>
                                        <input type="text" class="form-control" name="PLAZOS_AUTORIZADOS" 
                                               value="{{ reglas.PLAZOS_AUTORIZADOS|join(',') }}">
                                        <small class="text-muted">Separados por comas (ej: 3,6,9,12,18,24)</small>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="text-center">
                                <button type="button" class="btn btn-success btn-lg me-3" onclick="actualizarReglas()">
                                    <i class="fas fa-save me-2"></i>Guardar Cambios
                                </button>
                                <button type="button" class="btn btn-warning btn-lg me-3" onclick="resetearReglas()">
                                    <i class="fas fa-undo me-2"></i>Resetear Valores
                                </button>
                                <a href="/" class="btn btn-outline-secondary btn-lg">
                                    <i class="fas fa-eye me-2"></i>Ver Simulador
                                </a>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
            
            <div class="col-md-4">
                <div class="card">
                    <div class="card-header bg-info text-white">
                        <h6><i class="fas fa-info-circle me-2"></i>Guía de Configuración</h6>
                    </div>
                    <div class="card-body">
                        <div class="accordion" id="guiaAccordion">
                            <div class="accordion-item">
                                <h2 class="accordion-header">
                                    <button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#scoring">
                                        Parámetros de Scoring
                                    </button>
                                </h2>
                                <div id="scoring" class="accordion-collapse collapse show">
                                    <div class="accordion-body">
                                        <small>
                                            <strong>Score Mínimo:</strong> Puntaje mínimo para aprobar un crédito.<br>
                                            <strong>FICO Mínimo:</strong> Score crediticio mínimo aceptado.<br>
                                            <strong>Factor Scoring:</strong> Multiplica todos los puntajes calculados.
                                        </small>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="accordion-item">
                                <h2 class="accordion-header">
                                    <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#financieros">
                                        Parámetros Financieros
                                    </button>
                                </h2>
                                <div id="financieros" class="accordion-collapse collapse">
                                    <div class="accordion-body">
                                        <small>
                                            <strong>Ingreso Mínimo:</strong> Ingreso mensual mínimo requerido.<br>
                                            <strong>Monto Máximo:</strong> Límite máximo de crédito otorgable.<br>
                                            <strong>TDSR Máximo:</strong> Ratio máximo deuda/ingreso permitido.
                                        </small>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="accordion-item">
                                <h2 class="accordion-header">
                                    <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#recomendaciones">
                                        Recomendaciones
                                    </button>
                                </h2>
                                <div id="recomendaciones" class="accordion-collapse collapse">
                                    <div class="accordion-body">
                                        <small>
                                            <div class="alert alert-warning p-2">
                                                <strong>Para más aprobaciones:</strong><br>
                                                • Reducir Score Mínimo a 200-250<br>
                                                • Aumentar Factor Scoring a 1.3-1.5<br>
                                                • Reducir FICO Mínimo a 450-500
                                            </div>
                                            <div class="alert alert-info p-2">
                                                <strong>Para ser más restrictivo:</strong><br>
                                                • Aumentar Score Mínimo a 300-350<br>
                                                • Reducir Factor Scoring a 0.8-1.0<br>
                                                • Aumentar FICO Mínimo a 600-650
                                            </div>
                                        </small>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="mt-3">
                            <h6 class="text-danger">Estado Actual del Modelo:</h6>
                            <div id="estado-modelo" class="bg-light p-2 rounded">
                                <small>
                                    <strong>Modo:</strong> <span class="badge bg-success">Moderadamente Permisivo</span><br>
                                    <strong>Factor:</strong> {{ reglas.FACTOR_SCORING }}x<br>
                                    <strong>Score Min:</strong> {{ reglas.SCORE_MINIMO_APROBACION }} pts<br>
                                    <strong>FICO Min:</strong> {{ reglas.FICO_MINIMO_APROBACION }} pts
                                </small>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="card mt-3">
                    <div class="card-header bg-dark text-white">
                        <h6><i class="fas fa-vial me-2"></i>Prueba Rápida</h6>
                    </div>
                    <div class="card-body">
                        <p class="small">Prueba cómo funcionan las reglas actuales:</p>
                        <div class="d-grid gap-2">
                            <a href="/simulador" class="btn btn-outline-primary btn-sm" target="_blank">
                                <i class="fas fa-calculator me-1"></i>Abrir Simulador
                            </a>
                            <a href="/casos-estudio" class="btn btn-outline-success btn-sm" target="_blank">
                                <i class="fas fa-users me-1"></i>Probar Casos
                            </a>
                        </div>
                        
                        <div class="mt-3">
                            <small class="text-muted">
                                <strong>Tip:</strong> Después de cambiar las reglas, prueba los casos de estudio para verificar que funcionen como esperas.
                            </small>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        function actualizarReglas() {
            const form = document.getElementById('reglas-form');
            const formData = new FormData(form);
            const data = {};
            
            for (let [key, value] of formData.entries()) {
                if (key.includes('TASA_')) {
                    data[key] = parseFloat(value) / 100; // Convertir porcentaje a decimal
                } else if (key === 'TDSR_MAXIMO') {
                    data[key] = parseFloat(value) / 100; // Convertir porcentaje a decimal
                } else if (key === 'PLAZOS_AUTORIZADOS') {
                    data[key] = value; // Se procesará en el backend
                } else {
                    data[key] = value;
                }
            }
            
            fetch('/api/admin/actualizar-reglas', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    alert('✅ Reglas actualizadas correctamente');
                    location.reload();
                } else {
                    alert('❌ Error: ' + result.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('❌ Error al actualizar reglas');
            });
        }
        
        function resetearReglas() {
            if (confirm('¿Estás seguro de que quieres resetear todas las reglas a los valores por defecto?')) {
                const valoresDefecto = {
                    'SCORE_MINIMO_APROBACION': 250,
                    'FICO_MINIMO_APROBACION': 500,
                    'FACTOR_SCORING': 1.2,
                    'INGRESO_MINIMO': 8000,
                    'MONTO_MAXIMO_CREDITO': 150000,
                    'TDSR_MAXIMO': 45,
                    'TASA_MINIMA': 22,
                    'TASA_MAXIMA': 38,
                    'PLAZOS_AUTORIZADOS': '3,6,9,12'
                };
                
                for (let [key, value] of Object.entries(valoresDefecto)) {
                    const input = document.querySelector(`input[name="${key}"]`);
                    if (input) {
                        input.value = value;
                    }
                }
                
                alert('Valores reseteados. Haz clic en "Guardar Cambios" para aplicar.');
            }
        }
        
        // Validaciones en tiempo real
        document.addEventListener('DOMContentLoaded', function() {
            const inputs = document.querySelectorAll('input[type="number"]');
            inputs.forEach(input => {
                input.addEventListener('change', function() {
                    // Validar rangos
                    const min = parseFloat(this.min);
                    const max = parseFloat(this.max);
                    const value = parseFloat(this.value);
                    
                    if (value < min) {
                        this.value = min;
                        alert(`Valor mínimo permitido: ${min}`);
                    } else if (value > max) {
                        this.value = max;
                        alert(`Valor máximo permitido: ${max}`);
                    }
                });
            });
        });
    </script>
</body>
</html>
'''

# Templates principales (agregar navegación a admin)
TEMPLATE_HOME = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Simulador de Gestión de Crédito - Hotmart</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .hero-gradient { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .card-hover:hover { transform: translateY(-5px); transition: all 0.3s ease; }
        .feature-icon { width: 80px; height: 80px; margin: 0 auto; background: rgba(255,255,255,0.1); }
        .admin-link { position: fixed; bottom: 20px; right: 20px; z-index: 1000; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="/">
                <i class="fas fa-graduation-cap me-2"></i>Simulador de Crédito Profesional
            </a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/simulador">Simulador</a>
                <a class="nav-link" href="/casos-estudio">Casos de Estudio</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <!-- Hero Section -->
        <div class="hero-gradient text-white p-5 rounded mb-5">
            <div class="row align-items-center">
                <div class="col-md-8">
                    <h1 class="display-4 mb-3">
                        <i class="fas fa-calculator me-3"></i>
                        Simulador de Gestión de Crédito
                    </h1>
                    <p class="lead mb-3">
                        Herramienta educativa profesional con <strong>modelo matemático real</strong> 
                        para análisis de riesgo crediticio
                    </p>
                    <p class="mb-4">
                        📊 Score: 250-430 puntos | 💰 Hasta $150,000 | 📅 3-12 meses | 📈 22%-38% anual
                    </p>
                    <a href="/simulador" class="btn btn-light btn-lg me-3">
                        <i class="fas fa-play me-2"></i>Comenzar Simulación
                    </a>
                    <a href="/casos-estudio" class="btn btn-outline-light btn-lg">
                        <i class="fas fa-book me-2"></i>Ver Casos Reales
                    </a>
                </div>
                <div class="col-md-4 text-center">
                    <div class="bg-white bg-opacity-10 p-4 rounded">
                        <h3>✅ Modelo Profesional</h3>
                        <p>Basado en variables reales del sector financiero mexicano</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Resto del contenido igual... -->
        
    </div>

    <!-- Enlace Admin -->
    <a href="/admin/login" class="admin-link btn btn-danger btn-sm" title="Acceso Administrador">
        <i class="fas fa-cog"></i>
    </a>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
'''

# [Resto de templates TEMPLATE_SIMULADOR y TEMPLATE_CASOS iguales al código anterior]

# Puerto para Render
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
	# AGREGAR ESTA PARTE AL FINAL DE TU app.py

# Completar TEMPLATE_ADMIN_REGLAS (continúa desde donde se cortó)
TEMPLATE_ADMIN_REGLAS = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reglas de Negocio - Administrador</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-dark bg-danger">
        <div class="container">
            <span class="navbar-brand">
                <i class="fas fa-cogs me-2"></i>Panel de Administración - Reglas de Negocio
            </span>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/admin/logout">
                    <i class="fas fa-sign-out-alt me-1"></i>Cerrar Sesión
                </a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="alert alert-success">
            <h5><i class="fas fa-info-circle me-2"></i>Panel de Administración Activo</h5>
            <p class="mb-0">Puedes ajustar todas las reglas de negocio del simulador desde aquí.</p>
        </div>
        
        <div class="row">
            <div class="col-md-8">
                <div class="card">
                    <div class="card-header bg-primary text-white">
                        <h5><i class="fas fa-sliders-h me-2"></i>Configuración de Reglas de Negocio</h5>
                    </div>
                    <div class="card-body">
                        <form id="reglas-form">
                            <div class="row">
                                <div class="col-md-6">
                                    <h6 class="text-primary">Parámetros de Scoring</h6>
                                    
                                    <div class="mb-3">
                                        <label class="form-label">Score Mínimo para Aprobación:</label>
                                        <input type="number" class="form-control" name="SCORE_MINIMO_APROBACION" 
                                               value="{{ reglas.SCORE_MINIMO_APROBACION }}" min="100" max="400">
                                        <small class="text-muted">Actual: {{ reglas.SCORE_MINIMO_APROBACION }} puntos</small>
                                    </div>
                                    
                                    <div class="mb-3">
                                        <label class="form-label">FICO Score Mínimo:</label>
                                        <input type="number" class="form-control" name="FICO_MINIMO_APROBACION" 
                                               value="{{ reglas.FICO_MINIMO_APROBACION }}" min="300" max="650">
                                        <small class="text-muted">Actual: {{ reglas.FICO_MINIMO_APROBACION }}</small>
                                    </div>
                                    
                                    <div class="mb-3">
                                        <label class="form-label">Factor de Scoring:</label>
                                        <input type="number" class="form-control" name="FACTOR_SCORING" 
                                               value="{{ reglas.FACTOR_SCORING }}" min="0.5" max="2.0" step="0.1">
                                        <small class="text-muted">Actual: {{ reglas.FACTOR_SCORING }}x (multiplica los puntajes)</small>
                                    </div>
                                </div>
                                
                                <div class="col-md-6">
                                    <h6 class="text-success">Parámetros Financieros</h6>
                                    
                                    <div class="mb-3">
                                        <label class="form-label">Ingreso Mínimo (MXN):</label>
                                        <input type="number" class="form-control" name="INGRESO_MINIMO" 
                                               value="{{ reglas.INGRESO_MINIMO }}" min="5000" max="20000">
                                        <small class="text-muted">Actual: ${{ reglas.INGRESO_MINIMO:,}}</small>
                                    </div>
                                    
                                    <div class="mb-3">
                                        <label class="form-label">Monto Máximo de Crédito (MXN):</label>
                                        <input type="number" class="form-control" name="MONTO_MAXIMO_CREDITO" 
                                               value="{{ reglas.MONTO_MAXIMO_CREDITO }}" min="50000" max="500000">
                                        <small class="text-muted">Actual: ${{ reglas.MONTO_MAXIMO_CREDITO:,}}</small>
                                    </div>
                                    
                                    <div class="mb-3">
                                        <label class="form-label">TDSR Máximo (%):</label>
                                        <input type="number" class="form-control" name="TDSR_MAXIMO" 
                                               value="{{ (reglas.TDSR_MAXIMO * 100)|int }}" min="30" max="60">
                                        <small class="text-muted">Actual: {{ (reglas.TDSR_MAXIMO * 100)|int }}%</small>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="row">
                                <div class="col-md-6">
                                    <h6 class="text-info">Tasas de Interés</h6>
                                    
                                    <div class="mb-3">
                                        <label class="form-label">Tasa Mínima (% anual):</label>
                                        <input type="number" class="form-control" name="TASA_MINIMA" 
                                               value="{{ (reglas.TASA_MINIMA * 100)|int }}" min="15" max="30">
                                        <small class="text-muted">Actual: {{ (reglas.TASA_MINIMA * 100)|int }}%</small>
                                    </div>
                                    
                                    <div class="mb-3">
                                        <label class="form-label">Tasa Máxima (% anual):</label>
                                        <input type="number" class="form-control" name="TASA_MAXIMA" 
                                               value="{{ (reglas.TASA_MAXIMA * 100)|int }}" min="25" max="50">
                                        <small class="text-muted">Actual: {{ (reglas.TASA_MAXIMA * 100)|int }}%</small>
                                    </div>
                                </div>
                                
                                <div class="col-md-6">
                                    <h6 class="text-warning">Plazos Disponibles</h6>
                                    
                                    <div class="mb-3">
                                        <label class="form-label">Plazos Autorizados (meses):</label>
                                        <input type="text" class="form-control" name="PLAZOS_AUTORIZADOS" 
                                               value="{{ reglas.PLAZOS_AUTORIZADOS|join(',') }}">
                                        <small class="text-muted">Actual: {{ reglas.PLAZOS_AUTORIZADOS|join(', ') }} meses</small>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="text-center mt-4">
                                <button type="button" class="btn btn-success btn-lg me-3" onclick="actualizarReglas()">
                                    <i class="fas fa-save me-2"></i>Guardar Cambios
                                </button>
                                <button type="button" class="btn btn-warning btn-lg me-3" onclick="resetearReglas()">
                                    <i class="fas fa-undo me-2"></i>Valores por Defecto
                                </button>
                                <a href="/" class="btn btn-outline-secondary btn-lg">
                                    <i class="fas fa-eye me-2"></i>Ver Simulador
                                </a>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
            
            <div class="col-md-4">
                <div class="card">
                    <div class="card-header bg-info text-white">
                        <h6><i class="fas fa-lightbulb me-2"></i>Sugerencias Rápidas</h6>
                    </div>
                    <div class="card-body">
                        <div class="d-grid gap-2 mb-3">
                            <button class="btn btn-outline-success btn-sm" onclick="aplicarConfiguracion('permisivo')">
                                🟢 Más Permisivo
                            </button>
                            <button class="btn btn-outline-warning btn-sm" onclick="aplicarConfiguracion('equilibrado')">
                                🟡 Equilibrado
                            </button>
                            <button class="btn btn-outline-danger btn-sm" onclick="aplicarConfiguracion('restrictivo')">
                                🔴 Más Restrictivo
                            </button>
                        </div>
                        
                        <div class="alert alert-info p-2">
                            <small>
                                <strong>Configuración Actual:</strong><br>
                                • Score Min: {{ reglas.SCORE_MINIMO_APROBACION }}<br>
                                • Factor: {{ reglas.FACTOR_SCORING }}x<br>
                                • FICO Min: {{ reglas.FICO_MINIMO_APROBACION }}<br>
                                • TDSR Max: {{ (reglas.TDSR_MAXIMO * 100)|int }}%
                            </small>
                        </div>
                        
                        <div class="mt-3">
                            <h6>Prueba Rápida:</h6>
                            <div class="d-grid gap-1">
                                <a href="/simulador" class="btn btn-outline-primary btn-sm" target="_blank">
                                    <i class="fas fa-calculator me-1"></i>Abrir Simulador
                                </a>
                                <a href="/casos-estudio" class="btn btn-outline-success btn-sm" target="_blank">
                                    <i class="fas fa-users me-1"></i>Probar Casos
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        function actualizarReglas() {
            const form = document.getElementById('reglas-form');
            const formData = new FormData(form);
            const data = {};
            
            for (let [key, value] of formData.entries()) {
                if (key.includes('TASA_')) {
                    data[key] = parseFloat(value) / 100;
                } else if (key === 'TDSR_MAXIMO') {
                    data[key] = parseFloat(value) / 100;
                } else if (key === 'PLAZOS_AUTORIZADOS') {
                    data[key] = value;
                } else {
                    data[key] = value;
                }
            }
            
            fetch('/api/admin/actualizar-reglas', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    alert('✅ Reglas actualizadas correctamente');
                    location.reload();
                } else {
                    alert('❌ Error: ' + result.error);
                }
            });
        }
        
        function resetearReglas() {
            if (confirm('¿Resetear a valores por defecto?')) {
                document.querySelector('[name="SCORE_MINIMO_APROBACION"]').value = 250;
                document.querySelector('[name="FICO_MINIMO_APROBACION"]').value = 500;
                document.querySelector('[name="FACTOR_SCORING"]').value = 1.2;
                document.querySelector('[name="INGRESO_MINIMO"]').value = 8000;
                document.querySelector('[name="MONTO_MAXIMO_CREDITO"]').value = 150000;
                document.querySelector('[name="TDSR_MAXIMO"]').value = 45;
                document.querySelector('[name="TASA_MINIMA"]').value = 22;
                document.querySelector('[name="TASA_MAXIMA"]').value = 38;
                document.querySelector('[name="PLAZOS_AUTORIZADOS"]').value = '3,6,9,12';
            }
        }
        
        function aplicarConfiguracion(tipo) {
            let config = {};
            
            if (tipo === 'permisivo') {
                config = {
                    'SCORE_MINIMO_APROBACION': 200,
                    'FICO_MINIMO_APROBACION': 450,
                    'FACTOR_SCORING': 1.5,
                    'TDSR_MAXIMO': 50
                };
            } else if (tipo === 'equilibrado') {
                config = {
                    'SCORE_MINIMO_APROBACION': 250,
                    'FICO_MINIMO_APROBACION': 500,
                    'FACTOR_SCORING': 1.2,
                    'TDSR_MAXIMO': 45
                };
            } else if (tipo === 'restrictivo') {
                config = {
                    'SCORE_MINIMO_APROBACION': 300,
                    'FICO_MINIMO_APROBACION': 600,
                    'FACTOR_SCORING': 1.0,
                    'TDSR_MAXIMO': 35
                };
            }
            
            for (let [key, value] of Object.entries(config)) {
                const input = document.querySelector(`[name="${key}"]`);
                if (input) input.value = value;
            }
            
            alert(`Configuración "${tipo}" aplicada. Haz clic en "Guardar Cambios" para aplicar.`);
        }
    </script>
</body>
</html>
'''

# Templates principales
TEMPLATE_HOME = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Simulador de Gestión de Crédito - Hotmart</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .hero-gradient { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .card-hover:hover { transform: translateY(-5px); transition: all 0.3s ease; }
        .feature-icon { width: 80px; height: 80px; margin: 0 auto; background: rgba(255,255,255,0.1); }
        .admin-link { position: fixed; bottom: 20px; right: 20px; z-index: 1000; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="/">
                <i class="fas fa-graduation-cap me-2"></i>Simulador de Crédito Profesional
            </a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/simulador">Simulador</a>
                <a class="nav-link" href="/casos-estudio">Casos de Estudio</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="hero-gradient text-white p-5 rounded mb-5">
            <div class="row align-items-center">
                <div class="col-md-8">
                    <h1 class="display-4 mb-3">
                        <i class="fas fa-calculator me-3"></i>
                        Simulador de Gestión de Crédito
                    </h1>
                    <p class="lead mb-3">
                        Herramienta educativa profesional con <strong>modelo matemático real</strong> 
                        para análisis de riesgo crediticio
                    </p>
                    <p class="mb-4">
                        📊 Score: 250-430 puntos | 💰 Hasta $150,000 | 📅 3-12 meses | 📈 22%-38% anual
                    </p>
                    <a href="/simulador" class="btn btn-light btn-lg me-3">
                        <i class="fas fa-play me-2"></i>Comenzar Simulación
                    </a>
                    <a href="/casos-estudio" class="btn btn-outline-light btn-lg">
                        <i class="fas fa-book me-2"></i>Ver Casos Reales
                    </a>
                </div>
                <div class="col-md-4 text-center">
                    <div class="bg-white bg-opacity-10 p-4 rounded">
                        <h3>✅ Modelo Profesional</h3>
                        <p>Basado en variables reales del sector financiero mexicano</p>
                    </div>
                </div>
            </div>
        </div>

        <div class="row mb-5">
            <div class="col-12 text-center mb-4">
                <h2><i class="fas fa-cogs text-primary me-2"></i>Características del Modelo</h2>
                <p class="lead">Sistema de scoring crediticio con parámetros reales del mercado</p>
            </div>
            
            <div class="col-md-3">
                <div class="card card-hover text-center h-100">
                    <div class="card-body">
                        <div class="feature-icon bg-primary text-white rounded-circle d-flex align-items-center justify-content-center mb-3">
                            <i class="fas fa-chart-bar fa-2x"></i>
                        </div>
                        <h5>Variables Generales</h5>
                        <p class="small">Antigüedad, estado civil, educación, ocupación (30%)</p>
                        <span class="badge bg-primary">180 puntos máx</span>
                    </div>
                </div>
            </div>
            
            <div class="col-md-3">
                <div class="card card-hover text-center h-100">
                    <div class="card-body">
                        <div class="feature-icon bg-success text-white rounded-circle d-flex align-items-center justify-content-center mb-3">
                            <i class="fas fa-history fa-2x"></i>
                        </div>
                        <h5>Historial Crediticio</h5>
                        <p class="small">FICO Score, consultas, calificaciones (30%)</p>
                        <span class="badge bg-success">130 puntos máx</span>
                    </div>
                </div>
            </div>
            
            <div class="col-md-3">
                <div class="card card-hover text-center h-100">
                    <div class="card-body">
                        <div class="feature-icon bg-info text-white rounded-circle d-flex align-items-center justify-content-center mb-3">
                            <i class="fas fa-wallet fa-2x"></i>
                        </div>
                        <h5>Capacidad de Pago</h5>
                        <p class="small">TDSR, tipo comprobante, estabilidad (40%)</p>
                        <span class="badge bg-info">90 puntos máx</span>
                    </div>
                </div>
            </div>
            
            <div class="col-md-3">
                <div class="card card-hover text-center h-100">
                    <div class="card-body">
                        <div class="feature-icon bg-warning text-white rounded-circle d-flex align-items-center justify-content-center mb-3">
                            <i class="fas fa-calculator fa-2x"></i>
                        </div>
                        <h5>Condiciones</h5>
                        <p class="small">Monto, tasa, plazo automáticos</p>
                        <span class="badge bg-warning">Calculado</span>
                    </div>
                </div>
            </div>
        </div>

        <div class="row">
            <div class="col-md-6">
                <div class="card border-primary">
                    <div class="card-body text-center">
                        <h4 class="text-primary">🚀 Comenzar Simulación</h4>
                        <p>Evalúa un perfil crediticio completo con nuestro modelo profesional</p>
                        <a href="/simulador" class="btn btn-primary btn-lg">
                            <i class="fas fa-calculator me-2"></i>Ir al Simulador
                        </a>
                    </div>
                </div>
            </div>
            
            <div class="col-md-6">
                <div class="card border-success">
                    <div class="card-body text-center">
                        <h4 class="text-success">📚 Casos de Estudio</h4>
                        <p>Explora perfiles reales y aprende con ejemplos prácticos</p>
                        <a href="/casos-estudio" class="btn btn-success btn-lg">
                            <i class="fas fa-users me-2"></i>Ver Casos Reales
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <a href="/admin/login" class="admin-link btn btn-danger btn-sm" title="Acceso Administrador">
        <i class="fas fa-cog"></i>
    </a>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
'''

# Templates SIMULADOR y CASOS (usar los mismos del código anterior)
TEMPLATE_SIMULADOR = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Simulador de Crédito - Evaluación Profesional</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .form-section { border-left: 4px solid #007bff; padding-left: 15px; margin-bottom: 30px; }
        .resultado-aprobado { background: linear-gradient(135deg, #28a745, #20c997); }
        .resultado-rechazado { background: linear-gradient(135deg, #dc3545, #fd7e14); }
        .score-circle { width: 120px; height: 120px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 24px; font-weight: bold; margin: 0 auto; }
        .detalles-scoring { font-size: 0.9em; }
        .progress-custom { height: 25px; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="/">
                <i class="fas fa-calculator me-2"></i>Simulador de Crédito
            </a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/">Inicio</a>
                <a class="nav-link" href="/casos-estudio">Casos de Estudio</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="row">
            <div class="col-lg-8">
                <div class="card">
                    <div class="card-header bg-primary text-white">
                        <h4><i class="fas fa-user-check me-2"></i>Evaluación Crediticia Profesional</h4>
                        <p class="mb-0">Complete todos los campos para obtener su evaluación</p>
                    </div>
                    <div class="card-body">
                        <form id="formulario-credito">
                            <!-- Información Personal -->
                            <div class="form-section">
                                <h5 class="text-primary mb-3"><i class="fas fa-user me-2"></i>Información Personal</h5>
                                <div class="row">
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label class="form-label">Edad:</label>
                                            <input type="number" class="form-control" name="edad" min="18" max="75" value="30" required>
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label class="form-label">Estado Civil:</label>
                                            <select class="form-control" name="estado_civil" required>
                                                <option value="soltero">Soltero(a)</option>
                                                <option value="casado">Casado(a)</option>
                                                <option value="divorciado">Divorciado(a)</option>
                                                <option value="viudo">Viudo(a)</option>
                                            </select>
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label class="form-label">Dependientes Económicos:</label>
                                            <input type="number" class="form-control" name="dependientes" min="0" max="10" value="0" required>
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label class="form-label">Nivel de Estudios:</label>
                                            <select class="form-control" name="nivel_estudios" required>
                                                <option value="primaria">Primaria</option>
                                                <option value="secundaria">Secundaria</option>
                                                <option value="preparatoria">Preparatoria</option>
                                                <option value="universidad">Universidad</option>
                                            </select>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- Información Laboral -->
                            <div class="form-section">
                                <h5 class="text-success mb-3"><i class="fas fa-briefcase me-2"></i>Información Laboral</h5>
                                <div class="row">
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label class="form-label">Ocupación:</label>
                                            <select class="form-control" name="ocupacion" required>
                                                <option value="empleado_publico">Empleado Público</option>
                                                <option value="empleado_privado">Empleado Privado</option>
                                                <option value="independiente">Trabajador Independiente</option>
                                                <option value="comerciante">Comerciante</option>
                                            </select>
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label class="form-label">Antigüedad en Empleo (años):</label>
                                            <input type="number" class="form-control" name="antiguedad_empleo" min="0" max="50" step="0.5" value="2" required>
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label class="form-label">Ingresos Mensuales (MXN):</label>
                                            <input type="number" class="form-control" name="ingresos_mensuales" min="5000" max="200000" value="15000" required>
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label class="form-label">Tipo de Comprobante:</label>
                                            <select class="form-control" name="tipo_comprobante" required>
                                                <option value="nomina">Nómina</option>
                                                <option value="estados_cuenta">Estados de Cuenta</option>
                                                <option value="declaracion">Declaración Fiscal</option>
                                                <option value="otros">Otros</option>
                                            </select>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- Información de Vivienda -->
                            <div class="form-section">
                                <h5 class="text-info mb-3"><i class="fas fa-home me-2"></i>Información de Vivienda</h5>
                                <div class="row">
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label class="form-label">Antigüedad en Domicilio (años):</label>
                                            <input type="number" class="form-control" name="antiguedad_domicilio" min="0" max="50" step="0.5" value="3" required>
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label class="form-label">¿Cuenta con comprobante de domicilio?</label>
                                            <select class="form-control" name="comprobante_domicilio" required>
                                                <option value="si">Sí</option>
                                                <option value="no">No</option>
                                            </select>
                                        </div>
                                    </div>
                                    <div class="col-md-12">
                                        <div class="mb-3">
                                            <label class="form-label">¿Cuenta con comprobante de ingresos?</label>
                                            <select class="form-control" name="comprobante_ingresos" required>
                                                <option value="si">Sí</option>
                                                <option value="no">No</option>
                                            </select>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- Historial Crediticio -->
                            <div class="form-section">
                                <h5 class="text-warning mb-3"><i class="fas fa-history me-2"></i>Historial Crediticio</h5>
                                <div class="row">
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label class="form-label">FICO Score:</label>
                                            <input type="number" class="form-control" name="fico_score" min="300" max="850" value="650" required>
                                            <small class="text-muted">Rango: 300-850</small>
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label class="form-label">Última Calificación (1=Excelente, 4=Mala):</label>
                                            <select class="form-control" name="ultima_calificacion" required>
                                                <option value="1">1 - Excelente</option>
                                                <option value="2">2 - Buena</option>
                                                <option value="3">3 - Regular</option>
                                                <option value="4">4 - Mala</option>
                                            </select>
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label class="form-label">Número de Consultas (últimos 12 meses):</label>
                                            <input type="number" class="form-control" name="numero_consultas" min="0" max="50" value="5" required>
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label class="form-label">Deudas Mensuales Actuales (MXN):</label>
                                            <input type="number" class="form-control" name="deuda_mensual" min="0" max="100000" value="3000" required>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="text-center">
                                <button type="submit" class="btn btn-primary btn-lg px-5">
                                    <i class="fas fa-calculator me-2"></i>Evaluar Crédito
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>

            <div class="col-lg-4">
                <div id="resultado-evaluacion" style="display: none;">
                    <!-- Los resultados aparecerán aquí -->
                </div>
                
                <div class="card">
                    <div class="card-header bg-info text-white">
                        <h5><i class="fas fa-info-circle me-2"></i>Información del Modelo</h5>
                    </div>
                    <div class="card-body">
                        <div class="mb-3">
                            <h6>Variables Evaluadas:</h6>
                            <ul class="list-unstyled">
                                <li><i class="fas fa-check text-success me-2"></i>Variables Generales (30%)</li>
                                <li><i class="fas fa-check text-success me-2"></i>Historial Crediticio (30%)</li>
                                <li><i class="fas fa-check text-success me-2"></i>Capacidad de Pago (40%)</li>
                            </ul>
                        </div>
                        
                        <div class="mb-3">
                            <h6>Rangos de Score:</h6>
                            <div class="d-flex justify-content-between">
                                <span class="badge bg-danger">250-299</span>
                                <span class="badge bg-warning">300-349</span>
                                <span class="badge bg-success">350+</span>
                            </div>
                        </div>
                        
                        <div class="alert alert-info p-2">
                            <small>
                                <strong>Tip:</strong> Complete todos los campos con información real para obtener una evaluación precisa.
                            </small>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        document.getElementById('formulario-credito').addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Mostrar loading
            const boton = e.target.querySelector('button[type="submit"]');
            const textoOriginal = boton.innerHTML;
            boton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Evaluando...';
            boton.disabled = true;
            
            // Recopilar datos del formulario
            const formData = new FormData(e.target);
            const datos = {};
            for (let [key, value] of formData.entries()) {
                datos[key] = value;
            }
            
            // Enviar evaluación
            fetch('/api/evaluar', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(datos)
            })
            .then(response => response.json())
            .then(resultado => {
                // Restaurar botón
                boton.innerHTML = textoOriginal;
                boton.disabled = false;
                
                if (resultado.success) {
                    mostrarResultado(resultado.data);
                } else {
                    alert('Error: ' + resultado.error);
                }
            })
            .catch(error => {
                // Restaurar botón
                boton.innerHTML = textoOriginal;
                boton.disabled = false;
                console.error('Error:', error);
                alert('Error al procesar la evaluación');
            });
        });
        
        function mostrarResultado(data) {
            const contenedor = document.getElementById('resultado-evaluacion');
            
            let html = '';
            
            if (data.aprobado) {
                html = `
                    <div class="card">
                        <div class="card-header resultado-aprobado text-white text-center">
                            <h4><i class="fas fa-check-circle me-2"></i>¡CRÉDITO APROBADO!</h4>
                        </div>
                        <div class="card-body">
                            <div class="text-center mb-4">
                                <div class="score-circle bg-success text-white">
                                    ${data.score}
                                </div>
                                <h5 class="mt-2">Score Crediticio</h5>
                                <span class="badge bg-${data.color_riesgo}">${data.nivel_riesgo} Riesgo</span>
                            </div>
                            
                            <div class="row text-center mb-3">
                                <div class="col-12">
                                    <h3 class="text-success">$${data.monto_aprobado.toLocaleString()}</h3>
                                    <p class="text-muted">Monto Aprobado</p>
                                </div>
                            </div>
                            
                            <div class="mb-3">
                                <h6>Condiciones:</h6>
                                <p><strong>Tasa Anual:</strong> ${(data.tasa_anual * 100).toFixed(1)}%</p>
                                <p><strong>TDSR:</strong> ${(data.tdsr * 100).toFixed(1)}%</p>
                            </div>
                            
                            <div class="mb-3">
                                <h6>Opciones de Plazo:</h6>
                                ${data.opciones_plazo.map(opcion => `
                                    <div class="d-flex justify-content-between border-bottom py-2">
                                        <span>${opcion.plazo} meses</span>
                                        <span class="${opcion.factible ? 'text-success' : 'text-danger'}">
                                            $${opcion.pago_mensual.toLocaleString()}
                                            ${opcion.factible ? '✓' : '✗'}
                                        </span>
                                    </div>
                                `).join('')}
                            </div>
                            
                            <button class="btn btn-primary btn-sm w-100" onclick="mostrarDetalles()">
                                <i class="fas fa-chart-bar me-2"></i>Ver Detalles del Scoring
                            </button>
                        </div>
                    </div>
                `;
            } else {
                html = `
                    <div class="card">
                        <div class="card-header resultado-rechazado text-white text-center">
                            <h4><i class="fas fa-times-circle me-2"></i>CRÉDITO NO APROBADO</h4>
                        </div>
                        <div class="card-body text-center">
                            <div class="score-circle bg-danger text-white mb-3">
                                ${data.score}
                            </div>
                            <h6 class="text-danger">Razón:</h6>
                            <p>${data.razon}</p>
                            
                            <div class="alert alert-info mt-3">
                                <small>
                                    <strong>Sugerencias:</strong><br>
                                    • Mejorar historial crediticio<br>
                                    • Aumentar ingresos<br>
                                    • Reducir deudas actuales
                                </small>
                            </div>
                        </div>
                    </div>
                `;
            }
            
            contenedor.innerHTML = html;
            contenedor.style.display = 'block';
            
            // Guardar datos para detalles
            window.ultimaEvaluacion = data;
            
            // Scroll al resultado
            contenedor.scrollIntoView({ behavior: 'smooth' });
        }
        
        function mostrarDetalles() {
            if (!window.ultimaEvaluacion || !window.ultimaEvaluacion.desglose) return;
            
            const data = window.ultimaEvaluacion;
            const modal = `
                <div class="modal fade" id="modalDetalles" tabindex="-1">
                    <div class="modal-dialog modal-lg">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">Detalles del Scoring Crediticio</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body detalles-scoring">
                                ${Object.entries(data.desglose).map(([categoria, info]) => `
                                    <div class="mb-4">
                                        <h6 class="text-primary">${info.categoria}</h6>
                                        <div class="progress progress-custom mb-2">
                                            <div class="progress-bar" style="width: ${(info.puntos_ponderados / (info.puntos_maximos * info.peso)) * 100}%">
                                                ${info.puntos_ponderados.toFixed(1)} pts
                                            </div>
                                        </div>
                                        <small class="text-muted">
                                            ${info.puntos_obtenidos}/${info.puntos_maximos} puntos (Peso: ${(info.peso * 100)}%)
                                        </small>
                                        
                                        ${info.detalles ? info.detalles.map(detalle => `
                                            <div class="row mt-2">
                                                <div class="col-8">${detalle.factor}:</div>
                                                <div class="col-4 text-end">${detalle.puntos}/${detalle.maximo}</div>
                                            </div>
                                        `).join('') : ''}
                                    </div>
                                `).join('')}
                                
                                <div class="alert alert-success">
                                    <strong>Score Final: ${data.score} puntos</strong><br>
                                    <small>Calculado: ${data.fecha}</small>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            // Agregar modal al DOM
            document.body.insertAdjacentHTML('beforeend', modal);
            
            // Mostrar modal
            const modalElement = new bootstrap.Modal(document.getElementById('modalDetalles'));
            modalElement.show();
            
            // Limpiar modal al cerrar
            document.getElementById('modalDetalles').addEventListener('hidden.bs.modal', function() {
                this.remove();
            });
        }
    </script>
</body>
</html>
'''
TEMPLATE_CASOS = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Casos de Estudio - Simulador de Crédito</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .caso-card { transition: all 0.3s ease; cursor: pointer; }
        .caso-card:hover { transform: translateY(-5px); box-shadow: 0 8px 15px rgba(0,0,0,0.1); }
        .perfil-badge { position: absolute; top: 10px; right: 10px; }
        .resultado-preview { border-left: 4px solid #28a745; padding-left: 15px; }
        .score-display { font-size: 2rem; font-weight: bold; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="/">
                <i class="fas fa-users me-2"></i>Casos de Estudio
            </a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/">Inicio</a>
                <a class="nav-link" href="/simulador">Simulador</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="row mb-4">
            <div class="col-12 text-center">
                <h2><i class="fas fa-graduation-cap text-primary me-2"></i>Casos de Estudio Reales</h2>
                <p class="lead">Explore diferentes perfiles crediticios y analice los resultados del modelo</p>
            </div>
        </div>

        <div class="row">
            {% for caso_id, caso in casos.items() %}
            <div class="col-lg-4 mb-4">
                <div class="card caso-card h-100 position-relative" onclick="evaluarCaso('{{ caso_id }}')">
                    <span class="badge perfil-badge bg-{{ 'success' if 'alto' in caso_id else 'warning' if 'medio' in caso_id else 'info' }}">
                        {{ 'ALTO' if 'alto' in caso_id else 'MEDIO' if 'medio' in caso_id else 'BÁSICO' }}
                    </span>
                    
                    <div class="card-body">
                        <h5 class="card-title text-primary">
                            <i class="fas fa-user me-2"></i>{{ caso.nombre }}
                        </h5>
                        <p class="card-text text-muted">{{ caso.descripcion }}</p>
                        
                        <div class="row mb-3">
                            <div class="col-6">
                                <small class="text-muted">Ingresos:</small><br>
                                <strong>${{ "{:,}".format(caso.datos.ingresos_mensuales|int) }}</strong>
                            </div>
                            <div class="col-6">
                                <small class="text-muted">FICO Score:</small><br>
                                <strong>{{ caso.datos.fico_score }}</strong>
                            </div>
                        </div>
                        
                        <div class="row mb-3">
                            <div class="col-6">
                                <small class="text-muted">Ocupación:</small><br>
                                <strong>{{ caso.datos.ocupacion.replace('_', ' ').title() }}</strong>
                            </div>
                            <div class="col-6">
                                <small class="text-muted">Edad:</small><br>
                                <strong>{{ caso.datos.edad }} años</strong>
                            </div>
                        </div>
                        
                        <div id="resultado-{{ caso_id }}" class="resultado-preview" style="display: none;">
                            <!-- Los resultados aparecerán aquí -->
                        </div>
                        
                        <div class="text-center mt-3">
                            <button class="btn btn-primary" onclick="event.stopPropagation(); evaluarCaso('{{ caso_id }}')">
                                <i class="fas fa-calculator me-2"></i>Evaluar Caso
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
        
        <div class="row mt-5">
            <div class="col-12">
                <div class="card bg-light">
                    <div class="card-body">
                        <h5><i class="fas fa-lightbulb text-warning me-2"></i>Análisis Comparativo</h5>
                        <p>Estos casos muestran cómo diferentes variables afectan la evaluación crediticia:</p>
                        
                        <div class="row">
                            <div class="col-md-4">
                                <h6 class="text-success">Perfil Alto</h6>
                                <ul class="list-unstyled">
                                    <li><i class="fas fa-check text-success me-2"></i>Empleado público</li>
                                    <li><i class="fas fa-check text-success me-2"></i>FICO Score alto (720+)</li>
                                    <li><i class="fas fa-check text-success me-2"></i>Ingresos estables</li>
                                    <li><i class="fas fa-check text-success me-2"></i>Documentación completa</li>
                                </ul>
                            </div>
                            <div class="col-md-4">
                                <h6 class="text-warning">Perfil Medio</h6>
                                <ul class="list-unstyled">
                                    <li><i class="fas fa-check text-warning me-2"></i>Empleado privado</li>
                                    <li><i class="fas fa-check text-warning me-2"></i>FICO Score regular (650)</li>
                                    <li><i class="fas fa-check text-warning me-2"></i>Historial estándar</li>
                                    <li><i class="fas fa-check text-warning me-2"></i>Alguna documentación</li>
                                </ul>
                            </div>
                            <div class="col-md-4">
                                <h6 class="text-info">Perfil Básico</h6>
                                <ul class="list-unstyled">
                                    <li><i class="fas fa-check text-info me-2"></i>Trabajador independiente</li>
                                    <li><i class="fas fa-check text-info me-2"></i>FICO Score básico (600)</li>
                                    <li><i class="fas fa-check text-info me-2"></i>Ingresos variables</li>
                                    <li><i class="fas fa-check text-info me-2"></i>Documentación limitada</li>
                                </ul>
                            </div>
                        </div>
                        
                        <div class="text-center mt-3">
                            <a href="/simulador" class="btn btn-primary btn-lg">
                                <i class="fas fa-plus me-2"></i>Crear Tu Propio Caso
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        function evaluarCaso(casoId) {
            // Obtener datos del caso
            fetch(`/api/caso/${casoId}`)
                .then(response => response.json())
                .then(caso => {
                    // Evaluar el caso
                    return fetch('/api/evaluar', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(caso.datos)
                    });
                })
                .then(response => response.json())
                .then(resultado => {
                    if (resultado.success) {
                        mostrarResultadoCaso(casoId, resultado.data);
                    } else {
                        alert('Error: ' + resultado.error);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Error al evaluar el caso');
                });
        }
        
        function mostrarResultadoCaso(casoId, data) {
            const contenedor = document.getElementById(`resultado-${casoId}`);
            
            let html = '';
            let badgeClass = 'success';
            let iconClass = 'check-circle';
            
            if (!data.aprobado) {
                badgeClass = 'danger';
                iconClass = 'times-circle';
            } else if (data.score < 300) {
                badgeClass = 'warning';
                iconClass = 'exclamation-triangle';
            }
            
            if (data.aprobado) {
                html = `
                    <div class="mb-3">
                        <div class="d-flex align-items-center mb-2">
                            <i class="fas fa-${iconClass} text-${badgeClass} me-2"></i>
                            <span class="badge bg-${badgeClass}">APROBADO</span>
                        </div>
                        
                        <div class="row">
                            <div class="col-6">
                                <div class="score-display text-${badgeClass}">${data.score}</div>
                                <small class="text-muted">Score Final</small>
                            </div>
                            <div class="col-6">
                                <div class="h5">$${data.monto_aprobado.toLocaleString()}</div>
                                <small class="text-muted">Monto Aprobado</small>
                            </div>
                        </div>
                        
                        <div class="mt-2">
                            <small>
                                <strong>Tasa:</strong> ${(data.tasa_anual * 100).toFixed(1)}% anual<br>
                                <strong>Riesgo:</strong> ${data.nivel_riesgo}<br>
                                <strong>TDSR:</strong> ${(data.tdsr * 100).toFixed(1)}%
                            </small>
                        </div>
                        
                        <div class="mt-2">
                            <small class="text-muted">Plazos disponibles:</small><br>
                            ${data.opciones_plazo.filter(o => o.factible).map(opcion => 
                                `<span class="badge bg-outline-success me-1">${opcion.plazo}m</span>`
                            ).join('')}
                        </div>
                    </div>
                `;
            } else {
                html = `
                    <div class="mb-3">
                        <div class="d-flex align-items-center mb-2">
                            <i class="fas fa-${iconClass} text-${badgeClass} me-2"></i>
                            <span class="badge bg-${badgeClass}">RECHAZADO</span>
                        </div>
                        
                        <div class="score-display text-${badgeClass}">${data.score}</div>
                        <small class="text-muted">Score Final</small>
                        
                        <div class="mt-2">
                            <small class="text-danger">
                                <strong>Razón:</strong><br>
                                ${data.razon}
                            </small>
                        </div>
                    </div>
                `;
            }
            
            contenedor.innerHTML = html;
            contenedor.style.display = 'block';
            
            // Scroll suave al resultado
            contenedor.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
        
        // Evaluar todos los casos al cargar la página (opcional)
        document.addEventListener('DOMContentLoaded', function() {
            // Comentar esta línea si no quieres evaluación automática
            // ['perfil_alto', 'perfil_medio', 'perfil_basico'].forEach(caso => evaluarCaso(caso));
        });
    </script>
</body>
</html>
'''

# Puerto para Render
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
