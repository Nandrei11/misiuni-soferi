from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import json
import os
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = 'misiuni_soferi_secret_key_2024'

# Încarcă baza de date
def load_db(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_db(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# Decorator pentru verificare admin
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if session.get('is_admin'):
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        users = load_db('users.json')
        
        if users.get('admin', {}).get('password') == password:
            session['is_admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('login.html', error='Parolă incorectă')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/admin')
@admin_required
def admin_dashboard():
    missions = load_db('missions.json')
    drivers = {k: v for k, v in load_db('users.json').items() if v.get('type') == 'driver'}
    vehicles = load_db('vehicles.json')
    
    active_missions = {mid: m for mid, m in missions.items() if m.get('status') == 'active'}
    completed_missions = {mid: m for mid, m in missions.items() if m.get('status') == 'completed'}
    
    return render_template('admin_dashboard.html', 
                         active_missions=active_missions,
                         completed_missions=completed_missions,
                         drivers=drivers,
                         vehicles=vehicles)

@app.route('/create_mission', methods=['POST'])
@admin_required
def create_mission():
    mission_data = {
        'sofer': request.form.get('sofer'),
        'vehicul': request.form.get('vehicul'),
        'data': request.form.get('data'),
        'destinatie': request.form.get('destinatie'),
        'distanta': request.form.get('distanta'),
        'persoana_contact': request.form.get('persoana_contact'),
        'status': 'active'
    }
    
    missions = load_db('missions.json')
    mission_id = f"mission{len(missions) + 1}"
    missions[mission_id] = mission_data
    save_db('missions.json', missions)
    
    return jsonify({'success': True, 'mission_id': mission_id})

@app.route('/export_active_missions')
@admin_required
def export_active_missions():
    missions = load_db('missions.json')
    drivers = load_db('users.json')
    vehicles = load_db('vehicles.json')
    
    active_missions = {mid: m for mid, m in missions.items() if m.get('status') == 'active'}
    
    text_to_copy = "🚛 *MISIUNI ACTIVE* 🚛\n"
    text_to_copy += "══════════════════\n\n"
    
    for mission_id, mission in active_missions.items():
        driver_info = drivers.get(mission['sofer'], {'prenume': 'Necunoscut', 'nume': ''})
        vehicle_info = vehicles.get(mission['vehicul'], {'tip': 'Necunoscut', 'nr_inmatriculare': ''})
        
        text_to_copy += f"👤 *Șofer:* {driver_info.get('prenume', '')} {driver_info.get('nume', '')}\n"
        text_to_copy += f"🚗 *Vehicul:* {vehicle_info.get('tip', '')} - {vehicle_info.get('nr_inmatriculare', '')}\n"
        text_to_copy += f"📅 *Data:* {mission['data']}\n"
        text_to_copy += f"🎯 *Destinație:* {mission['destinatie']}\n"
        text_to_copy += f"📏 *Distanță:* {mission['distanta']} km\n"
        text_to_copy += f"📞 *Contact:* {mission['persoana_contact']}\n"
        text_to_copy += "────────────────────\n\n"
    
    text_to_copy += "_Trimis din aplicația Misiuni Șoferi_"
    
    return render_template('export.html', export_text=text_to_copy)

@app.route('/driver/<driver_id>')
def driver_view(driver_id):
    missions = load_db('missions.json')
    drivers = load_db('users.json')
    vehicles = load_db('vehicles.json')
    
    driver_missions = {mid: m for mid, m in missions.items() if m.get('sofer') == driver_id}
    driver_info = drivers.get(driver_id, {})
    
    return render_template('driver_view.html', 
                         missions=driver_missions,
                         driver_info=driver_info,
                         vehicles=vehicles)

if __name__ == '__main__':
    # Inițializează baza de date dacă nu există
    if not os.path.exists('users.json'):
        save_db('users.json', {
            'admin': {'password': 'admin123', 'type': 'admin'},
            'sofer1': {'password': '', 'type': 'driver', 'nume': 'Popescu', 'prenume': 'Ion'},
            'sofer2': {'password': '', 'type': 'driver', 'nume': 'Ionescu', 'prenume': 'Vasile'}
        })
    
    if not os.path.exists('vehicles.json'):
        save_db('vehicles.json', {
            'vehicle1': {'tip': 'Duba', 'nr_inmatriculare': 'B-123-ABC', 'sofer': 'sofer1'},
            'vehicle2': {'tip': 'Camion', 'nr_inmatriculare': 'B-456-DEF', 'sofer': 'sofer2'}
        })
    
    if not os.path.exists('missions.json'):
        save_db('missions.json', {})
    
    # SCHIMBARE PENTRU RENDER:
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
