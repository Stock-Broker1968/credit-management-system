#!/usr/bin/env python3
"""
Simulador Completo de Gestión de Crédito - Hotmart
Con Panel de Administración Seguro y Dashboard de Reportes
Versión Optimizada con Clave RAG123 y Sistema de Reportes Mejorado
"""

import os
import json
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for, flash

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'hotmart_credit_sim_secret_key_2025')

# Clave de acceso al módulo de administración
ADMIN_ACCESS_KEY = "RAG123"

# Lista para almacenar simulaciones de la sesión (máximo 10)
session_simulations = []

# Configuración de reglas de negocio por defecto
DEFAULT_RULES = {
    "score_minimo": 650,
    "edad_minima": 18,
    "edad_maxima": 70,
    "ingresos_minimos": 15000,
    "antiguedad_laboral_minima": 1,  # EN AÑOS
    "ratio_deuda_ingreso_maximo": 0.35,
    "monto_maximo_por_perfil": {
        "AAA": 200000, "AA": 150000, "A": 100000,
        "BBB": 75000, "BB": 50000, "B": 25000
    },
    "tasas_por_perfil": {
        "AAA": {"min": 8.5, "max": 12.0}, "AA": {"min": 12.0, "max": 15.0},
        "A": {"min": 15.0, "max": 18.0}, "BBB": {"min": 18.0, "max": 22.0},
        "BB": {"min": 22.0, "max": 28.0}, "B": {"min": 28.0, "max": 35.0}
    },
    "plazos_por_perfil": {
        "AAA": {"min": 12, "max": 60}, "AA": {"min": 12, "max": 48},
        "A": {"min": 12, "max": 36}, "BBB": {"min": 12, "max": 24},
        "BB": {"min": 6, "max": 18}, "B": {"min": 6, "max": 12}
    }
}

business_rules = DEFAULT_RULES.copy()

def load_business_rules():
    """Carga las reglas de negocio desde archivo o usa las por defecto"""
    global business_rules
    rules_file = 'business_rules.json'
    
    if os.path.exists(rules_file):
        try:
            with open(rules_file, 'r', encoding='utf-8') as f:
                loaded_rules = json.load(f)
                business_rules = DEFAULT_RULES.copy()
                for key, value in loaded_rules.items():
                    if key in business_rules:
                        if isinstance(business_rules[key], dict):
                            business_rules[key].update(value)
                        else:
                            business_rules[key] = value
            print("✓ Reglas de negocio cargadas desde archivo")
        except Exception as e:
            print(f"⚠ Error cargando reglas: {e}. Usando reglas por defecto.")
            business_rules = DEFAULT_RULES.copy()
    else:
        business_rules = DEFAULT_RULES.copy()
        save_business_rules()

def save_business_rules():
    """Guarda las reglas de negocio en archivo"""
    rules_file = 'business_rules.json'
    try:
        with open(rules_file, 'w', encoding='utf-8') as f:
            json.dump(business_rules, f, indent=2, ensure_ascii=False)
        print("✓ Reglas de negocio guardadas")
    except Exception as e:
        print(f"⚠ Error guardando reglas: {e}")

def add_simulation_to_session(simulation_data):
    """Añade una simulación a la lista de la sesión (máximo 10)"""
    global session_simulations
    
    # Preparar datos de la simulación
    sim_record = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "nombre": simulation_data.get('nombre', 'N/A'),
        "edad": simulation_data.get('edad', 0),
        "score_crediticio": simulation_data.get('score_crediticio', 0),
        "ingresos_mensuales": simulation_data.get('ingresos_mensuales', 0),
        "antiguedad_laboral": simulation_data.get('antiguedad_laboral', 0),
        "deudas_actuales": simulation_data.get('deudas_actuales', 0),
        "monto_solicitado": simulation_data.get('monto_solicitado', 0) or 0,
        "proposito": simulation_data.get('proposito', 'personal'),
        "resultado": simulation_data.get('resultado', {}),
        "aprobado": simulation_data.get('resultado', {}).get('aprobado', False),
        "perfil": simulation_data.get('resultado', {}).get('perfil_riesgo', {}).get('perfil', 'RECHAZADO'),
        "monto_aprobado": simulation_data.get('resultado', {}).get('oferta_credito', {}).get('monto_aprobado', 0) if simulation_data.get('resultado', {}).get('oferta_credito') else 0,
        "tasa_anual": simulation_data.get('resultado', {}).get('oferta_credito', {}).get('tasa_anual', 0) if simulation_data.get('resultado', {}).get('oferta_credito') else 0,
        "plazo_meses": simulation_data.get('resultado', {}).get('oferta_credito', {}).get('plazo_meses', 0) if simulation_data.get('resultado', {}).get('oferta_credito') else 0,
        "pago_mensual": simulation_data.get('resultado', {}).get('oferta_credito', {}).get('pago_mensual', 0) if simulation_data.get('resultado', {}).get('oferta_credito') else 0,
        "motivo_rechazo": simulation_data.get('resultado', {}).get('motivo_rechazo', '') if not simulation_data.get('resultado', {}).get('aprobado', False) else ''
    }
    
    # Añadir al principio de la lista
    session_simulations.insert(0, sim_record)
    
    # Mantener máximo 10 simulaciones
    if len(session_simulations) > 10:
        session_simulations = session_simulations[:10]

def validate_rules(rules):
    """Valida la consistencia de las reglas de negocio"""
    validation_results = []
    
    if rules['edad_minima'] < rules['edad_maxima']:
        validation_results.append("✓ Rango de edad válido")
    else:
        validation_results.append("❌ Rango de edad inválido")
    
    if 0 < rules['ratio_deuda_ingreso_maximo'] <= 1:
        validation_results.append("✓ Ratio deuda-ingreso válido")
    else:
        validation_results.append("❌ Ratio deuda-ingreso inválido")
    
    for perfil, tasas in rules['tasas_por_perfil'].items():
        if tasas['min'] < tasas['max']:
            validation_results.append(f"✓ Tasas {perfil} válidas")
        else:
            validation_results.append(f"❌ Tasas {perfil} inválidas")
    
    return validation_results

class CreditEvaluator:
    def __init__(self):
        self.rules = business_rules
    
    def calculate_risk_profile(self, data):
        """Calcula el perfil de riesgo basado en múltiples factores"""
        score = 0
        factors = []
        
        # Factor Score Crediticio (40% del peso)
        score_credit = int(data.get('score_crediticio', 0))
        if score_credit >= 800:
            score += 40
            factors.append("Score excelente (800+)")
        elif score_credit >= 750:
            score += 35
            factors.append("Score muy bueno (750-799)")
        elif score_credit >= 700:
            score += 30
            factors.append("Score bueno (700-749)")
        elif score_credit >= 650:
            score += 20
            factors.append("Score regular (650-699)")
        elif score_credit >= 600:
            score += 10
            factors.append("Score bajo (600-649)")
        else:
            score += 5
            factors.append("Score muy bajo (<600)")
        
        # Factor Ingresos (25% del peso)
        ingresos = float(data.get('ingresos_mensuales', 0))
        if ingresos >= 50000:
            score += 25
            factors.append("Ingresos altos ($50k+)")
        elif ingresos >= 30000:
            score += 20
            factors.append("Ingresos buenos ($30k-$50k)")
        elif ingresos >= 20000:
            score += 15
            factors.append("Ingresos medios ($20k-$30k)")
        elif ingresos >= 15000:
            score += 10
            factors.append("Ingresos básicos ($15k-$20k)")
        else:
            score += 2
            factors.append("Ingresos bajos (<$15k)")

        # Factor Antigüedad Laboral (15% del peso) - EN AÑOS
        antiguedad_anos = int(data.get('antiguedad_laboral', 0))
        if antiguedad_anos >= 5:
            score += 15
            factors.append("Antigüedad excelente (5+ años)")
        elif antiguedad_anos >= 3:
            score += 12
            factors.append("Antigüedad buena (3-5 años)")
        elif antiguedad_anos >= 2:
            score += 10
            factors.append("Antigüedad regular (2-3 años)")
        elif antiguedad_anos >= 1:
            score += 7
            factors.append("Antigüedad mínima (1-2 años)")
        else:
            score += 2
            factors.append("Antigüedad insuficiente (<1 año)")

        # Factor Edad (10% del peso)
        edad = int(data.get('edad', 0))
        if 35 <= edad <= 50:
            score += 10
            factors.append("Edad óptima (35-50)")
        elif 25 <= edad < 35 or 50 < edad <= 60:
            score += 8
            factors.append("Edad favorable")
        elif 18 <= edad < 25 or 60 < edad <= 65:
            score += 5
            factors.append("Edad aceptable")
        else:
            score += 1
            factors.append("Edad de riesgo")

        # Factor Ratio Deuda-Ingreso (10% del peso)
        deudas = float(data.get('deudas_actuales', 0))
        ratio_deuda = deudas / ingresos if ingresos > 0 else 1
        if ratio_deuda <= 0.10:
            score += 10
            factors.append("Endeudamiento muy bajo (<10%)")
        elif ratio_deuda <= 0.20:
            score += 8
            factors.append("Endeudamiento bajo (10-20%)")
        elif ratio_deuda <= 0.30:
            score += 6
            factors.append("Endeudamiento moderado (20-30%)")
        elif ratio_deuda <= 0.35:
            score += 3
            factors.append("Endeudamiento alto (30-35%)")
        else:
            score += 1
            factors.append("Endeudamiento excesivo (>35%)")
        
        # Determinar perfil basado en score total
        profile = "RECHAZADO"
        if score >= 85:
            profile = "AAA"
        elif score >= 75:
            profile = "AA"
        elif score >= 65:
            profile = "A"
        elif score >= 55:
            profile = "BBB"
        elif score >= 45:
            profile = "BB"
        elif score >= 35:
            profile = "B"
        
        return {
            "perfil": profile,
            "score_total": round(score, 2),
            "factores": factors,
            "ratio_deuda_ingreso": ratio_deuda
        }
    
    def validate_basic_requirements(self, data):
        """Valida los requisitos básicos según las reglas de negocio"""
        errors = []
        warnings = []
        
        score_crediticio = int(data.get('score_crediticio', 0))
        if score_crediticio < self.rules['score_minimo']:
            errors.append(f"Score crediticio insuficiente: {score_crediticio} < {self.rules['score_minimo']}")
        
        edad = int(data.get('edad', 0))
        if not self.rules['edad_minima'] <= edad <= self.rules['edad_maxima']:
            errors.append(f"Edad fuera del rango: {edad} (permitido: {self.rules['edad_minima']}-{self.rules['edad_maxima']})")
        
        ingresos = float(data.get('ingresos_mensuales', 0))
        if ingresos < self.rules['ingresos_minimos']:
            errors.append(f"Ingresos insuficientes: ${ingresos:,.0f} < ${self.rules['ingresos_minimos']:,.0f}")
        
        # Validación en años
        antiguedad_anos = int(data.get('antiguedad_laboral', 0))
        if antiguedad_anos < self.rules['antiguedad_laboral_minima']:
            errors.append(f"Antigüedad laboral insuficiente: {antiguedad_anos} años < {self.rules['antiguedad_laboral_minima']} años")
        
        deudas = float(data.get('deudas_actuales', 0))
        ratio_deuda = deudas / ingresos if ingresos > 0 else 1
        if ratio_deuda > self.rules['ratio_deuda_ingreso_maximo']:
            errors.append(f"Ratio deuda-ingreso excesivo: {ratio_deuda:.2%} > {self.rules['ratio_deuda_ingreso_maximo']:.2%}")
        
        return errors, warnings
    
    def calculate_credit_offer(self, profile_data, monto_solicitado=None):
        """Calcula la oferta de crédito basada en el perfil"""
        profile = profile_data['perfil']
        if profile == "RECHAZADO":
            return None
        
        monto_maximo = self.rules['monto_maximo_por_perfil'][profile]
        tasa_info = self.rules['tasas_por_perfil'][profile]
        plazo_info = self.rules['plazos_por_perfil'][profile]
        
        monto_ofrecido = monto_maximo
        if monto_solicitado and monto_solicitado <= monto_maximo:
            monto_ofrecido = monto_solicitado
        
        # Calcular tasa basada en el score interno
        score_ratio = profile_data['score_total'] / 100
        tasa_range = tasa_info['max'] - tasa_info['min']
        tasa_anual = tasa_info['max'] - (score_ratio * tasa_range)
        tasa_anual = max(tasa_info['min'], min(tasa_info['max'], tasa_anual))
        
        # Plazo recomendado basado en monto y perfil
        if monto_ofrecido <= 50000:
            plazo_meses = min(24, plazo_info['max'])
        elif monto_ofrecido <= 100000:
            plazo_meses = min(36, plazo_info['max'])
        else:
            plazo_meses = plazo_info['max']
        
        # Calcular pago mensual
        tasa_mensual = tasa_anual / 100 / 12
        if tasa_mensual > 0:
            pago_mensual = monto_ofrecido * (tasa_mensual * (1 + tasa_mensual) ** plazo_meses) / ((1 + tasa_mensual) ** plazo_meses - 1)
        else:
            pago_mensual = monto_ofrecido / plazo_meses
        
        return {
            "monto_aprobado": round(monto_ofrecido, 2),
            "tasa_anual": round(tasa_anual, 2),
            "plazo_meses": plazo_meses,
            "pago_mensual": round(pago_mensual, 2),
            "total_a_pagar": round(pago_mensual * plazo_meses, 2),
            "intereses_totales": round((pago_mensual * plazo_meses) - monto_ofrecido, 2)
        }
    
    def evaluate_credit_request(self, data):
        """Evaluación completa de solicitud de crédito"""
        try:
            errors, warnings = self.validate_basic_requirements(data)
            if errors:
                return {
                    "aprobado": False, 
                    "motivo_rechazo": "No cumple requisitos básicos", 
                    "errores": errors, 
                    "advertencias": warnings
                }
            
            profile_data = self.calculate_risk_profile(data)
            if profile_data['perfil'] == "RECHAZADO":
                return {
                    "aprobado": False, 
                    "motivo_rechazo": "Perfil de riesgo muy alto", 
                    "perfil_riesgo": profile_data, 
                    "advertencias": warnings
                }
            
            monto_solicitado = float(data.get('monto_solicitado', 0)) if data.get('monto_solicitado') else None
            oferta = self.calculate_credit_offer(profile_data, monto_solicitado)
            
            return {
                "aprobado": True,
                "perfil_riesgo": profile_data,
                "oferta_credito": oferta,
                "advertencias": warnings,
                "fecha_evaluacion": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "aprobado": False, 
                "motivo_rechazo": f"Error en evaluación: {str(e)}", 
                "error_tecnico": True
            }

# Inicializar
load_business_rules()
evaluator = CreditEvaluator()

def check_admin_access():
    """Verifica si el usuario tiene acceso al panel de administración"""
    return session.get('admin_authenticated', False)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            # Recargar reglas por si fueron actualizadas
            global business_rules, evaluator
            load_business_rules()
            evaluator = CreditEvaluator()
            
            form_data = {
                'nombre': request.form.get('nombre', ''),
                'edad': int(request.form.get('edad', 0)),
                'score_crediticio': int(request.form.get('score_crediticio', 0)),
                'ingresos_mensuales': float(request.form.get('ingresos_mensuales', 0)),
                'deudas_actuales': float(request.form.get('deudas_actuales', 0)),
                'antiguedad_laboral': int(request.form.get('antiguedad_laboral', 0)),  # EN AÑOS
                'monto_solicitado': float(request.form.get('monto_solicitado', 0)) if request.form.get('monto_solicitado') else None,
                'proposito': request.form.get('proposito', 'personal')
            }
            
            resultado = evaluator.evaluate_credit_request(form_data)
            
            # Agregar simulación a la sesión
            simulation_data = form_data.copy()
            simulation_data['resultado'] = resultado
            add_simulation_to_session(simulation_data)
            
            return render_template_string(MAIN_TEMPLATE, resultado=resultado)
        except (ValueError, TypeError) as e:
            return render_template_string(MAIN_TEMPLATE, resultado={
                "aprobado": False, 
                "motivo_rechazo": f"Datos incompletos o incorrectos: {str(e)}"
            })
    return render_template_string(MAIN_TEMPLATE, resultado=None)

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        access_key = request.form.get('access_key', '')
        if access_key == ADMIN_ACCESS_KEY:
            session['admin_authenticated'] = True
            flash('Acceso autorizado al panel de administración', 'success')
            return redirect(url_for('admin'))
        else:
            flash('Clave de acceso incorrecta', 'danger')
    
    return render_template_string(ADMIN_LOGIN_TEMPLATE)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not check_admin_access():
        flash('Acceso denegado. Ingrese la clave de acceso.', 'danger')
        return redirect(url_for('admin_login'))
    
    global business_rules, evaluator
    mensaje = None
    tipo_mensaje = 'info'
    
    if request.method == 'POST':
        try:
            action = request.form.get('action', 'save')
            if action == 'reset':
                business_rules = DEFAULT_RULES.copy()
                save_business_rules()
                evaluator = CreditEvaluator()
                mensaje = "✅ Reglas restauradas a valores por defecto"
                tipo_mensaje = 'success'
            elif action == 'save':
                # Actualizar reglas básicas
                business_rules['score_minimo'] = int(request.form.get('score_minimo', 650))
                business_rules['edad_minima'] = int(request.form.get('edad_minima', 18))
                business_rules['edad_maxima'] = int(request.form.get('edad_maxima', 70))
                business_rules['ingresos_minimos'] = int(request.form.get('ingresos_minimos', 15000))
                business_rules['antiguedad_laboral_minima'] = int(request.form.get('antiguedad_laboral_minima', 1))  # EN AÑOS
                business_rules['ratio_deuda_ingreso_maximo'] = float(request.form.get('ratio_deuda_ingreso_maximo', 35)) / 100
                
                # Actualizar reglas por perfil
                for perfil in ['AAA', 'AA', 'A', 'BBB', 'BB', 'B']:
                    business_rules['monto_maximo_por_perfil'][perfil] = int(request.form.get(f'monto_{perfil}', 50000))
                    business_rules['tasas_por_perfil'][perfil]['min'] = float(request.form.get(f'tasa_min_{perfil}', 10))
                    business_rules['tasas_por_perfil'][perfil]['max'] = float(request.form.get(f'tasa_max_{perfil}', 20))
                    business_rules['plazos_por_perfil'][perfil]['max'] = int(request.form.get(f'plazo_max_{perfil}', 24))
                    # Mantener plazo mínimo por defecto
                    if 'min' not in business_rules['plazos_por_perfil'][perfil]:
                        business_rules['plazos_por_perfil'][perfil]['min'] = 6 if perfil in ['BB', 'B'] else 12
                
                save_business_rules()
                evaluator = CreditEvaluator()
                mensaje = "✅ Configuración guardada exitosamente"
                tipo_mensaje = 'success'
        except Exception as e:
            mensaje = f"❌ Error al guardar configuración: {str(e)}"
            tipo_mensaje = 'danger'
    
    return render_template_string(ADMIN_TEMPLATE, 
                                rules=business_rules, 
                                mensaje=mensaje, 
                                tipo_mensaje=tipo_mensaje,
                                validate_rules=validate_rules,
                                datetime=datetime)

@app.route('/admin_logout')
def admin_logout():
    session.pop('admin_authenticated', None)
    flash('Sesión de administración cerrada', 'info')
    return redirect(url_for('index'))

@app.route('/reports')
def reports():
    # Generar estadísticas de la sesión
    total_simulations = len(session_simulations)
    approved_count = len([s for s in session_simulations if s['aprobado']])
    rejected_count = total_simulations - approved_count
    
    # Estadísticas por perfil
    profile_stats = {}
    approved_amount = 0
    
    for sim in session_simulations:
        if sim['aprobado']:
            approved_amount += sim['monto_aprobado']
            perfil = sim['perfil']
            if perfil in profile_stats:
                profile_stats[perfil]['count'] += 1
                profile_stats[perfil]['total_amount'] += sim['monto_aprobado']
            else:
                profile_stats[perfil] = {
                    'count': 1, 
                    'total_amount': sim['monto_aprobado'],
                    'avg_rate': sim['tasa_anual']
                }
    
    # Calcular promedios para perfiles
    for perfil in profile_stats:
        profile_stats[perfil]['avg_amount'] = profile_stats[perfil]['total_amount'] / profile_stats[perfil]['count']
    
    stats = {
        'total_simulations': total_simulations,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'approval_rate': (approved_count / total_simulations * 100) if total_simulations > 0 else 0,
        'total_approved_amount': approved_amount,
        'avg_approved_amount': approved_amount / approved_count if approved_count > 0 else 0,
        'profile_stats': profile_stats
    }
    
    return render_template_string(REPORTS_TEMPLATE, 
                                simulations=session_simulations,
                                stats=stats,
                                datetime=datetime)

@app.route('/clear_session')
def clear_session():
    """Limpiar simulaciones de la sesión"""
    global session_simulations
    session_simulations = []
    flash('Simulaciones de sesión limpiadas', 'info')
    return redirect(url_for('reports'))

@app.route('/api/test/<profile>')
def test_profile(profile):
    test_data = {
        'AAA': {
            'nombre': 'Cliente AAA Test', 'edad': 35, 'score_crediticio': 820, 
            'ingresos_mensuales': 60000, 'deudas_actuales': 5000, 
            'antiguedad_laboral': 5, 'monto_solicitado': 150000  # EN AÑOS
        },
        'AA': {
            'nombre': 'Cliente AA Test', 'edad': 40, 'score_crediticio': 780, 
            'ingresos_mensuales': 45000, 'deudas_actuales': 8000, 
            'antiguedad_laboral': 4, 'monto_solicitado': 120000  # EN AÑOS
        },
        'A': {
            'nombre': 'Cliente A Test', 'edad': 30, 'score_crediticio': 720, 
            'ingresos_mensuales': 30000, 'deudas_actuales': 6000, 
            'antiguedad_laboral': 3, 'monto_solicitado': 80000  # EN AÑOS
        },
        'REJECT': {
            'nombre': 'Cliente Rechazado Test', 'edad': 22, 'score_crediticio': 580, 
            'ingresos_mensuales': 12000, 'deudas_actuales': 8000, 
            'antiguedad_laboral': 0, 'monto_solicitado': 50000  # EN AÑOS (menos de 1)
        }
    }
    
    if profile.upper() not in test_data:
        return jsonify({'error': 'Perfil no encontrado'}), 404
    
    data = test_data[profile.upper()]
    resultado = evaluator.evaluate_credit_request(data)
    
    # Agregar a simulaciones de sesión
    simulation_data = data.copy()
    simulation_data['resultado'] = resultado
    add_simulation_to_session(simulation_data)
    
    return jsonify({
        'perfil_test': profile.upper(),
        'datos_entrada': data,
        'resultado_evaluacion': resultado
    })

@app.route('/api/rules')
def get_rules():
    return jsonify(business_rules)

@app.route('/api/evaluate', methods=['POST'])
def api_evaluate():
    """API para evaluar crédito via JSON"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        resultado = evaluator.evaluate_credit_request(data)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== TEMPLATES HTML =====
ADMIN_LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Acceso Admin - Hotmart Credit</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; }
        .login-card { background: white; border-radius: 15px; padding: 40px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); max-width: 400px; width: 100%; }
        .login-header { text-align: center; margin-bottom: 30px; }
        .login-header h1 { color: #667eea; margin-bottom: 10px; }
        .login-header .subtitle { color: #666; font-size: 14px; }
        .form-group { margin-bottom: 20px; }
        .form-group label { display: block; margin-bottom: 8px; font-weight: 600; color: #333; }
        .form-group input { width: 100%; padding: 15px; border: 2px solid #e1e1e1; border-radius: 8px; font-size: 16px; text-align: center; letter-spacing: 2px; }
        .form-group input:focus { outline: none; border-color: #667eea; }
        .login-btn { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; padding: 15px; border-radius: 8px; font-size: 18px; font-weight: 600; cursor: pointer; width: 100%; margin-bottom: 20px; transition: all 0.3s ease; }
        .login-btn:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4); }
        .back-link { text-align: center; }
        .back-link a { color: #667eea; text-decoration: none; font-weight: 600; }
        .alert { padding: 15px; border-radius: 5px; margin-bottom: 20px; }
        .alert-success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .alert-danger { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .key-hint { background: #e3f2fd; padding: 15px; border-radius: 8px; margin-bottom: 20px; text-align: center; color: #1565c0; font-size: 14px; }
    </style>
</head>
<body>
    <div class="login-card">
        <div class="login-header">
            <h1>🔐 Acceso Administrativo</h1>
            <p class="subtitle">Panel de Configuración de Reglas de Negocio</p>
        </div>
        <div class="key-hint">
            <strong>🔑 Clave de Acceso Requerida</strong><br>
            Ingrese la clave para acceder al módulo administrativo
        </div>
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        <form method="POST">
            <div class="form-group">
                <label for="access_key">Clave de Acceso</label>
                <input type="password" id="access_key" name="access_key" placeholder="Ingrese clave" required>
            </div>
            <button type="submit" class="login-btn">🚀 Acceder al Panel</button>
        </form>
        <div class="back-link">
            <a href="/">← Volver al Simulador</a>
        </div>
    </div>
</body>
</html>
'''

MAIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Simulador de Crédito Hotmart</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; color: white; margin-bottom: 30px; }
        .header h1 { font-size: 2.5rem; margin-bottom: 10px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
        .header p { font-size: 1.2rem; opacity: 0.9; }
        .nav-buttons { display: flex; gap: 15px; justify-content: center; margin-bottom: 30px; }
        .nav-btn { padding: 12px 24px; background: rgba(255,255,255,0.2); color: white; text-decoration: none; border-radius: 25px; border: 2px solid rgba(255,255,255,0.3); transition: all 0.3s ease; font-weight: 600; }
        .nav-btn:hover { background: rgba(255,255,255,0.3); transform: translateY(-2px); }
        .nav-btn.active { background: rgba(255,255,255,0.9); color: #667eea; }
        .form-card { background: white; border-radius: 15px; padding: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); margin-bottom: 20px; }
        .form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .form-group { margin-bottom: 20px; }
        .form-group label { display: block; margin-bottom: 8px; font-weight: 600; color: #333; }
        .form-group input, .form-group select { width: 100%; padding: 12px; border: 2px solid #e1e1e1; border-radius: 8px; font-size: 16px; transition: border-color 0.3s ease; }
        .form-group input:focus, .form-group select:focus { outline: none; border-color: #667eea; }
        .submit-btn { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; padding: 15px 40px; border-radius: 8px; font-size: 18px; font-weight: 600; cursor: pointer; transition: all 0.3s ease; width: 100%; }
        .submit-btn:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4); }
        .result-card { background: white; border-radius: 15px; padding: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); margin-top: 20px; }
        .result-approved { border-left: 5px solid #28a745; }
        .result-rejected { border-left: 5px solid #dc3545; }
        .profile-badge { display: inline-block; padding: 5px 12px; border-radius: 20px; font-weight: bold; text-transform: uppercase; font-size: 12px; }
        .profile-AAA { background: #28a745; color: white; }
        .profile-AA { background: #17a2b8; color: white; }
        .profile-A { background: #007bff; color: white; }
        .profile-BBB { background: #ffc107; color: black; }
        .profile-BB { background: #fd7e14; color: white; }
        .profile-B { background: #dc3545; color: white; }
        .offer-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }
        .offer-item { text-align: center; padding: 20px; background: #f8f9fa; border-radius: 10px; }
        .offer-item h4 { color: #667eea; margin-bottom: 10px; }
        .offer-item .value { font-size: 1.5rem; font-weight: bold; color: #333; }
        .factors-list { margin: 15px 0; }
        .factors-list li { margin: 5px 0; padding: 8px; background: #e9ecef; border-radius: 5px; }
        @media (max-width: 768px) {
            .header h1 { font-size: 2rem; }
            .nav-buttons { flex-direction: column; align-items: center; }
            .form-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏦 Simulador de Crédito Hotmart</h1>
            <p>Sistema Integral de Evaluación Crediticia</p>
        </div>
        <div class="nav-buttons">
            <a href="/" class="nav-btn active">🏠 Evaluación</a>
            <a href="/admin_login" class="nav-btn">⚙️ Administración</a>
            <a href="/reports" class="nav-btn">📊 Reportes</a>
        </div>
        <div class="form-card">
            <form method="POST">
                <h2 style="margin-bottom: 25px; color: #333;">📋 Información del Solicitante</h2>
                <div class="form-grid">
                    <div class="form-group"><label for="nombre">Nombre Completo *</label><input type="text" id="nombre" name="nombre" required></div>
                    <div class="form-group"><label for="edad">Edad *</label><input type="number" id="edad" name="edad" min="18" max="80" required></div>
                    <div class="form-group"><label for="score_crediticio">Score Crediticio (300-850) *</label><input type="number" id="score_crediticio" name="score_crediticio" min="300" max="850" required></div>
                    <div class="form-group"><label for="ingresos_mensuales">Ingresos Mensuales ($) *</label><input type="number" id="ingresos_mensuales" name="ingresos_mensuales" min="0" step="0.01" required></div>
                    <div class="form-group"><label for="deudas_actuales">Deudas Actuales ($)</label><input type="number" id="deudas_actuales" name="deudas_actuales" min="0" step="0.01" value="0"></div>
                    <div class="form-group"><label for="antiguedad_laboral">Antigüedad Laboral (años) *</label><input type="number" id="antiguedad_laboral" name="antiguedad_laboral" min="0" max="50" required></div>
                    <div class="form-group"><label for="monto_solicitado">Monto Solicitado ($)</label><input type="number" id="monto_solicitado" name="monto_solicitado" min="1000" step="1000" placeholder="Opcional - se calculará automáticamente"></div>
                    <div class="form-group"><label for="proposito">Propósito del Crédito</label><select id="proposito" name="proposito"><option value="personal">Uso Personal</option><option value="auto">Compra de Vehículo</option><option value="vivienda">Mejoras al Hogar</option><option value="educacion">Educación</option><option value="negocio">Inversión en Negocio</option><option value="consolidacion">Consolidación de Deudas</option></select></div>
                </div>
                <button type="submit" class="submit-btn">🔍 Evaluar Solicitud de Crédito</button>
            </form>
        </div>
        {% if resultado %}
        <div class="result-card {% if resultado.aprobado %}result-approved{% else %}result-rejected{% endif %}">
            <h2 style="margin-bottom: 20px; color: {% if resultado.aprobado %}#28a745{% else %}#dc3545{% endif %};">
                {% if resultado.aprobado %}✅ CRÉDITO APROBADO{% else %}❌ CRÉDITO RECHAZADO{% endif %}
            </h2>
            {% if not resultado.aprobado %}
            <div style="background: #f8d7da; padding: 15px; border-radius: 8px; margin: 15px 0;">
                <h4>Motivo del Rechazo:</h4>
                <p><strong>{{ resultado.motivo_rechazo }}</strong></p>
                {% if resultado.errores %}
                <ul style="margin: 10px 0; margin-left: 20px;">
                {% for error in resultado.errores %}
                    <li>{{ error }}</li>
                {% endfor %}
                </ul>
                {% endif %}
            </div>
            {% endif %}
            {% if resultado.perfil_riesgo %}
                <div style="background: #e9ecef; padding: 20px; border-radius: 10px; margin: 20px 0;">
                    <h3>📈 Análisis de Perfil</h3>
                    <p><span>Perfil de Riesgo: </span><span class="profile-badge profile-{{ resultado.perfil_riesgo.perfil }}">{{ resultado.perfil_riesgo.perfil }}</span></p>
                    <p><strong>Score Interno:</strong> {{ resultado.perfil_riesgo.score_total }}/100</p>
                    <p><strong>Ratio Deuda-Ingreso:</strong> {{ "%.2f"|format(resultado.perfil_riesgo.ratio_deuda_ingreso * 100) }}%</p>
                    <h4 style="margin: 15px 0 10px 0;">Factores Evaluados:</h4>
                    <ul class="factors-list">
                    {% for factor in resultado.perfil_riesgo.factores %}
                        <li>{{ factor }}</li>
                    {% endfor %}
                    </ul>
                </div>
            {% endif %}
            {% if resultado.oferta_credito %}
                <div style="background: #d4edda; padding: 20px; border-radius: 10px; margin: 20px 0;">
                    <h3>💰 Oferta de Crédito</h3>
                    <div class="offer-grid">
                        <div class="offer-item"><h4>Monto Aprobado</h4><div class="value">${{ "{:,.0f}".format(resultado.oferta_credito.monto_aprobado) }}</div></div>
                        <div class="offer-item"><h4>Tasa Anual</h4><div class="value">{{ resultado.oferta_credito.tasa_anual }}%</div></div>
                        <div class="offer-item"><h4>Plazo</h4><div class="value">{{ resultado.oferta_credito.plazo_meses }} meses</div></div>
                        <div class="offer-item"><h4>Pago Mensual</h4><div class="value">${{ "{:,.0f}".format(resultado.oferta_credito.pago_mensual) }}</div></div>
                        <div class="offer-item"><h4>Total a Pagar</h4><div class="value">${{ "{:,.0f}".format(resultado.oferta_credito.total_a_pagar) }}</div></div>
                        <div class="offer-item"><h4>Intereses Totales</h4><div class="value">${{ "{:,.0f}".format(resultado.oferta_credito.intereses_totales) }}</div></div>
                    </div>
                </div>
            {% endif %}
            {% if resultado.advertencias %}
                <div style="background: #fff3cd; padding: 15px; border-radius: 8px; margin: 15px 0;">
                    <h4>⚠️ Advertencias:</h4>
                    <ul style="margin: 10px 0; margin-left: 20px;">
                    {% for warning in resultado.advertencias %}
                        <li>{{ warning }}</li>
                    {% endfor %}
                    </ul>
                </div>
            {% endif %}
        </div>
        {% endif %}
    </div>
</body>
</html>
'''

ADMIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Panel de Administración - Hotmart Credit</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; color: white; margin-bottom: 30px; }
        .header h1 { font-size: 2.5rem; margin-bottom: 10px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
        .nav-buttons { display: flex; gap: 15px; justify-content: center; margin-bottom: 30px; }
        .nav-btn { padding: 12px 24px; background: rgba(255,255,255,0.2); color: white; text-decoration: none; border-radius: 25px; border: 2px solid rgba(255,255,255,0.3); transition: all 0.3s ease; font-weight: 600; }
        .nav-btn:hover { background: rgba(255,255,255,0.3); transform: translateY(-2px); }
        .nav-btn.active { background: rgba(255,255,255,0.9); color: #667eea; }
        .admin-card { background: white; border-radius: 15px; padding: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); margin-bottom: 30px; }
        .admin-section { margin-bottom: 40px; }
        .admin-section h3 { color: #333; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #667eea; }
        .rules-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .rule-group { background: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 4px solid #667eea; }
        .rule-group h4 { color: #333; margin-bottom: 15px; }
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; margin-bottom: 5px; font-weight: 600; color: #555; }
        .form-group input { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
        .profile-rules { background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 10px 0; }
        .profile-title { font-weight: bold; margin-bottom: 10px; color: #333; }
        .profile-inputs { display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 10px; }
        .btn-primary { background: #667eea; color: white; border: none; padding: 12px 30px; border-radius: 5px; cursor: pointer; font-weight: 600; transition: all 0.3s ease; }
        .btn-primary:hover { background: #5a67d8; }
        .btn-secondary { background: #6c757d; color: white; border: none; padding: 12px 30px; border-radius: 5px; cursor: pointer; font-weight: 600; margin-left: 10px; transition: all 0.3s ease; }
        .btn-secondary:hover { background: #5a6268; }
        .btn-logout { background: #dc3545; color: white; border: none; padding: 8px 20px; border-radius: 5px; cursor: pointer; font-weight: 600; margin-left: 10px; transition: all 0.3s ease; font-size: 14px; }
        .btn-logout:hover { background: #c82333; }
        .alert { padding: 15px; border-radius: 5px; margin: 15px 0; }
        .alert-success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .alert-danger { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .admin-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        @media (max-width: 768px) {
            .rules-grid { grid-template-columns: 1fr; }
            .profile-inputs { grid-template-columns: 1fr 1fr; }
            .admin-header { flex-direction: column; gap: 15px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚙️ Panel de Administración</h1>
            <p>Configuración de Reglas de Negocio - Acceso Autorizado</p>
        </div>
        <div class="nav-buttons">
            <a href="/" class="nav-btn">🏠 Evaluación</a>
            <a href="/admin" class="nav-btn active">⚙️ Administración</a>
            <a href="/reports" class="nav-btn">📊 Reportes</a>
            <a href="/admin_logout" class="nav-btn" style="background: rgba(220,53,69,0.8);">🚪 Cerrar Sesión</a>
        </div>
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        {% if mensaje %}<div class="alert alert-{{ tipo_mensaje }}">{{ mensaje }}</div>{% endif %}
        <div class="admin-card">
            <div class="admin-header">
                <h3>🔧 Configuración del Sistema</h3>
                <div>
                    <span style="color: #28a745; font-weight: bold;">✅ Sesión Administrativa Activa</span>
                </div>
            </div>
            <form method="POST">
                <div class="admin-section">
                    <h3>📋 Requisitos Básicos</h3>
                    <div class="rules-grid">
                        <div class="rule-group">
                            <h4>Score Crediticio</h4>
                            <div class="form-group"><label>Score Mínimo Requerido</label><input type="number" name="score_minimo" value="{{ rules.score_minimo }}" min="300" max="850"></div>
                        </div>
                        <div class="rule-group">
                            <h4>Edad</h4>
                            <div class="form-group"><label>Edad Mínima</label><input type="number" name="edad_minima" value="{{ rules.edad_minima }}" min="18" max="25"></div>
                            <div class="form-group"><label>Edad Máxima</label><input type="number" name="edad_maxima" value="{{ rules.edad_maxima }}" min="60" max="80"></div>
                        </div>
                        <div class="rule-group">
                            <h4>Ingresos y Empleo</h4>
                            <div class="form-group"><label>Ingresos Mínimos ($)</label><input type="number" name="ingresos_minimos" value="{{ rules.ingresos_minimos }}" min="5000" step="1000"></div>
                            <div class="form-group"><label>Antigüedad Laboral Mínima (años)</label><input type="number" name="antiguedad_laboral_minima" value="{{ rules.antiguedad_laboral_minima }}" min="1" max="10"></div>
                        </div>
                        <div class="rule-group">
                            <h4>Endeudamiento</h4>
                            <div class="form-group"><label>Ratio Deuda-Ingreso Máximo (%)</label><input type="number" name="ratio_deuda_ingreso_maximo" value="{{ (rules.ratio_deuda_ingreso_maximo * 100)|round|int }}" min="10" max="50" step="5"></div>
                        </div>
                    </div>
                </div>
                <div class="admin-section">
                    <h3>💰 Configuración por Perfil de Riesgo</h3>
                    {% for perfil in ['AAA', 'AA', 'A', 'BBB', 'BB', 'B'] %}
                    <div class="profile-rules">
                        <div class="profile-title">Perfil {{ perfil }}</div>
                        <div class="profile-inputs">
                            <div><label>Monto Máximo ($)</label><input type="number" name="monto_{{ perfil }}" value="{{ rules.monto_maximo_por_perfil[perfil] }}" min="10000" step="5000"></div>
                            <div><label>Tasa Mín (%)</label><input type="number" name="tasa_min_{{ perfil }}" value="{{ rules.tasas_por_perfil[perfil].min }}" min="5" max="40" step="0.5"></div>
                            <div><label>Tasa Máx (%)</label><input type="number" name="tasa_max_{{ perfil }}" value="{{ rules.tasas_por_perfil[perfil].max }}" min="5" max="40" step="0.5"></div>
                            <div><label>Plazo Máx (meses)</label><input type="number" name="plazo_max_{{ perfil }}" value="{{ rules.plazos_por_perfil[perfil].max }}" min="6" max="72" step="6"></div>
                        </div>
                    </div>
                    {% endfor %}
                </div>
                <div style="text-align: center; margin-top: 30px;">
                    <button type="submit" name="action" value="save" class="btn-primary">💾 Guardar Configuración</button>
                    <button type="submit" name="action" value="reset" class="btn-secondary">🔄 Restaurar Valores por Defecto</button>
                </div>
            </form>
        </div>
        <div class="admin-card">
            <h3>📊 Estado Actual del Sistema</h3>
            <div class="rules-grid">
                <div class="rule-group">
                    <h4>Configuración Activa</h4>
                    <p><strong>Fecha de última actualización:</strong> {{ datetime.now().strftime('%Y-%m-%d %H:%M:%S') }}</p>
                    <p><strong>Perfiles configurados:</strong> {{ rules.monto_maximo_por_perfil.keys()|list|length }}</p>
                    <p><strong>Score mínimo:</strong> {{ rules.score_minimo }}</p>
                    <p><strong>Antigüedad mínima:</strong> {{ rules.antiguedad_laboral_minima }} años</p>
                    <p><strong>Monto máximo general:</strong> ${{ "{:,}".format(rules.monto_maximo_por_perfil.AAA) }}</p>
                </div>
                <div class="rule-group">
                    <h4>Validación de Reglas</h4>
                    {% set validation = validate_rules(rules) %}
                    {% for item in validation %}
                        <p style="color: {{ 'green' if item.startswith('✓') else 'red' }};">{{ item }}</p>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>
</body>
</html>
'''

REPORTS_TEMPLATE = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard de Reportes - Hotmart Credit</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; color: white; margin-bottom: 30px; }
        .header h1 { font-size: 2.5rem; margin-bottom: 10px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
        .nav-buttons { display: flex; gap: 15px; justify-content: center; margin-bottom: 30px; }
        .nav-btn { padding: 12px 24px; background: rgba(255,255,255,0.2); color: white; text-decoration: none; border-radius: 25px; border: 2px solid rgba(255,255,255,0.3); transition: all 0.3s ease; font-weight: 600; }
        .nav-btn:hover { background: rgba(255,255,255,0.3); transform: translateY(-2px); }
        .nav-btn.active { background: rgba(255,255,255,0.9); color: #667eea; }
        .dashboard-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .stat-card { background: white; border-radius: 15px; padding: 25px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); text-align: center; }
        .stat-number { font-size: 2.5rem; font-weight: bold; margin-bottom: 10px; }
        .stat-label { color: #666; font-weight: 600; }
        .approval-rate { color: #28a745; }
        .rejection-rate { color: #dc3545; }
        .total-amount { color: #667eea; }
        .avg-amount { color: #fd7e14; }
        .report-card { background: white; border-radius: 15px; padding: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); margin-bottom: 30px; }
        .section-title { color: #333; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #667eea; display: flex; justify-content: space-between; align-items: center; }
        .simulations-table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        .simulations-table th, .simulations-table td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        .simulations-table th { background: #f8f9fa; font-weight: 600; }
        .status-approved { color: #28a745; font-weight: bold; }
        .status-rejected { color: #dc3545; font-weight: bold; }
        .profile-badge { display: inline-block; padding: 3px 8px; border-radius: 12px; font-weight: bold; font-size: 11px; text-transform: uppercase; }
        .profile-AAA { background: #28a745; color: white; }
        .profile-AA { background: #17a2b8; color: white; }
        .profile-A { background: #007bff; color: white; }
        .profile-BBB { background: #ffc107; color: black; }
        .profile-BB { background: #fd7e14; color: white; }
        .profile-B { background: #dc3545; color: white; }
        .profile-RECHAZADO { background: #6c757d; color: white; }
        .profile-stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }
        .profile-stat { background: #f8f9fa; padding: 15px; border-radius: 10px; text-align: center; }
        .no-data { text-align: center; color: #666; padding: 40px; font-style: italic; }
        .btn-action { padding: 10px 20px; background: #667eea; color: white; text-decoration: none; border-radius: 5px; margin: 0 5px; font-weight: 600; transition: all 0.3s ease; }
        .btn-action:hover { background: #5a67d8; }
        .btn-clear { background: #dc3545; }
        .btn-clear:hover { background: #c82333; }
        .btn-print { background: #28a745; }
        .btn-print:hover { background: #218838; }
        .executive-summary { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 25px; border-radius: 15px; margin-bottom: 30px; }
        .executive-summary h3 { margin-bottom: 15px; }
        .summary-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; }
        .summary-item { text-align: center; }
        .summary-value { font-size: 1.8rem; font-weight: bold; margin-bottom: 5px; }
        .summary-label { opacity: 0.9; font-size: 0.9rem; }
        @media (max-width: 768px) {
            .dashboard-grid { grid-template-columns: 1fr; }
            .simulations-table { font-size: 14px; }
            .simulations-table th, .simulations-table td { padding: 8px; }
            .nav-buttons { flex-wrap: wrap; }
        }
        @media print {
            body { background: white; }
            .nav-buttons, .btn-action { display: none; }
            .container { max-width: 100%; }
            .header { color: black; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Dashboard de Reportes</h1>
            <p>Análisis y Estadísticas del Sistema de Evaluación Crediticia</p>
        </div>
        <div class="nav-buttons">
            <a href="/" class="nav-btn">🏠 Evaluación</a>
            <a href="/admin_login" class="nav-btn">⚙️ Administración</a>
            <a href="/reports" class="nav-btn active">📊 Reportes</a>
        </div>

        {% if stats.total_simulations > 0 %}
        <!-- Resumen Ejecutivo -->
        <div class="executive-summary">
            <h3>📈 Resumen Ejecutivo de Simulaciones</h3>
            <div class="summary-grid">
                <div class="summary-item">
                    <div class="summary-value">{{ stats.total_simulations }}</div>
                    <div class="summary-label">Total Simulaciones</div>
                </div>
                <div class="summary-item">
                    <div class="summary-value">{{ "%.1f"|format(stats.approval_rate) }}%</div>
                    <div class="summary-label">Tasa de Aprobación</div>
                </div>
                <div class="summary-item">
                    <div class="summary-value">${{ "{:,.0f}".format(stats.total_approved_amount) }}</div>
                    <div class="summary-label">Monto Total Aprobado</div>
                </div>
                <div class="summary-item">
                    <div class="summary-value">${{ "{:,.0f}".format(stats.avg_approved_amount) }}</div>
                    <div class="summary-label">Promedio por Crédito</div>
                </div>
            </div>
        </div>

        <!-- KPIs Principales -->
        <div class="dashboard-grid">
            <div class="stat-card">
                <div class="stat-number approval-rate">{{ stats.approved_count }}</div>
                <div class="stat-label">Créditos Aprobados</div>
            </div>
            <div class="stat-card">
                <div class="stat-number rejection-rate">{{ stats.rejected_count }}</div>
                <div class="stat-label">Créditos Rechazados</div>
            </div>
            <div class="stat-card">
                <div class="stat-number total-amount">${{ "{:,.0f}".format(stats.total_approved_amount) }}</div>
                <div class="stat-label">Monto Total Aprobado</div>
            </div>
            <div class="stat-card">
                <div class="stat-number avg-amount">${{ "{:,.0f}".format(stats.avg_approved_amount) }}</div>
                <div class="stat-label">Promedio por Aprobación</div>
            </div>
        </div>

        <!-- Estadísticas por Perfil -->
        {% if stats.profile_stats %}
        <div class="report-card">
            <h3 class="section-title">📊 Distribución por Perfil de Riesgo</h3>
            <div class="profile-stats">
                {% for perfil, data in stats.profile_stats.items() %}
                <div class="profile-stat">
                    <h4><span class="profile-badge profile-{{ perfil }}">{{ perfil }}</span></h4>
                    <p><strong>{{ data.count }}</strong> aprobaciones</p>
                    <p><strong>${{ "{:,.0f}".format(data.total_amount) }}</strong> total</p>
                    <p><strong>${{ "{:,.0f}".format(data.avg_amount) }}</strong> promedio</p>
                    <p><strong>{{ "%.1f"|format(data.avg_rate) }}%</strong> tasa promedio</p>
                </div>
                {% endfor %}
            </div>
        </div>
        {% endif %}

        <!-- Detalle de Simulaciones -->
        <div class="report-card">
            <h3 class="section-title">
                📋 Registro de Simulaciones (Últimas {{ simulations|length }})
                <div>
                    <a href="javascript:window.print()" class="btn-action btn-print">🖨️ Imprimir</a>
                    <a href="/clear_session" class="btn-action btn-clear" onclick="return confirm('¿Está seguro de limpiar todas las simulaciones?')">🗑️ Limpiar</a>
                </div>
            </h3>
            <div style="overflow-x: auto;">
                <table class="simulations-table">
                    <thead>
                        <tr>
                            <th>Fecha/Hora</th>
                            <th>Cliente</th>
                            <th>Edad</th>
                            <th>Score</th>
                            <th>Ingresos</th>
                            <th>Antigüedad</th>
                            <th>Resultado</th>
                            <th>Perfil</th>
                            <th>Monto Aprobado</th>
                            <th>Tasa</th>
                            <th>Motivo Rechazo</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for sim in simulations %}
                        <tr>
                            <td>{{ sim.timestamp }}</td>
                            <td>{{ sim.nombre }}</td>
                            <td>{{ sim.edad }}</td>
                            <td>{{ sim.score_crediticio }}</td>
                            <td>${{ "{:,.0f}".format(sim.ingresos_mensuales) }}</td>
                            <td>{{ sim.antiguedad_laboral }} años</td>
                            <td class="{% if sim.aprobado %}status-approved{% else %}status-rejected{% endif %}">
                                {% if sim.aprobado %}✅ APROBADO{% else %}❌ RECHAZADO{% endif %}
                            </td>
                            <td><span class="profile-badge profile-{{ sim.perfil }}">{{ sim.perfil }}</span></td>
                            <td>{% if sim.monto_aprobado > 0 %} ${{ "{:,.0f}".format(sim.monto_aprobado) }}{% else %}-{% endif %}</td>
                            <td>{% if sim.tasa_anual > 0 %}{{ "%.1f"|format(sim.tasa_anual) }}%{% else %}-{% endif %}</td>
                            <td style="max-width: 200px; overflow: hidden; text-overflow: ellipsis;">{{ sim.motivo_rechazo[:50] }}{% if sim.motivo_rechazo|length > 50 %}...{% endif %}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Análisis de Riesgos -->
        <div class="report-card">
            <h3 class="section-title">⚠️ Análisis de Factores de Rechazo</h3>
            {% set rejected_sims = simulations | selectattr('aprobado', 'equalto', false) | list %}
            {% if rejected_sims %}
            <div class="profile-stats">
                <div class="profile-stat">
                    <h4>Total Rechazos</h4>
                    <p><strong>{{ rejected_sims|length }}</strong> de {{ simulations|length }}</p>
                    <p><strong>{{ "%.1f"|format((rejected_sims|length / simulations|length * 100) if simulations|length > 0 else 0) }}%</strong> de tasa de rechazo</p>
                </div>
                {% set score_rejects = rejected_sims | selectattr('score_crediticio', 'lt', 650) | list %}
                <div class="profile-stat">
                    <h4>Score Bajo</h4>
                    <p><strong>{{ score_rejects|length }}</strong> rechazos</p>
                    <p>Score < 650</p>
                </div>
                {% set income_rejects = rejected_sims | selectattr('ingresos_mensuales', 'lt', 15000) | list %}
                <div class="profile-stat">
                    <h4>Ingresos Bajos</h4>
                    <p><strong>{{ income_rejects|length }}</strong> rechazos</p>
                    <p>Ingresos < $15,000</p>
                </div>
                {% set exp_rejects = rejected_sims | selectattr('antiguedad_laboral', 'lt', 1) | list %}
                <div class="profile-stat">
                    <h4>Poca Experiencia</h4>
                    <p><strong>{{ exp_rejects|length }}</strong> rechazos</p>
                    <p>Antigüedad < 1 año</p>
                </div>
            </div>
            {% else %}
            <p class="no-data">No hay rechazos registrados en la sesión actual.</p>
            {% endif %}
        </div>

        <!-- Footer del Reporte -->
        <div class="report-card">
            <h3 class="section-title">📝 Información del Reporte</h3>
            <div class="profile-stats">
                <div class="profile-stat">
                    <h4>Generado</h4>
                    <p>{{ datetime.now().strftime('%Y-%m-%d %H:%M:%S') }}</p>
                </div>
                <div class="profile-stat">
                    <h4>Sistema</h4>
                    <p>Hotmart Credit Simulator v2.0</p>
                </div>
                <div class="profile-stat">
                    <h4>Alcance</h4>
                    <p>Simulaciones de Sesión (Máx. 10)</p>
                </div>
                <div class="profile-stat">
                    <h4>Uso</h4>
                    <p>Evaluación del Módulo de Curso</p>
                </div>
            </div>
        </div>

        {% else %}
        <!-- Sin Datos -->
        <div class="report-card">
            <div class="no-data">
                <h3>📊 No hay simulaciones registradas</h3>
                <p>Realice algunas evaluaciones de crédito para ver el dashboard de reportes.</p>
                <a href="/" class="btn-action" style="margin-top: 20px;">🏠 Ir a Evaluaciones</a>
            </div>
        </div>
        {% endif %}
    </div>
</body>
</html>
'''

if __name__ == '__main__':
    print("🚀 Iniciando Simulador de Crédito Hotmart - Versión Completa")
    print("📊 Sistema de Evaluación Crediticia con Dashboard de Reportes")
    print("🔐 Panel de Administración Protegido con Clave RAG123")
    print("=" * 60)
    
    load_business_rules()
    print(f"✅ Reglas de negocio cargadas")
    print(f"📋 Score mínimo: {business_rules['score_minimo']}")
    print(f"💰 Monto máximo AAA: ${business_rules['monto_maximo_por_perfil']['AAA']:,}")
    print(f"⚡ Ratio deuda máximo: {business_rules['ratio_deuda_ingreso_maximo']:.0%}")
    print(f"👔 Antigüedad mínima: {business_rules['antiguedad_laboral_minima']} años")
    
    print("\n🌐 Acceso al sistema:")
    print("   • Evaluación: http://localhost:5000/")
    print("   • Administración: http://localhost:5000/admin_login (Clave: RAG123)")
    print("   • Dashboard Reportes: http://localhost:5000/reports")
    print("   • API Test AAA: http://localhost:5000/api/test/aaa")
    print("   • API Reglas: http://localhost:5000/api/rules")
    print("\n🎯 Características principales:")
    print("   ✓ Autenticación administrativa segura")
    print("   ✓ Antigüedad laboral en años (no meses)")
    print("   ✓ Dashboard completo con estadísticas")
    print("   ✓ Registro de máximo 10 simulaciones por sesión")
    print("   ✓ Reporte ejecutivo para evaluación del módulo")
    print("   ✓ Funcionalidad de impresión para reportes")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
