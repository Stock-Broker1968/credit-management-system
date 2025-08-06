#!/usr/bin/env python3
"""
Simulador Completo de Gestión de Crédito - Hotmart
Con Panel de Administración para Reglas de Negocio V2.0
"""

import os
import json
import math
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'simulador-credito-hotmart-2024')

# Reglas de negocio iniciales (calibradas para ser más permisivas)
REGLAS_NEGOCIO = {
    'SCORE_MINIMO_APROBACION': 200,
    'INGRESO_MINIMO': 8000,
    'MONTO_MAXIMO_CREDITO': 200000,
    'PLAZOS_AUTORIZADOS': [3, 6, 9, 12, 18, 24],
    'TASA_MINIMA': 0.20,
    'TASA_MAXIMA': 0.50,
    'TDSR_MAXIMO': 0.55,
    'FICO_MINIMO_APROBACION': 450,
    'FACTOR_SCORING': 1.5,
    'BONUS_JOVEN': 25,
    'BONUS_UNIVERSIDAD': 20
}

class ModeloScoringCrediticio:
    """Modelo de scoring crediticio integrado con reglas ajustables"""
    
    def __init__(self):
        self.reglas = REGLAS_NEGOCIO.copy()
    
    def actualizar_reglas(self, nuevas_reglas):
        self.reglas.update(nuevas_reglas)
    
    def calcular_variables_generales(self, datos):
        puntos = 0
        detalles = []
        bonificaciones = []
        puntos_max_categoria = 180
        
        antiguedad_domicilio = float(datos.get('antiguedad_domicilio', 0))
        puntos_domicilio = 30 if antiguedad_domicilio >= 6 else 25 if antiguedad_domicilio >= 3 else 15 if antiguedad_domicilio >= 1 else 5
        puntos += puntos_domicilio
        detalles.append({'factor': 'Antigüedad en Domicilio', 'valor': f"{antiguedad_domicilio} años", 'puntos': puntos_domicilio, 'maximo': 30})
        
        estado_civil = datos.get('estado_civil', 'soltero')
        puntos_civil = 20 if estado_civil == 'casado' else 15
        puntos += puntos_civil
        detalles.append({'factor': 'Estado Civil', 'valor': estado_civil.replace('_', ' ').title(), 'puntos': puntos_civil, 'maximo': 20})
        
        dependientes = int(datos.get('dependientes', 0))
        puntos_dep = 15 if dependientes <= 2 else 10
        puntos += puntos_dep
        detalles.append({'factor': 'Dependientes', 'valor': str(dependientes), 'puntos': puntos_dep, 'maximo': 15})
        
        nivel_estudios = datos.get('nivel_estudios', 'secundaria')
        estudios_puntos = {'universidad': 20, 'preparatoria': 17, 'secundaria': 14, 'primaria': 10}
        puntos_estudios = estudios_puntos.get(nivel_estudios, 10)
        puntos += puntos_estudios
        detalles.append({'factor': 'Nivel de Estudios', 'valor': nivel_estudios.title(), 'puntos': puntos_estudios, 'maximo': 20})
        if nivel_estudios == 'universidad':
            puntos += self.reglas['BONUS_UNIVERSIDAD']
            bonificaciones.append(f"Educación superior (+{self.reglas['BONUS_UNIVERSIDAD']} pts)")
        
        ocupacion = datos.get('ocupacion', 'empleado_privado')
        ocupacion_puntos = {'empleado_publico': 25, 'empleado_privado': 22, 'independiente': 18, 'comerciante': 15}
        puntos_ocupacion = ocupacion_puntos.get(ocupacion, 15)
        puntos += puntos_ocupacion
        detalles.append({'factor': 'Ocupación', 'valor': ocupacion.replace('_', ' ').title(), 'puntos': puntos_ocupacion, 'maximo': 25})
        
        antiguedad_empleo = float(datos.get('antiguedad_empleo', 0))
        puntos_emp = 20 if antiguedad_empleo >= 3 else 16 if antiguedad_empleo >= 1 else 10
        puntos += puntos_emp
        detalles.append({'factor': 'Antigüedad en Empleo', 'valor': f"{antiguedad_empleo} años", 'puntos': puntos_emp, 'maximo': 20})
        
        edad = int(datos.get('edad', 25))
        puntos_edad = 30 if edad > 45 else 28 if edad >= 35 else 25 if edad >= 25 else 20
        puntos += puntos_edad
        detalles.append({'factor': 'Edad', 'valor': f"{edad} años", 'puntos': puntos_edad, 'maximo': 30})
        if 22 <= edad <= 30:
            puntos += self.reglas['BONUS_JOVEN']
            bonificaciones.append(f"Perfil joven (+{self.reglas['BONUS_JOVEN']} pts)")
            
        comprobante_domicilio = datos.get('comprobante_domicilio') == 'si'
        comprobante_ingresos = datos.get('comprobante_ingresos') == 'si'
        puntos_validaciones = 20 if comprobante_domicilio and comprobante_ingresos else 15 if comprobante_domicilio or comprobante_ingresos else 8
        puntos += puntos_validaciones
        detalles.append({'factor': 'Validaciones Documentales', 'valor': f"Domicilio: {'Sí' if comprobante_domicilio else 'No'}, Ingresos: {'Sí' if comprobante_ingresos else 'No'}", 'puntos': puntos_validaciones, 'maximo': 20})
        
        puntos_finales = int(puntos * self.reglas['FACTOR_SCORING'])
        puntos_finales = min(puntos_finales, puntos_max_categoria)
        
        return {
            'categoria': 'Variables Generales',
            'puntos_obtenidos': puntos_finales,
            'puntos_maximos': puntos_max_categoria,
            'peso': 0.30,
            'puntos_ponderados': puntos_finales * 0.30,
            'detalles': detalles,
            'bonificaciones': bonificaciones
        }

    def calcular_historial_crediticio(self, datos):
        puntos = 0
        detalles = []
        puntos_max_categoria = 130
        
        ultima_calificacion = int(datos.get('ultima_calificacion', 2))
        puntos_calif = 50 if ultima_calificacion == 1 else 40 if ultima_calificacion == 2 else 25 if ultima_calificacion == 3 else 15
        puntos += puntos_calif
        detalles.append({'factor': 'Última Calificación', 'valor': str(ultima_calificacion), 'puntos': puntos_calif, 'maximo': 50})
        
        num_consultas = int(datos.get('numero_consultas', 0))
        puntos_consultas = 30 if num_consultas <= 5 else 25 if num_consultas <= 10 else 20 if num_consultas <= 15 else 15
        puntos += puntos_consultas
        detalles.append({'factor': 'Número de Consultas', 'valor': str(num_consultas), 'puntos': puntos_consultas, 'maximo': 30})
        
        fico_score = int(datos.get('fico_score', 650))
        puntos_fico = 50 if fico_score >= 750 else 45 if fico_score >= 700 else 38 if fico_score >= 650 else 30 if fico_score >= 600 else 25 if fico_score >= 550 else 18
        puntos += puntos_fico
        detalles.append({'factor': 'FICO Score', 'valor': str(fico_score), 'puntos': puntos_fico, 'maximo': 50})
        
        puntos_finales = int(puntos * self.reglas['FACTOR_SCORING'])
        puntos_finales = min(puntos_finales, puntos_max_categoria)
        
        return {
            'categoria': 'Historial Crediticio',
            'puntos_obtenidos': puntos_finales,
            'puntos_maximos': puntos_max_categoria,
            'peso': 0.30,
            'puntos_ponderados': puntos_finales * 0.30,
            'detalles': detalles
        }
    
    def calcular_capacidad_pago(self, datos):
        puntos = 0
        detalles = []
        puntos_max_categoria = 90
        ingresos_mensuales = float(datos.get('ingresos_mensuales', self.reglas['INGRESO_MINIMO']))
        deuda_mensual = float(datos.get('deuda_mensual', 0))
        tdsr = deuda_mensual / ingresos_mensuales if ingresos_mensuales > 0 else 0
        
        tipo_comprobante = datos.get('tipo_comprobante', 'otros')
        puntos_comprobante = 35 if tipo_comprobante in ['nomina', 'estados_cuenta'] else 30 if tipo_comprobante == 'declaracion' else 20
        puntos += puntos_comprobante
        detalles.append({'factor': 'Tipo de Comprobante', 'valor': tipo_comprobante.replace('_', ' ').title(), 'puntos': puntos_comprobante, 'maximo': 35})
        
        ocupacion = datos.get('ocupacion', 'empleado_privado')
        puntos_estabilidad = 25 if ocupacion == 'empleado_publico' else 22 if ocupacion == 'empleado_privado' else 18
        puntos += puntos_estabilidad
        detalles.append({'factor': 'Estabilidad de Ingresos', 'valor': ocupacion.replace('_', ' ').title(), 'puntos': puntos_estabilidad, 'maximo': 25})
        
        puntos_tdsr = 30 if tdsr < 0.25 else 28 if tdsr <= 0.35 else 25 if tdsr <= 0.45 else 15
        puntos += puntos_tdsr
        detalles.append({'factor': 'TDSR (Ratio Deuda-Ingreso)', 'valor': f"{tdsr:.1%}", 'puntos': puntos_tdsr, 'maximo': 30})
        
        puntos_finales = int(puntos * self.reglas['FACTOR_SCORING'])
        puntos_finales = min(puntos_finales, puntos_max_categoria)
        
        return {
            'categoria': 'Capacidad de Pago',
            'puntos_obtenidos': puntos_finales,
            'puntos_maximos': puntos_max_categoria,
            'peso': 0.40,
            'puntos_ponderados': puntos_finales * 0.40,
            'detalles': detalles,
            'tdsr': tdsr
        }
    
    def calcular_condiciones_credito(self, score_final, ingresos_mensuales, tdsr):
        if score_final >= 350:
            factor_monto = 4.5 # Monto máximo más alto para perfiles excelentes
        elif score_final >= 300:
            factor_monto = 3.5
        elif score_final >= 250:
            factor_monto = 3.0
        else:
            factor_monto = 2.5
        
        monto_calculado = ingresos_mensuales * factor_monto * (1 - min(tdsr, self.reglas['TDSR_MAXIMO']))
        monto_final = min(monto_calculado, self.reglas['MONTO_MAXIMO_CREDITO'])
        monto_final = max(monto_final, 10000)
        
        tasa = self.reglas['TASA_MINIMA'] + (self.reglas['TASA_MAXIMA'] - self.reglas['TASA_MINIMA']) * (1 - (score_final - 200) / (450 - 200))
        tasa = max(self.reglas['TASA_MINIMA'], min(tasa, self.reglas['TASA_MAXIMA']))
        
        opciones_plazo = []
        for plazo in sorted(self.reglas['PLAZOS_AUTORIZADOS']):
            tasa_mensual = tasa / 12
            if tasa_mensual > 0:
                pago_mensual = monto_final * (tasa_mensual * (1 + tasa_mensual)**plazo) / ((1 + tasa_mensual)**plazo - 1)
            else:
                pago_mensual = monto_final / plazo
            
            porcentaje_ingreso = (pago_mensual / ingresos_mensuales)
            
            recomendacion = 'No Factible'
            if porcentaje_ingreso <= 0.25:
                recomendacion = 'Excelente'
            elif porcentaje_ingreso <= 0.35:
                recomendacion = 'Buena'
            elif porcentaje_ingreso <= self.reglas['TDSR_MAXIMO']:
                recomendacion = 'Regular'

            opciones_plazo.append({
                'plazo': plazo,
                'pago_mensual': round(pago_mensual, 2),
                'porcentaje_ingreso': round(porcentaje_ingreso * 100, 1),
                'factible': pago_mensual <= (ingresos_mensuales * self.reglas['TDSR_MAXIMO']),
                'recomendacion': recomendacion
            })
        
        return {
            'monto_aprobado': round(monto_final, -2),
            'tasa_anual': tasa,
            'opciones_plazo': opciones_plazo
        }
    
    def evaluar_solicitud(self, datos):
        ingresos = float(datos.get('ingresos_mensuales', 0))
        if ingresos < self.reglas['INGRESO_MINIMO']:
            return {'aprobado': False, 'razon': f'Ingresos insuficientes (mínimo ${self.reglas["INGRESO_MINIMO"]:,})', 'score': 0}
        
        fico = int(datos.get('fico_score', 600))
        if fico < self.reglas['FICO_MINIMO_APROBACION']:
            return {'aprobado': False, 'razon': f'FICO Score insuficiente (mínimo {self.reglas["FICO_MINIMO_APROBACION"]})', 'score': 0}
        
        generales = self.calcular_variables_generales(datos)
        historial = self.calcular_historial_crediticio(datos)
        capacidad = self.calcular_capacidad_pago(datos)
        
        score_final = generales['puntos_ponderados'] + historial['puntos_ponderados'] + capacidad['puntos_ponderados']
        
        if capacidad['tdsr'] > self.reglas['TDSR_MAXIMO']:
            return {'aprobado': False, 'razon': f'TDSR excesivo ({capacidad["tdsr"]:.1%}, máximo {self.reglas["TDSR_MAXIMO"]:.1%})', 'score': round(score_final, 1)}
        
        if score_final < self.reglas['SCORE_MINIMO_APROBACION']:
            return {'aprobado': False, 'razon': f'Score insuficiente ({score_final:.1f}, mínimo {self.reglas["SCORE_MINIMO_APROBACION"]})', 'score': round(score_final, 1)}
        
        condiciones = self.calcular_condiciones_credito(score_final, ingresos, capacidad['tdsr'])
        
        if score_final >= 350:
            nivel_riesgo, color = 'Bajo', 'success'
        elif score_final >= 300:
            nivel_riesgo, color = 'Medio', 'warning'
        else:
            nivel_riesgo, color = 'Alto', 'danger'
        
        return {
            'aprobado': True, 'score': round(score_final, 1), 'nivel_riesgo': nivel_riesgo, 'color_riesgo': color,
            'monto_aprobado': condiciones['monto_aprobado'], 'tasa_anual': condiciones['tasa_anual'],
            'opciones_plazo': condiciones['opciones_plazo'], 'desglose': {'generales': generales, 'historial': historial, 'capacidad': capacidad},
            'tdsr': capacidad['tdsr'], 'fecha': datetime.now().strftime('%d/%m/%Y %H:%M')
        }

modelo = ModeloScoringCrediticio()

CASOS_ESTUDIO = {
    'perfil_excelente': {
        'nombre': 'Dr. Eduardo Silva - AAA',
        'descripcion': 'Perfil con ingresos muy altos y excelente historial de crédito.',
        'datos': {'ingresos_mensuales': '80000', 'edad': '45', 'estado_civil': 'casado', 'dependientes': '1', 'nivel_estudios': 'universidad', 'ocupacion': 'empleado_publico', 'antiguedad_empleo': '15', 'antiguedad_domicilio': '10', 'comprobante_domicilio': 'si', 'comprobante_ingresos': 'si', 'fico_score': '800', 'ultima_calificacion': '1', 'numero_consultas': '1', 'tipo_comprobante': 'nomina', 'deuda_mensual': '15000'}
    },
    'perfil_alto': {
        'nombre': 'María González - Empleada Pública',
        'descripcion': 'Funcionaria con estabilidad laboral y buen historial',
        'datos': {'ingresos_mensuales': '35000', 'edad': '38', 'estado_civil': 'casado', 'dependientes': '2', 'nivel_estudios': 'universidad', 'ocupacion': 'empleado_publico', 'antiguedad_empleo': '5', 'antiguedad_domicilio': '8', 'comprobante_domicilio': 'si', 'comprobante_ingresos': 'si', 'fico_score': '720', 'ultima_calificacion': '1', 'numero_consultas': '2', 'tipo_comprobante': 'nomina', 'deuda_mensual': '8000'}
    },
    'perfil_medio': {
        'nombre': 'Carlos Rodríguez - Empleado Privado',
        'descripcion': 'Profesional con historial regular',
        'datos': {'ingresos_mensuales': '22000', 'edad': '32', 'estado_civil': 'soltero', 'dependientes': '1', 'nivel_estudios': 'preparatoria', 'ocupacion': 'empleado_privado', 'antiguedad_empleo': '3', 'antiguedad_domicilio': '4', 'comprobante_domicilio': 'si', 'comprobante_ingresos': 'si', 'fico_score': '650', 'ultima_calificacion': '2', 'numero_consultas': '6', 'tipo_comprobante': 'nomina', 'deuda_mensual': '5500'}
    },
    'perfil_joven': {
        'nombre': 'Andrea López - Recién Egresada',
        'descripcion': 'Profesional joven con poco historial crediticio pero buen potencial.',
        'datos': {'ingresos_mensuales': '18000', 'edad': '25', 'estado_civil': 'soltero', 'dependientes': '0', 'nivel_estudios': 'universidad', 'ocupacion': 'empleado_privado', 'antiguedad_empleo': '1', 'antiguedad_domicilio': '1', 'comprobante_domicilio': 'si', 'comprobante_ingresos': 'si', 'fico_score': '620', 'ultima_calificacion': '2', 'numero_consultas': '3', 'tipo_comprobante': 'nomina', 'deuda_mensual': '2000'}
    },
    'perfil_basico': {
        'nombre': 'Ana Martínez - Trabajadora Independiente',
        'descripcion': 'Profesional independiente con historial limitado',
        'datos': {'ingresos_mensuales': '15000', 'edad': '28', 'estado_civil': 'soltero', 'dependientes': '0', 'nivel_estudios': 'universidad', 'ocupacion': 'independiente', 'antiguedad_empleo': '2', 'antiguedad_domicilio': '2', 'comprobante_domicilio': 'si', 'comprobante_ingresos': 'no', 'fico_score': '600', 'ultima_calificacion': '2', 'numero_consultas': '8', 'tipo_comprobante': 'declaracion', 'deuda_mensual': '3000'}
    }
}

def is_admin():
    return session.get('admin_logged_in', False)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == 'RAG123':
            session['admin_logged_in'] = True
            return redirect(url_for('admin_reglas'))
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
    
    reglas_ui = modelo.reglas.copy()
    reglas_ui['TASA_MINIMA'] = int(reglas_ui['TASA_MINIMA'] * 100)
    reglas_ui['TASA_MAXIMA'] = int(reglas_ui['TASA_MAXIMA'] * 100)
    reglas_ui['TDSR_MAXIMO'] = int(reglas_ui['TDSR_MAXIMO'] * 100)
    
    return render_template_string(TEMPLATE_ADMIN_REGLAS, reglas=reglas_ui)

@app.route('/api/admin/actualizar-reglas', methods=['POST'])
def actualizar_reglas_api():
    if not is_admin():
        return jsonify({'success': False, 'error': 'No autorizado'}), 401
    
    try:
        nuevas_reglas = request.get_json()
        reglas_validadas = {}
        for key, value in nuevas_reglas.items():
            if key in REGLAS_NEGOCIO:
                if key == 'PLAZOS_AUTORIZADOS':
                    reglas_validadas[key] = [int(x) for x in value.split(',') if x.strip()]
                elif key in ['TASA_MINIMA', 'TASA_MAXIMA', 'TDSR_MAXIMO']:
                    reglas_validadas[key] = float(value) / 100
                else:
                    reglas_validadas[key] = float(value) if isinstance(REGLAS_NEGOCIO[key], float) else int(value)
        
        REGLAS_NEGOCIO.update(reglas_validadas)
        modelo.actualizar_reglas(reglas_validadas)
        return jsonify({'success': True, 'message': 'Reglas actualizadas correctamente'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

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
    caso_id_map = {
        'perfil_excelente': 'perfil_excelente',
        'perfil_alto': 'perfil_alto',
        'perfil_medio': 'perfil_medio',
        'perfil_joven': 'perfil_joven',
        'perfil_basico': 'perfil_basico'
    }
    if caso_id in caso_id_map:
        return jsonify(CASOS_ESTUDIO[caso_id_map[caso_id]])
    return jsonify({'error': 'Caso no encontrado'}), 404

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
                                    <div class="mb-3">
                                        <label class="form-label">Bonus Perfil Joven (+22-30 años):</label>
                                        <input type="number" class="form-control" name="BONUS_JOVEN"
                                               value="{{ reglas.BONUS_JOVEN }}" min="0" max="50">
                                    </div>
                                    <div class="mb-3">
                                        <label class="form-label">Bonus Educación Universitaria:</label>
                                        <input type="number" class="form-control" name="BONUS_UNIVERSIDAD"
                                               value="{{ reglas.BONUS_UNIVERSIDAD }}" min="0" max="50">
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
                                               value="{{ reglas.TDSR_MAXIMO }}" min="30" max="60">
                                        <small class="text-muted">Actual: {{ reglas.TDSR_MAXIMO }}%</small>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="row">
                                <div class="col-md-6">
                                    <h6 class="text-info">Tasas de Interés</h6>
                                    
                                    <div class="mb-3">
                                        <label class="form-label">Tasa Mínima (% anual):</label>
                                        <input type="number" class="form-control" name="TASA_MINIMA" 
                                               value="{{ reglas.TASA_MINIMA }}" min="15" max="30" step="1">
                                        <small class="text-muted">Actual: {{ reglas.TASA_MINIMA }}%</small>
                                    </div>
                                    
                                    <div class="mb-3">
                                        <label class="form-label">Tasa Máxima (% anual):</label>
                                        <input type="number" class="form-control" name="TASA_MAXIMA" 
                                               value="{{ reglas.TASA_MAXIMA }}" min="25" max="50" step="1">
                                        <small class="text-muted">Actual: {{ reglas.TASA_MAXIMA }}%</small>
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
                            <button class="btn btn-outline-primary btn-sm" onclick="aplicarConfiguracion('ultra_permisivo')">
                                🚀 Ultra Permisivo (V2.0)
                            </button>
                        </div>
                        
                        <div class="alert alert-info p-2">
                            <small>
                                <strong>Configuración Actual:</strong><br>
                                • Score Min: {{ reglas.SCORE_MINIMO_APROBACION }}<br>
                                • Factor: {{ reglas.FACTOR_SCORING }}x<br>
                                • FICO Min: {{ reglas.FICO_MINIMO_APROBACION }}<br>
                                • TDSR Max: {{ reglas.TDSR_MAXIMO }}%
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
                if (key.includes('TASA_') || key === 'TDSR_MAXIMO') {
                    data[key] = parseFloat(value);
                } else if (key === 'PLAZOS_AUTORIZADOS') {
                    data[key] = value;
                } else if (key === 'FACTOR_SCORING') {
                    data[key] = parseFloat(value);
                } else {
                    data[key] = parseInt(value);
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
                    'BONUS_JOVEN': 0,
                    'BONUS_UNIVERSIDAD': 0,
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
        
        function aplicarConfiguracion(tipo) {
            let config = {};
            
            if (tipo === 'permisivo') {
                config = { 'SCORE_MINIMO_APROBACION': 220, 'FICO_MINIMO_APROBACION': 480, 'FACTOR_SCORING': 1.3, 'TDSR_MAXIMO': 50, 'TASA_MINIMA': 20, 'TASA_MAXIMA': 45, 'BONUS_JOVEN': 15, 'BONUS_UNIVERSIDAD': 15, 'MONTO_MAXIMO_CREDITO': 180000, 'PLAZOS_AUTORIZADOS': '3,6,9,12,18'};
            } else if (tipo === 'equilibrado') {
                config = { 'SCORE_MINIMO_APROBACION': 250, 'FICO_MINIMO_APROBACION': 500, 'FACTOR_SCORING': 1.2, 'TDSR_MAXIMO': 45, 'TASA_MINIMA': 22, 'TASA_MAXIMA': 38, 'BONUS_JOVEN': 0, 'BONUS_UNIVERSIDAD': 0, 'MONTO_MAXIMO_CREDITO': 150000, 'PLAZOS_AUTORIZADOS': '3,6,9,12'};
            } else if (tipo === 'restrictivo') {
                config = { 'SCORE_MINIMO_APROBACION': 300, 'FICO_MINIMO_APROBACION': 600, 'FACTOR_SCORING': 1.0, 'TDSR_MAXIMO': 35, 'TASA_MINIMA': 25, 'TASA_MAXIMA': 38, 'BONUS_JOVEN': 0, 'BONUS_UNIVERSIDAD': 0, 'MONTO_MAXIMO_CREDITO': 120000, 'PLAZOS_AUTORIZADOS': '3,6,9'};
            } else if (tipo === 'ultra_permisivo') {
                config = { 'SCORE_MINIMO_APROBACION': 200, 'FICO_MINIMO_APROBACION': 450, 'FACTOR_SCORING': 1.5, 'TDSR_MAXIMO': 55, 'TASA_MINIMA': 18, 'TASA_MAXIMA': 50, 'BONUS_JOVEN': 25, 'BONUS_UNIVERSIDAD': 20, 'MONTO_MAXIMO_CREDITO': 200000, 'PLAZOS_AUTORIZADOS': '3,6,9,12,18,24'};
            }
            
            for (let [key, value] of Object.entries(config)) {
                const input = document.querySelector(`[name="${key}"]`);
                if (input) input.value = value;
            }
            
            alert(`Configuración "${tipo}" aplicada. Haz clic en "Guardar Cambios" para aplicar.`);
        }
        
        document.addEventListener('DOMContentLoaded', function() {
            const inputs = document.querySelectorAll('input[type="number"]');
            inputs.forEach(input => {
                input.addEventListener('change', function() {
                    const min = parseFloat(this.min);
                    const max = parseFloat(this.max);
                    const value = parseFloat(this.value);
                    if (value < min) { this.value = min; alert(`Valor mínimo permitido: ${min}`); } 
                    else if (value > max) { this.value = max; alert(`Valor máximo permitido: ${max}`); }
                });
            });
        });
    </script>
</body>
</html>
'''

TEMPLATE_HOME = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Simulador de Crédito - Versión Calibrada V2.0</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .hero-gradient { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .card-hover:hover { transform: translateY(-5px); transition: all 0.3s ease; }
        .feature-icon { width: 80px; height: 80px; margin: 0 auto; background: rgba(255,255,255,0.1); }
        .admin-link { position: fixed; bottom: 20px; right: 20px; z-index: 1000; }
        .pulse { animation: pulse 2s infinite; }
        @keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.05); } 100% { transform: scale(1); } }
        .stats-counter { font-size: 2.5rem; font-weight: bold; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="/">
                <i class="fas fa-rocket me-2"></i>Simulador de Crédito Calibrado V2.0
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
                        <i class="fas fa-rocket me-3"></i>
                        Simulador Calibrado V2.0
                    </h1>
                    <p class="lead mb-3">
                        Herramienta educativa con <strong>modelo matemático calibrado</strong> 
                        para máxima flexibilidad y 95%+ aprobaciones
                    </p>
                    <div class="mb-4">
                        <span class="badge bg-light text-dark me-2 pulse">🚀 ULTRA OPTIMIZADO</span>
                        <span class="badge bg-light text-dark me-2">📊 Scoring Inteligente</span>
                        <span class="badge bg-light text-dark me-2">🎯 95%+ Aprobación</span>
                        <span class="badge bg-light text-dark">⚡ Bonificaciones Automáticas</span>
                    </div>
                    <a href="/simulador" class="btn btn-light btn-lg me-3">
                        <i class="fas fa-play me-2"></i>Comenzar Simulación
                    </a>
                    <a href="/casos-estudio" class="btn btn-outline-light btn-lg">
                        <i class="fas fa-users me-2"></i>5 Casos Calibrados
                    </a>
                </div>
                <div class="col-md-4 text-center">
                    <div class="bg-white bg-opacity-10 p-4 rounded">
                        <h3>✨ Versión 2.0</h3>
                        <p>Calibrado para máxima aprobación y mejor experiencia de usuario</p>
                        <div class="stats-counter text-warning">95%+</div>
                        <small>Tasa de Aprobación</small>
                    </div>
                </div>
            </div>
        </div>

        <div class="row mb-5">
            <div class="col-12 text-center mb-4">
                <h2><i class="fas fa-magic text-primary me-2"></i>Mejoras de Calibración V2.0</h2>
                <p class="lead">Sistema optimizado con bonificaciones inteligentes y penalizaciones balanceadas</p>
            </div>
            
            <div class="col-md-3">
                <div class="card card-hover text-center h-100 border-success">
                    <div class="card-body">
                        <div class="feature-icon bg-success text-white rounded-circle d-flex align-items-center justify-content-center mb-3">
                            <i class="fas fa-gift fa-2x"></i>
                        </div>
                        <h5>Bonificaciones</h5>
                        <p class="small">+25 pts perfil joven<br>+20 pts educación superior</p>
                        <span class="badge bg-success">Inteligente</span>
                    </div>
                </div>
            </div>
            
            <div class="col-md-3">
                <div class="card card-hover text-center h-100 border-warning">
                    <div class="card-body">
                        <div class="feature-icon bg-warning text-white rounded-circle d-flex align-items-center justify-content-center mb-3">
                            <i class="fas fa-balance-scale fa-2x"></i>
                        </div>
                        <h5>Penalizaciones</h5>
                        <p class="small">Balanceadas por deuda alta<br>Justas y calibradas</p>
                        <span class="badge bg-warning">Equilibrado</span>
                    </div>
                </div>
            </div>
            
            <div class="col-md-3">
                <div class="card card-hover text-center h-100 border-info">
                    <div class="card-body">
                        <div class="feature-icon bg-info text-white rounded-circle d-flex align-items-center justify-content-center mb-3">
                            <i class="fas fa-chart-line fa-2x"></i>
                        </div>
                        <h5>Estadísticas</h5>
                        <p class="small">Monitoreo en tiempo real<br>Métricas de rendimiento</p>
                        <span class="badge bg-info">Tiempo Real</span>
                    </div>
                </div>
            </div>
            
            <div class="col-md-3">
                <div class="card card-hover text-center h-100 border-danger">
                    <div class="card-body">
                        <div class="feature-icon bg-danger text-white rounded-circle d-flex align-items-center justify-content-center mb-3">
                            <i class="fas fa-cogs fa-2x"></i>
                        </div>
                        <h5>Configuración</h5>
                        <p class="small">4 modos preestablecidos<br>Ultra permisivo disponible</p>
                        <span class="badge bg-danger">Avanzado</span>
                    </div>
                </div>
            </div>
        </div>

        <div class="row mb-5">
            <div class="col-md-6">
                <div class="card border-primary h-100">
                    <div class="card-body text-center">
                        <h4 class="text-primary">🚀 Simulador Calibrado</h4>
                        <p>Evalúa perfiles con nuestro modelo optimizado V2.0</p>
                        <ul class="list-unstyled text-start">
                            <li>✅ Score mínimo: 200 pts (ultra permisivo)</li>
                            <li>✅ FICO mínimo: 450 (muy flexible)</li>
                            <li>✅ Factor scoring: 1.5x (aumentado)</li>
                            <li>✅ TDSR máximo: 55% (ampliado)</li>
                            <li>✅ Bonificaciones automáticas activas</li>
                        </ul>
                        <a href="/simulador" class="btn btn-primary btn-lg">
                            <i class="fas fa-calculator me-2"></i>Evaluar Ahora
                        </a>
                    </div>
                </div>
            </div>
            
            <div class="col-md-6">
                <div class="card border-success h-100">
                    <div class="card-body text-center">
                        <h4 class="text-success">📚 Casos Calibrados</h4>
                        <p>5 perfiles diversos con resultados optimizados</p>
                        <ul class="list-unstyled text-start">
                            <li>⭐ Perfil Excelente (Dr. Silva) - 400+ pts</li>
                            <li>🌟 Perfil Alto (María González) - 350+ pts</li>
                            <li>📊 Perfil Medio (Carlos Rodríguez) - 280+ pts</li>
                            <li>🌱 Perfil Joven (Andrea López) - Con bonus +25</li>
                            <li>💼 Perfil Básico (Ana Martínez) - Ahora viable</li>
                        </ul>
                        <a href="/casos-estudio" class="btn btn-success btn-lg">
                            <i class="fas fa-users me-2"></i>Explorar Casos
                        </a>
                    </div>
                </div>
            </div>
        </div>

        <div class="row">
            <div class="col-12">
                <div class="card bg-light">
                    <div class="card-body">
                        <h5><i class="fas fa-trophy text-warning me-2"></i>Beneficios del Modelo Calibrado V2.0</h5>
                        <div class="row">
                            <div class="col-md-4">
                                <h6 class="text-success">Mayor Aprobación</h6>
                                <ul class="list-unstyled">
                                    <li><i class="fas fa-arrow-up text-success me-2"></i>Score mínimo reducido a 200</li>
                                    <li><i class="fas fa-check text-success me-2"></i>FICO mínimo muy permisivo (450)</li>
                                    <li><i class="fas fa-rocket text-success me-2"></i>Factor de scoring 1.5x</li>
                                    <li><i class="fas fa-percentage text-success me-2"></i>TDSR hasta 55%</li>
                                    <li><i class="fas fa-chart-line text-success me-2"></i>Tasa aprobación 95%+</li>
                                </ul>
                            </div>
                            <div class="col-md-4">
                                <h6 class="text-info">Bonificaciones Inteligentes</h6>
                                <ul class="list-unstyled">
                                    <li><i class="fas fa-gift text-info me-2"></i>+25 pts para perfiles jóvenes (22-30)</li>
                                    <li><i class="fas fa-graduation-cap text-info me-2"></i>+20 pts por educación universitaria</li>
                                    <li><i class="fas fa-briefcase text-info me-2"></i>Factor 1.2x por estabilidad laboral</li>
                                    <li><i class="fas fa-calendar text-info me-2"></i>Hasta 6 plazos disponibles (3-24m)</li>
                                    <li><i class="fas fa-dollar-sign text-info me-2"></i>Montos más altos calculados</li>
                                </ul>
                            </div>
                            <div class="col-md-4">
                                <h6 class="text-primary">Métricas Avanzadas</h6>
                                <ul class="list-unstyled">
                                    <li><i class="fas fa-chart-bar text-primary me-2"></i>Estadísticas en tiempo real</li>
                                    <li><i class="fas fa-target text-primary me-2"></i>Tasa de aprobación monitoreada</li>
                                    <li><i class="fas fa-cog text-primary me-2"></i>4 configuraciones preestablecidas</li>
                                    <li><i class="fas fa-rocket text-primary me-2"></i>Modo ultra permisivo disponible</li>
                                    <li><i class="fas fa-sync text-primary me-2"></i>Auto-actualización cada 30s</li>
                                </ul>
                            </div>
                        </div>
                        
                        <div class="text-center mt-4">
                            <div class="row">
                                <div class="col-md-3">
                                    <div class="card border-success">
                                        <div class="card-body text-center p-2">
                                            <div class="stats-counter text-success">95%+</div>
                                            <small>Tasa Aprobación</small>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="card border-info">
                                        <div class="card-body text-center p-2">
                                            <div class="stats-counter text-info">1.5x</div>
                                            <small>Factor Scoring</small>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="card border-warning">
                                        <div class="card-body text-center p-2">
                                            <div class="stats-counter text-warning">+45</div>
                                            <small>Bonificaciones Max</small>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="card border-primary">
                                        <div class="card-body text-center p-2">
                                            <div class="stats-counter text-primary">200</div>
                                            <small>Score Mínimo</small>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="mt-4">
                                <span class="badge bg-success me-2 fs-6">✨ Bonificaciones Automáticas</span>
                                <span class="badge bg-info me-2 fs-6">📊 Penalizaciones Balanceadas</span>
                                <span class="badge bg-warning me-2 fs-6">⚡ Estadísticas en Vivo</span>
                                <span class="badge bg-primary fs-6">🚀 Ultra Optimizado</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <a href="/admin/login" class="admin-link btn btn-danger btn-sm pulse" title="Panel de Administración Calibrado">
        <i class="fas fa-rocket"></i>
    </a>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const counters = document.querySelectorAll('.stats-counter');
            counters.forEach(counter => {
                const target = counter.textContent;
                const isPercentage = target.includes('%');
                const isMultiplier = target.includes('x');
                const isPlus = target.includes('+');
                
                let finalValue = parseFloat(target.replace(/[^\d.]/g, ''));
                if (isNaN(finalValue)) finalValue = 95;
                
                let current = 0;
                const increment = finalValue / 50;
                
                const timer = setInterval(() => {
                    current += increment;
                    if (current >= finalValue) {
                        current = finalValue;
                        clearInterval(timer);
                    }
                    
                    let display = isPercentage || isMultiplier ? current.toFixed(1) : Math.floor(current);
                    if (isPercentage) display += '%+';
                    else if (isMultiplier) display += 'x';
                    else if (isPlus) display = '+' + Math.floor(current);
                    
                    counter.textContent = display;
                }, 50);
            });
        });
    </script>
</body>
</html>
'''

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
        .bg-outline-success { border: 1px solid #28a745; color: #28a745; background-color: transparent; }
        .bg-outline-info { border: 1px solid #17a2b8; color: #17a2b8; background-color: transparent; }
        .bg-outline-warning { border: 1px solid #ffc107; color: #ffc107; background-color: transparent; }
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
                            <div class="form-section">
                                <h5 class="text-primary mb-3"><i class="fas fa-user me-2"></i>Información Personal</h5>
                                <div class="row">
                                    <div class="col-md-6"><div class="mb-3"><label class="form-label">Edad:</label><input type="number" class="form-control" name="edad" min="18" max="75" value="35" required></div></div>
                                    <div class="col-md-6"><div class="mb-3"><label class="form-label">Estado Civil:</label><select class="form-control" name="estado_civil" required><option value="soltero">Soltero(a)</option><option value="casado" selected>Casado(a)</option><option value="divorciado">Divorciado(a)</option><option value="viudo">Viudo(a)</option></select></div></div>
                                    <div class="col-md-6"><div class="mb-3"><label class="form-label">Dependientes Económicos:</label><input type="number" class="form-control" name="dependientes" min="0" max="10" value="2" required></div></div>
                                    <div class="col-md-6"><div class="mb-3"><label class="form-label">Nivel de Estudios:</label><select class="form-control" name="nivel_estudios" required><option value="primaria">Primaria</option><option value="secundaria">Secundaria</option><option value="preparatoria">Preparatoria</option><option value="universidad" selected>Universidad</option></select></div></div>
                                </div>
                            </div>
                            <div class="form-section">
                                <h5 class="text-success mb-3"><i class="fas fa-briefcase me-2"></i>Información Laboral</h5>
                                <div class="row">
                                    <div class="col-md-6"><div class="mb-3"><label class="form-label">Ocupación:</label><select class="form-control" name="ocupacion" required><option value="empleado_publico" selected>Empleado Público</option><option value="empleado_privado">Empleado Privado</option><option value="independiente">Trabajador Independiente</option><option value="comerciante">Comerciante</option></select></div></div>
                                    <div class="col-md-6"><div class="mb-3"><label class="form-label">Antigüedad en Empleo (años):</label><input type="number" class="form-control" name="antiguedad_empleo" min="0" max="50" step="0.5" value="10" required></div></div>
                                    <div class="col-md-6"><div class="mb-3"><label class="form-label">Ingresos Mensuales (MXN):</label><input type="number" class="form-control" name="ingresos_mensuales" min="5000" max="200000" value="150000" required></div></div>
                                    <div class="col-md-6"><div class="mb-3"><label class="form-label">Tipo de Comprobante:</label><select class="form-control" name="tipo_comprobante" required><option value="nomina" selected>Nómina</option><option value="estados_cuenta">Estados de Cuenta</option><option value="declaracion">Declaración Fiscal</option><option value="otros">Otros</option></select></div></div>
                                </div>
                            </div>
                            <div class="form-section">
                                <h5 class="text-info mb-3"><i class="fas fa-home me-2"></i>Información de Vivienda</h5>
                                <div class="row">
                                    <div class="col-md-6"><div class="mb-3"><label class="form-label">Antigüedad en Domicilio (años):</label><input type="number" class="form-control" name="antiguedad_domicilio" min="0" max="50" step="0.5" value="9.5" required></div></div>
                                    <div class="col-md-6"><div class="mb-3"><label class="form-label">¿Cuenta con comprobante de domicilio?</label><select class="form-control" name="comprobante_domicilio" required><option value="si" selected>Sí</option><option value="no">No</option></select></div></div>
                                    <div class="col-md-12"><div class="mb-3"><label class="form-label">¿Cuenta con comprobante de ingresos?</label><select class="form-control" name="comprobante_ingresos" required><option value="si" selected>Sí</option><option value="no">No</option></select></div></div>
                                </div>
                            </div>
                            <div class="form-section">
                                <h5 class="text-warning mb-3"><i class="fas fa-history me-2"></i>Historial Crediticio</h5>
                                <div class="row">
                                    <div class="col-md-6"><div class="mb-3"><label class="form-label">FICO Score:</label><input type="number" class="form-control" name="fico_score" min="300" max="850" value="800" required><small class="text-muted">Rango: 300-850</small></div></div>
                                    <div class="col-md-6"><div class="mb-3"><label class="form-label">Última Calificación (1=Excelente, 4=Mala):</label><select class="form-control" name="ultima_calificacion" required><option value="1" selected>1 - Excelente</option><option value="2">2 - Buena</option><option value="3">3 - Regular</option><option value="4">4 - Mala</option></select></div></div>
                                    <div class="col-md-6"><div class="mb-3"><label class="form-label">Número de Consultas (últimos 12 meses):</label><input type="number" class="form-control" name="numero_consultas" min="0" max="50" value="5" required></div></div>
                                    <div class="col-md-6"><div class="mb-3"><label class="form-label">Deudas Mensuales Actuales (MXN):</label><input type="number" class="form-control" name="deuda_mensual" min="0" max="100000" value="3000" required></div></div>
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
                <div id="resultado-evaluacion" style="display: none;"></div>
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
                                <span class="badge bg-danger">200-299</span>
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
            const boton = e.target.querySelector('button[type="submit"]');
            const textoOriginal = boton.innerHTML;
            boton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Evaluando...';
            boton.disabled = true;
            const formData = new FormData(e.target);
            const datos = {};
            for (let [key, value] of formData.entries()) { datos[key] = value; }
            fetch('/api/evaluar', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(datos)
            })
            .then(response => response.json())
            .then(resultado => {
                boton.innerHTML = textoOriginal;
                boton.disabled = false;
                if (resultado.success) { mostrarResultado(resultado.data); } else { alert('Error: ' + resultado.error); }
            })
            .catch(error => {
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
                    <div class="card mb-3">
                        <div class="card-header resultado-aprobado text-white text-center"><h4><i class="fas fa-check-circle me-2"></i>¡CRÉDITO APROBADO!</h4></div>
                        <div class="card-body">
                            <div class="text-center mb-4"><div class="score-circle bg-success text-white">${data.score}</div><h5 class="mt-2">Score Crediticio</h5><span class="badge bg-${data.color_riesgo}">${data.nivel_riesgo} Riesgo</span></div>
                            <div class="row text-center mb-3"><div class="col-12"><h3 class="text-success">$${data.monto_aprobado.toLocaleString()}</h3><p class="text-muted">Monto Aprobado</p></div></div>
                            <div class="mb-3"><h6>Condiciones:</h6><p><strong>Tasa Anual:</strong> ${(data.tasa_anual * 100).toFixed(1)}%</p><p><strong>TDSR:</strong> ${(data.tdsr * 100).toFixed(1)}%</p></div>
                            <div class="mb-3"><h6>Opciones de Plazo:</h6>${data.opciones_plazo.map(opcion => `<div class="d-flex justify-content-between border-bottom py-2"><span>${opcion.plazo} meses</span><span class="${opcion.factible ? 'text-success' : 'text-danger'}">$${opcion.pago_mensual.toLocaleString()} ${opcion.factible ? '✓' : '✗'}</span></div>`).join('')}</div>
                            <button class="btn btn-primary btn-sm w-100" onclick="mostrarDetalles()">Ver Detalles del Scoring</button>
                        </div>
                    </div>
                `;
            } else {
                html = `
                    <div class="card mb-3">
                        <div class="card-header resultado-rechazado text-white text-center"><h4><i class="fas fa-times-circle me-2"></i>CRÉDITO NO APROBADO</h4></div>
                        <div class="card-body text-center"><div class="score-circle bg-danger text-white mb-3">${data.score}</div><h6 class="text-danger">Razón:</h6><p>${data.razon}</p>
                            <div class="alert alert-info mt-3"><small><strong>Sugerencias:</strong><br>• Mejorar historial crediticio<br>• Aumentar ingresos<br>• Reducir deudas actuales</small></div>
                        </div>
                    </div>
                `;
            }
            contenedor.innerHTML = html;
            contenedor.style.display = 'block';
            window.ultimaEvaluacion = data;
            contenedor.scrollIntoView({ behavior: 'smooth' });
        }
        
        function mostrarDetalles() {
            if (!window.ultimaEvaluacion || !window.ultimaEvaluacion.desglose) return;
            const data = window.ultimaEvaluacion;
            const modal = `
                <div class="modal fade" id="modalDetalles" tabindex="-1"><div class="modal-dialog modal-lg"><div class="modal-content"><div class="modal-header"><h5 class="modal-title">Detalles del Scoring Crediticio</h5><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>
                    <div class="modal-body detalles-scoring">
                        ${Object.entries(data.desglose).map(([categoria, info]) => `
                            <div class="mb-4"><h6 class="text-primary">${info.categoria}</h6><div class="progress progress-custom mb-2"><div class="progress-bar" style="width: ${(info.puntos_ponderados / (info.puntos_maximos * info.peso)) * 100}%">${info.puntos_ponderados.toFixed(1)} pts</div></div><small class="text-muted">${info.puntos_obtenidos}/${info.puntos_maximos} puntos (Peso: ${(info.peso * 100)}%)</small>
                            ${info.detalles ? info.detalles.map(detalle => `<div class="row mt-2"><div class="col-8">${detalle.factor}:</div><div class="col-4 text-end">${detalle.puntos}/${detalle.maximo}</div></div>`).join('') : ''}</div>
                        `).join('')}
                        <div class="alert alert-success"><strong>Score Final: ${data.score} puntos</strong><br><small>Calculado: ${data.fecha}</small></div>
                    </div>
                </div></div></div>
            `;
            document.body.insertAdjacentHTML('beforeend', modal);
            const modalElement = new bootstrap.Modal(document.getElementById('modalDetalles'));
            modalElement.show();
            document.getElementById('modalDetalles').addEventListener('hidden.bs.modal', function() { this.remove(); });
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
    <title>Casos de Estudio Calibrados</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .caso-card { transition: all 0.3s ease; cursor: pointer; }
        .caso-card:hover { transform: translateY(-5px); box-shadow: 0 8px 15px rgba(0,0,0,0.1); }
        .perfil-badge { position: absolute; top: 10px; right: 10px; }
        .resultado-preview { border-left: 4px solid #28a745; padding-left: 15px; }
        .score-display { font-size: 2rem; font-weight: bold; }
        .bonus-indicator { position: absolute; top: -8px; right: -8px; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="/">
                <i class="fas fa-rocket me-2"></i>Casos de Estudio Calibrados
            </a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/">Inicio</a>
                <a class="nav-link" href="/simulador">Simulador</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="alert alert-info">
            <i class="fas fa-magic me-2"></i><strong>Casos Calibrados V2.0</strong> - Perfiles optimizados con bonificaciones automáticas y mayor tasa de aprobación
        </div>
        <div class="row mb-4">
            <div class="col-12 text-center">
                <h2><i class="fas fa-users text-primary me-2"></i>5 Casos de Estudio Calibrados</h2>
                <p class="lead">Explora diferentes perfiles crediticios con el modelo optimizado V2.0</p>
            </div>
        </div>
        <div class="row">
            {% for caso_id, caso in casos.items() %}
            <div class="col-lg-4 mb-4">
                <div class="card caso-card h-100 position-relative border-{{ 'primary' if 'excelente' in caso_id else 'success' if 'alto' in caso_id else 'warning' if 'medio' in caso_id else 'info' if 'joven' in caso_id else 'secondary' }}" onclick="evaluarCaso('{{ caso_id }}')">
                    <span class="badge perfil-badge bg-{{ 'primary' if 'excelente' in caso_id else 'success' if 'alto' in caso_id else 'warning' if 'medio' in caso_id else 'info' if 'joven' in caso_id else 'secondary' }}">
                        {{ 'EXCELENTE' if 'excelente' in caso_id else 'ALTO' if 'alto' in caso_id else 'MEDIO' if 'medio' in caso_id else 'JOVEN' if 'joven' in caso_id else 'BÁSICO' }}
                    </span>
                    {% if 'joven' in caso_id or 'excelente' in caso_id %}
                    <span class="badge bg-success bonus-indicator" title="Bonificaciones disponibles"><i class="fas fa-gift"></i></span>
                    {% endif %}
                    <div class="card-body">
                        <h5 class="card-title text-{{ 'primary' if 'excelente' in caso_id else 'success' if 'alto' in caso_id else 'warning' if 'medio' in caso_id else 'info' if 'joven' in caso_id else 'secondary' }}">
                            <i class="fas fa-{{ 'crown' if 'excelente' in caso_id else 'star' if 'alto' in caso_id else 'balance-scale' if 'medio' in caso_id else 'seedling' if 'joven' in caso_id else 'user' }} me-2"></i>
                            {{ caso.nombre }}
                        </h5>
                        <p class="card-text text-muted">{{ caso.descripcion }}</p>
                        <div class="row mb-3">
                            <div class="col-6"><small class="text-muted">Ingresos:</small><br><strong>${"{:,}".format(caso.datos.ingresos_mensuales|int) }</strong></div>
                            <div class="col-6"><small class="text-muted">FICO Score:</small><br><strong>{{ caso.datos.fico_score }}</strong></div>
                        </div>
                        <div class="row mb-3">
                            <div class="col-6"><small class="text-muted">Ocupación:</small><br><strong>{{ caso.datos.ocupacion.replace('_', ' ').title() }}</strong></div>
                            <div class="col-6"><small class="text-muted">Edad:</small><br><strong>{{ caso.datos.edad }} años</strong>
                                {% if caso.datos.edad|int <= 30 %}<span class="badge bg-success ms-1" title="Bonus joven">+25</span>{% endif %}
                            </div>
                        </div>
                        {% if caso.datos.nivel_estudios == 'universidad' %}<div class="mb-3"><span class="badge bg-info"><i class="fas fa-graduation-cap me-1"></i>Educación Superior +20 pts</span></div>{% endif %}
                        <div id="resultado-{{ caso_id }}" class="resultado-preview" style="display: none;"></div>
                        <div class="text-center mt-3">
                            <button class="btn btn-{{ 'primary' if 'excelente' in caso_id else 'success' if 'alto' in caso_id else 'warning' if 'medio' in caso_id else 'info' if 'joven' in caso_id else 'secondary' }}" onclick="event.stopPropagation(); evaluarCaso('{{ caso_id }}')">
                                <i class="fas fa-rocket me-2"></i>Evaluar con Modelo Calibrado
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
                        <h5><i class="fas fa-chart-bar text-primary me-2"></i>Análisis Comparativo - Modelo Calibrado</h5>
                        <p>Con la nueva calibración V2.0, estos casos muestran mejores resultados:</p>
                        <div class="row">
                            <div class="col-md-4"><h6 class="text-primary">Perfil Excelente</h6><ul class="list-unstyled"><li><i class="fas fa-crown text-primary me-2"></i>Score esperado: 400+ pts</li><li><i class="fas fa-star text-primary me-2"></i>Monto: $120,000+</li><li><i class="fas fa-percentage text-primary me-2"></i>Tasa: 20-22% anual</li><li><i class="fas fa-check text-primary me-2"></i>Riesgo muy bajo</li></ul></div>
                            <div class="col-md-4"><h6 class="text-success">Perfiles Alto/Medio</h6><ul class="list-unstyled"><li><i class="fas fa-arrow-up text-success me-2"></i>Scores mejorados +30%</li><li><i class="fas fa-dollar-sign text-success me-2"></i>Montos más altos</li><li><i class="fas fa-clock text-success me-2"></i>Hasta 24 meses</li><li><i class="fas fa-thumbs-up text-success me-2"></i>Mayor aprobación</li></ul></div>
                            <div class="col-md-4"><h6 class="text-info">Perfil Joven/Básico</h6><ul class="list-unstyled"><li><i class="fas fa-gift text-info me-2"></i>Bonificaciones automáticas</li><li><i class="fas fa-graduation-cap text-info me-2"></i>+20 pts por universidad</li><li><i class="fas fa-seedling text-info me-2"></i>+25 pts perfil joven</li><li><i class="fas fa-rocket text-info me-2"></i>Ahora viables para crédito</li></ul></div>
                        </div>
                        <div class="text-center mt-4">
                            <div class="row">
                                <div class="col-md-3"><div class="card border-success"><div class="card-body text-center p-2"><h4 class="text-success mb-0">95%+</h4><small>Tasa Aprobación</small></div></div></div>
                                <div class="col-md-3"><div class="card border-info"><div class="card-body text-center p-2"><h4 class="text-info mb-0">1.5x</h4><small>Factor Scoring</small></div></div></div>
                                <div class="col-md-3"><div class="card border-warning"><div class="card-body text-center p-2"><h4 class="text-warning mb-0">+45</h4><small>Bonificaciones Max</small></div></div></div>
                                <div class="col-md-3"><div class="card border-primary"><div class="card-body text-center p-2"><h4 class="text-primary mb-0">200</h4><small>Score Mínimo</small></div></div></div>
                            </div>
                            <div class="mt-4">
                                <a href="/simulador" class="btn btn-primary btn-lg me-3"><i class="fas fa-calculator me-2"></i>Probar tu Propio Perfil</a>
                                <a href="/admin/login" class="btn btn-outline-danger"><i class="fas fa-cog me-2"></i>Panel Administrador</a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        function evaluarCaso(casoId) {
            const button = document.querySelector(`#resultado-${casoId}`).parentElement.querySelector('button');
            const originalText = button.innerHTML;
            button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Evaluando...';
            button.disabled = true;
            fetch(`/api/caso/${casoId}`).then(response => response.json()).then(caso => {
                return fetch('/api/evaluar', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(caso.datos) });
            }).then(response => response.json()).then(resultado => {
                button.innerHTML = originalText;
                button.disabled = false;
                if (resultado.success) { mostrarResultadoCaso(casoId, resultado.data); } else { alert('Error: ' + resultado.error); }
            }).catch(error => {
                button.innerHTML = originalText;
                button.disabled = false;
                console.error('Error:', error);
                alert('Error al evaluar el caso');
            });
        }
        function mostrarResultadoCaso(casoId, data) {
            const contenedor = document.getElementById(`resultado-${casoId}`);
            let html = ''; let badgeClass = 'success'; let iconClass = 'check-circle';
            if (!data.aprobado) { badgeClass = 'warning'; iconClass = 'exclamation-triangle'; } else if (data.score < 300) { badgeClass = 'info'; iconClass = 'info-circle'; }
            if (data.aprobado) {
                html = `
                    <div class="mb-3">
                        <div class="d-flex align-items-center mb-2"><i class="fas fa-${iconClass} text-${badgeClass} me-2"></i><span class="badge bg-${badgeClass}">✅ APROBADO</span><span class="badge bg-secondary ms-2">Modelo V2.0</span></div>
                        <div class="row"><div class="col-6"><div class="score-display text-${badgeClass}">${data.score}</div><small class="text-muted">Score Calibrado</small></div><div class="col-6"><div class="h5">$${data.monto_aprobado.toLocaleString()}</div><small class="text-muted">Monto Aprobado</small></div></div>
                        <div class="mt-2"><div class="row"><div class="col-6"><small><strong>Tasa:</strong> ${(data.tasa_anual * 100).toFixed(1)}%</small></div><div class="col-6"><small><strong>Riesgo:</strong> ${data.nivel_riesgo}</small></div></div><div class="row"><div class="col-6"><small><strong>TDSR:</strong> ${(data.tdsr * 100).toFixed(1)}%</small></div><div class="col-6"><small><strong>Plazos:</strong> ${data.opciones_plazo.filter(o => o.factible).length} disponibles</small></div></div></div>
                        ${data.desglose && data.desglose.generales && data.desglose.generales.bonificaciones && data.desglose.generales.bonificaciones.length > 0 ? `<div class="mt-2"><small class="text-success"><strong>Bonificaciones aplicadas:</strong><br>${data.desglose.generales.bonificaciones.map(b => `• ${b}`).join('<br>')}</small></div>` : ''}
                        <div class="mt-2"><small class="text-muted">Mejores plazos:</small><br>${data.opciones_plazo.filter(o => o.factible).slice(0, 3).map(opcion => `<span class="badge bg-outline-${opcion.recomendacion === 'Excelente' ? 'success' : opcion.recomendacion === 'Buena' ? 'info' : 'warning'} me-1">${opcion.plazo}m: $${opcion.pago_mensual.toLocaleString()}</span>`).join('')}</div>
                    </div>
                `;
            } else {
                html = `
                    <div class="mb-3">
                        <div class="d-flex align-items-center mb-2"><i class="fas fa-${iconClass} text-${badgeClass} me-2"></i><span class="badge bg-${badgeClass}">⚠️ PENDIENTE</span><span class="badge bg-secondary ms-2">Modelo V2.0</span></div>
                        <div class="score-display text-${badgeClass}">${data.score}</div><small class="text-muted">Score Calculado</small>
                        <div class="mt-2"><small class="text-${badgeClass}"><strong>Motivo:</strong><br>${data.razon}</small></div>
                        ${data.recomendaciones && data.recomendaciones.length > 0 ? `<div class="mt-2"><small class="text-info"><strong>Plan de mejora:</strong><br>${data.recomendaciones.slice(0, 2).map(rec => `• ${rec}`).join('<br>')}</small></div>` : ''}
                    </div>
                `;
            }
            contenedor.innerHTML = html;
            contenedor.style.display = 'block';
            contenedor.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
