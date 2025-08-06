#!/usr/bin/env python3
"""
Simulador Completo de Gestión de Crédito - Hotmart
Con Panel de Administración para Reglas de Negocio
Versión Definitiva Corregida - Templates Separados Correctamente
"""

import os
import json
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify, redirect, url_for

app = Flask(__name__)
# Usar una clave secreta para la sesión, esencial para seguridad.
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'hotmart_credit_sim_secret_key')

# Configuración de reglas de negocio por defecto
DEFAULT_RULES = {
    "score_minimo": 650,
    "edad_minima": 18,
    "edad_maxima": 70,
    "ingresos_minimos": 15000,
    "antiguedad_laboral_minima": 12,  # en meses
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

class CreditEvaluator:
    def __init__(self):
        self.rules = business_rules
    
    def calculate_risk_profile(self, data):
        """Calcula el perfil de riesgo basado en múltiples factores, con un score de 0 a 100"""
        score = 0
        factors = []
        
        # Factor Score Crediticio (40%)
        score_credit = int(data.get('score_crediticio', 0))
        score_mapping = {
            'AAA': (800, 850), 'AA': (750, 799), 'A': (700, 749),
            'BBB': (650, 699), 'BB': (600, 649), 'B': (550, 599)
        }
        for profile, (min_s, max_s) in score_mapping.items():
            if min_s <= score_credit <= max_s:
                score += (40 * (score_credit - min_s)) / (max_s - min_s) if (max_s - min_s) > 0 else 40
                factors.append(f"Score crediticio: {score_credit} ({profile})")
                break
        
        # Factor Ingresos (25%)
        ingresos = float(data.get('ingresos_mensuales', 0))
        ingresos_weight = 0
        if ingresos >= 50000: ingresos_weight = 25
        elif ingresos >= 30000: ingresos_weight = 20
        elif ingresos >= 20000: ingresos_weight = 15
        elif ingresos >= 15000: ingresos_weight = 10
        else: ingresos_weight = 2
        score += ingresos_weight
        factors.append(f"Ingresos mensuales: ${ingresos:,.0f}")

        # Factor Antigüedad Laboral (15%)
        antiguedad = int(data.get('antiguedad_laboral', 0))
        antiguedad_weight = 0
        if antiguedad >= 60: antiguedad_weight = 15
        elif antiguedad >= 36: antiguedad_weight = 12
        elif antiguedad >= 24: antiguedad_weight = 10
        elif antiguedad >= 12: antiguedad_weight = 7
        else: antiguedad_weight = 2
        score += antiguedad_weight
        factors.append(f"Antigüedad laboral: {antiguedad} meses")

        # Factor Edad (10%)
        edad = int(data.get('edad', 0))
        edad_weight = 0
        if 35 <= edad <= 50: edad_weight = 10
        elif 25 <= edad < 35 or 50 < edad <= 60: edad_weight = 8
        elif 18 <= edad < 25 or 60 < edad <= 65: edad_weight = 5
        else: edad_weight = 1
        score += edad_weight
        factors.append(f"Edad: {edad} años")

        # Factor Ratio Deuda-Ingreso (10%)
        deudas = float(data.get('deudas_actuales', 0))
        ratio_deuda = deudas / ingresos if ingresos > 0 else 1
        ratio_weight = 0
        if ratio_deuda <= 0.10: ratio_weight = 10
        elif ratio_deuda <= 0.20: ratio_weight = 8
        elif ratio_deuda <= 0.30: ratio_weight = 6
        elif ratio_deuda <= 0.35: ratio_weight = 3
        else: ratio_weight = 1
        score += ratio_weight
        factors.append(f"Ratio deuda-ingreso: {ratio_deuda:.2%}")
        
        # Determinar perfil basado en score total
        profile = "RECHAZADO"
        if score >= 85: profile = "AAA"
        elif score >= 75: profile = "AA"
        elif score >= 65: profile = "A"
        elif score >= 55: profile = "BBB"
        elif score >= 45: profile = "BB"
        elif score >= 35: profile = "B"
        
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
        
        antiguedad = int(data.get('antiguedad_laboral', 0))
        if antiguedad < self.rules['antiguedad_laboral_minima']:
            errors.append(f"Antigüedad laboral insuficiente: {antiguedad} meses < {self.rules['antiguedad_laboral_minima']} meses")
        
        deudas = float(data.get('deudas_actuales', 0))
        ratio_deuda = deudas / ingresos if ingresos > 0 else 1
        if ratio_deuda > self.rules['ratio_deuda_ingreso_maximo']:
            errors.append(f"Ratio deuda-ingreso excesivo: {ratio_deuda:.2%} > {self.rules['ratio_deuda_ingreso_maximo']:.2%}")
        
        return errors, warnings
    
    def calculate_credit_offer(self, profile_data, monto_solicitado=None):
        """Calcula la oferta de crédito basada en el perfil"""
        profile = profile_data['perfil']
        if profile == "RECHAZADO": return None
        
        monto_maximo = self.rules['monto_maximo_por_perfil'][profile]
        tasa_info = self.rules['tasas_por_perfil'][profile]
        plazo_info = self.rules['plazos_por_perfil'][profile]
        
        monto_ofrecido = monto_maximo
        if monto_solicitado and monto_solicitado <= monto_maximo:
            monto_ofrecido = monto_solicitado
        
        # Tasa ajustada inversamente al score dentro del rango del perfil
        tasa_anual = tasa_info['min'] + (tasa_info['max'] - tasa_info['min']) * (1 - (profile_data['score_total'] / 100))
        tasa_anual = max(tasa_info['min'], min(tasa_info['max'], tasa_anual))
        
        # Plazo recomendado basado en monto y perfil
        plazo_meses = plazo_info['max']
        if monto_ofrecido < 50000:
            plazo_meses = min(36, plazo_info['max'])
        
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
                return {"aprobado": False, "motivo_rechazo": "No cumple requisitos básicos", "errores": errors, "advertencias": warnings}
            
            profile_data = self.calculate_risk_profile(data)
            if profile_data['perfil'] == "RECHAZADO":
                return {"aprobado": False, "motivo_rechazo": "Perfil de riesgo muy bajo", "perfil_riesgo": profile_data, "advertencias": warnings}
            
            oferta = self.calculate_credit_offer(profile_data, float(data.get('monto_solicitado', 0)))
            
            return {
                "aprobado": True,
                "perfil_riesgo": profile_data,
                "oferta_credito": oferta,
                "advertencias": warnings,
                "fecha_evaluacion": datetime.now().isoformat()
            }
        except Exception as e:
            return {"aprobado": False, "motivo_rechazo": f"Error en evaluación: {str(e)}", "error_tecnico": True}

load_business_rules()
evaluator = CreditEvaluator()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            form_data = {
                'nombre': request.form.get('nombre', ''),
                'edad': int(request.form.get('edad', 0)),
                'score_crediticio': int(request.form.get('score_crediticio', 0)),
                'ingresos_mensuales': float(request.form.get('ingresos_mensuales', 0)),
                'deudas_actuales': float(request.form.get('deudas_actuales', 0)),
                'antiguedad_laboral': int(request.form.get('antiguedad_laboral', 0)),
                'monto_solicitado': float(request.form.get('monto_solicitado', 0)) if request.form.get('monto_solicitado') else None,
                'proposito': request.form.get('proposito', 'personal')
            }
            resultado = evaluator.evaluate_credit_request(form_data)
            return render_template_string(MAIN_TEMPLATE, resultado=resultado)
        except (ValueError, TypeError) as e:
            return render_template_string(MAIN_TEMPLATE, resultado={"aprobado": False, "motivo_rechazo": f"Datos incompletos o incorrectos: {str(e)}"})
    return render_template_string(MAIN_TEMPLATE, resultado=None)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
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
            elif action == 'save':
                new_rules = {}
                for key, value in request.form.items():
                    if key in ['action']: continue
                    
                    if key in ['score_minimo', 'edad_minima', 'edad_maxima', 'ingresos_minimos', 'antiguedad_laboral_minima']:
                        new_rules[key] = int(value)
                    elif key == 'ratio_deuda_ingreso_maximo':
                        new_rules[key] = float(value) / 100
                    elif key.startswith('monto_'):
                        perfil = key.split('_')[-1]
                        if 'monto_maximo_por_perfil' not in new_rules: new_rules['monto_maximo_por_perfil'] = business_rules['monto_maximo_por_perfil'].copy()
                        new_rules['monto_maximo_por_perfil'][perfil] = int(value)
                    elif key.startswith('tasa_min_') or key.startswith('tasa_max_'):
                        partes = key.split('_')
                        tipo, perfil = partes[1], partes[2]
                        if 'tasas_por_perfil' not in new_rules: new_rules['tasas_por_perfil'] = business_rules['tasas_por_perfil'].copy()
                        if perfil not in new_rules['tasas_por_perfil']: new_rules['tasas_por_perfil'][perfil] = business_rules['tasas_por_perfil'][perfil].copy()
                        new_rules['tasas_por_perfil'][perfil][tipo] = float(value)
                    elif key.startswith('plazo_max_'):
                        perfil = key.split('_')[-1]
                        if 'plazos_por_perfil' not in new_rules: new_rules['plazos_por_perfil'] = business_rules['plazos_por_perfil'].copy()
                        if perfil not in new_rules['plazos_por_perfil']: new_rules['plazos_por_perfil'][perfil] = business_rules['plazos_por_perfil'][perfil].copy()
                        new_rules['plazos_por_perfil'][perfil]['max'] = int(value)
                
                business_rules.update(new_rules)
                save_business_rules()
                evaluator = CreditEvaluator()
                mensaje = "✅ Configuración guardada exitosamente"
        except Exception as e:
            mensaje = f"❌ Error al guardar configuración: {str(e)}"
    return render_template_string(ADMIN_TEMPLATE, rules=business_rules, mensaje=mensaje, tipo_mensaje='success' if mensaje and '✅' in mensaje else 'danger')

@app.route('/reports')
def reports():
    return render_template_string(REPORTS_TEMPLATE)

def validate_rules(rules):
    validation_results = []
    if rules['edad_minima'] < rules['edad_maxima']: validation_results.append("✓ Rango de edad válido")
    else: validation_results.append("❌ Rango de edad inválido")
    if 0 < rules['ratio_deuda_ingreso_maximo'] <= 1: validation_results.append("✓ Ratio deuda-ingreso válido")
    else: validation_results.append("❌ Ratio deuda-ingreso inválido")
    for perfil, tasas in rules['tasas_por_perfil'].items():
        if tasas['min'] < tasas['max']: validation_results.append(f"✓ Tasas {perfil} válidas")
        else: validation_results.append(f"❌ Tasas {perfil} inválidas")
    return validation_results

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
            <a href="/admin" class="nav-btn">⚙️ Administración</a>
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
                    <div class="form-group"><label for="antiguedad_laboral">Antigüedad Laboral (meses) *</label><input type="number" id="antiguedad_laboral" name="antiguedad_laboral" min="0" required></div>
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
        .btn-primary { background: #667eea; color: white; border: none; padding: 12px 30px; border-radius: 5px; cursor: pointer; font-weight: 600; }
        .btn-primary:hover { background: #5a67d8; }
        .btn-secondary { background: #6c757d; color: white; border: none; padding: 12px 30px; border-radius: 5px; cursor: pointer; font-weight: 600; margin-left: 10px; }
        .btn-secondary:hover { background: #5a6268; }
        .alert { padding: 15px; border-radius: 5px; margin: 15px 0; }
        .alert-success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .alert-danger { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        @media (max-width: 768px) {
            .rules-grid { grid-template-columns: 1fr; }
            .profile-inputs { grid-template-columns: 1fr 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header"><h1>⚙️ Panel de Administración</h1><p>Configuración de Reglas de Negocio</p></div>
        <div class="nav-buttons">
            <a href="/" class="nav-btn">🏠 Evaluación</a>
            <a href="/admin" class="nav-btn active">⚙️ Administración</a>
            <a href="/reports" class="nav-btn">📊 Reportes</a>
        </div>
        {% if mensaje %}<div class="alert alert-{{ tipo_mensaje }}">{{ mensaje }}</div>{% endif %}
        <div class="admin-card">
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
                            <div class="form-group"><label>Antigüedad Laboral Mínima (meses)</label><input type="number" name="antiguedad_laboral_minima" value="{{ rules.antiguedad_laboral_minima }}" min="1" max="60"></div>
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
    <title>Reportes - Hotmart Credit</title>
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
        .card { background: white; border-radius: 15px; padding: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header"><h1>📊 Reportes</h1><p>Análisis y Estadísticas del Sistema</p></div>
        <div class="nav-buttons">
            <a href="/" class="nav-btn">🏠 Evaluación</a>
            <a href="/admin" class="nav-btn">⚙️ Administración</a>
            <a href="/reports" class="nav-btn active">📊 Reportes</a>
        </div>
        <div class="card">
            <h2>🚧 Módulo en Desarrollo</h2>
            <p>Esta sección contendrá reportes detallados sobre:</p>
            <ul style="text-align: left; max-width: 500px; margin: 20px auto;">
                <li>📈 Estadísticas de aprobación por perfil</li>
                <li>💰 Análisis de montos otorgados</li>
                <li>⚠️ Factores de rechazo más comunes</li>
                <li>📊 Tendencias de evaluación</li>
                <li>🎯 Performance del sistema</li>
            </ul>
            <p style="margin-top: 20px;"><em>Próximamente disponible...</em></p>
        </div>
    </div>
</body>
</html>
'''

if __name__ == '__main__':
    print("🚀 Iniciando Simulador de Crédito Hotmart")
    print("📊 Sistema de Evaluación Crediticia Integral")
    print("=" * 50)
    load_business_rules()
    print(f"✅ Reglas de negocio cargadas")
    print(f"📋 Score mínimo: {business_rules['score_minimo']}")
    print(f"💰 Monto máximo AAA: ${business_rules['monto_maximo_por_perfil']['AAA']:,}")
    print(f"⚡ Ratio deuda máximo: {business_rules['ratio_deuda_ingreso_maximo']:.0%}")
    print("\n🌐 Acceso al sistema:")
    print("   • Evaluación: http://localhost:5000/")
    print("   • Administración: http://localhost:5000/admin")
    print("   • Reportes: http://localhost:5000/reports")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)
