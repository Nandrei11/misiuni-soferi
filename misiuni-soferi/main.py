from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
import os
from datetime import datetime, date
from functools import wraps

app = Flask(__name__)
app.secret_key = 'misiuni_soferi_secret_key_2024'

# Inițializare bază de date SQLite
def init_db():
    conn = sqlite3.connect('misiuni_soferi.db')
    c = conn.cursor()
    
    # Tabela șoferi
    c.execute('''
        CREATE TABLE IF NOT EXISTS drivers (
            id TEXT PRIMARY KEY,
            nume TEXT NOT NULL,
            prenume TEXT NOT NULL,
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    
    # Tabela vehicule
    c.execute('''
        CREATE TABLE IF NOT EXISTS vehicles (
            id TEXT PRIMARY KEY,
            tip TEXT NOT NULL,
            nr_inmatriculare TEXT NOT NULL,
            sofer_id TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    
    # Tabela misiuni
    c.execute('''
        CREATE TABLE IF NOT EXISTS missions (
            id TEXT PRIMARY KEY,
            sofer_id TEXT NOT NULL,
            vehicle_id TEXT NOT NULL,
            data_inceput TEXT NOT NULL,
            data_sfarsit TEXT NOT NULL,
            destinatie TEXT NOT NULL,
            distanta INTEGER NOT NULL,
            persoana_contact TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY (sofer_id) REFERENCES drivers (id),
            FOREIGN KEY (vehicle_id) REFERENCES vehicles (id)
        )
    ''')
    
    # Tabela admin
    c.execute('''
        CREATE TABLE IF NOT EXISTS admin (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL
        )
    ''')
    
    # Inserează date inițiale dacă nu există
    c.execute("SELECT COUNT(*) FROM admin WHERE username = 'admin'")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO admin (username, password) VALUES ('admin', 'admin123')")
        
        # Șoferi inițiali
        drivers_data = [
            ('sofer001', 'Popescu', 'Ion'),
            ('sofer002', 'Ionescu', 'Vasile')
        ]
        c.executemany(
            "INSERT INTO drivers (id, nume, prenume, created_at) VALUES (?, ?, ?, ?)",
            [(id, nume, prenume, datetime.now().isoformat()) for id, nume, prenume in drivers_data]
        )
        
        # Vehicule inițiale
        vehicles_data = [
            ('vehicle001', 'Duba', 'B-123-ABC', 'sofer001'),
            ('vehicle002', 'Camion', 'B-456-DEF', 'sofer002')
        ]
        c.executemany(
            "INSERT INTO vehicles (id, tip, nr_inmatriculare, sofer_id, created_at) VALUES (?, ?, ?, ?, ?)",
            [(id, tip, nr, sofer, datetime.now().isoformat()) for id, tip, nr, sofer in vehicles_data]
        )
    
    conn.commit()
    conn.close()

# Funcții helper pentru baza de date
def get_db_connection():
    conn = sqlite3.connect('misiuni_soferi.db')
    conn.row_factory = sqlite3.Row
    return conn

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
        
        conn = get_db_connection()
        admin = conn.execute('SELECT * FROM admin WHERE username = "admin"').fetchone()
        conn.close()
        
        if admin and admin['password'] == password:
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
    conn = get_db_connection()
    
    # Obține toate datele
    drivers = conn.execute('SELECT * FROM drivers').fetchall()
    vehicles = conn.execute('SELECT * FROM vehicles').fetchall()
    missions = conn.execute('''
        SELECT m.*, d.nume, d.prenume, v.tip, v.nr_inmatriculare 
        FROM missions m 
        LEFT JOIN drivers d ON m.sofer_id = d.id 
        LEFT JOIN vehicles v ON m.vehicle_id = v.id
    ''').fetchall()
    
    conn.close()
    
    today = date.today().isoformat()
    
    # Separa misiunile active de cele istorice
    active_missions = [m for m in missions if m['data_sfarsit'] >= today]
    completed_missions = [m for m in missions if m['data_sfarsit'] < today]
    
    # Sortează misiunile istorice descrescător
    completed_missions.sort(key=lambda x: x['data_inceput'], reverse=True)
    
    return render_template('admin_dashboard.html', 
                         active_missions=active_missions,
                         completed_missions=completed_missions,
                         drivers=drivers,
                         vehicles=vehicles,
                         today=today)

@app.route('/create_mission', methods=['POST'])
@admin_required
def create_mission():
    mission_data = (
        f"mission{datetime.now().strftime('%Y%m%d%H%M%S')}",
        request.form.get('sofer'),
        request.form.get('vehicul'),
        request.form.get('data_inceput'),
        request.form.get('data_sfarsit'),
        request.form.get('destinatie'),
        request.form.get('distanta'),
        request.form.get('persoana_contact'),
        'active',
        datetime.now().isoformat()
    )
    
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO missions (id, sofer_id, vehicle_id, data_inceput, data_sfarsit, 
                            destinatie, distanta, persoana_contact, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', mission_data)
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'mission_id': mission_data[0]})

@app.route('/update_mission/<mission_id>', methods=['POST'])
@admin_required
def update_mission(mission_id):
    conn = get_db_connection()
    conn.execute('''
        UPDATE missions 
        SET sofer_id = ?, vehicle_id = ?, data_inceput = ?, data_sfarsit = ?,
            destinatie = ?, distanta = ?, persoana_contact = ?, updated_at = ?
        WHERE id = ?
    ''', (
        request.form.get('sofer'),
        request.form.get('vehicul'),
        request.form.get('data_inceput'),
        request.form.get('data_sfarsit'),
        request.form.get('destinatie'),
        request.form.get('distanta'),
        request.form.get('persoana_contact'),
        datetime.now().isoformat(),
        mission_id
    ))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/delete_mission/<mission_id>')
@admin_required
def delete_mission(mission_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM missions WHERE id = ?', (mission_id,))
    conn.commit()
    conn.close()
    
    return redirect(url_for('admin_dashboard'))

@app.route('/get_mission_data/<mission_id>')
@admin_required
def get_mission_data(mission_id):
    conn = get_db_connection()
    mission = conn.execute('SELECT * FROM missions WHERE id = ?', (mission_id,)).fetchone()
    conn.close()
    
    if mission:
        return jsonify({
            'success': True, 
            'mission': dict(mission)
        })
    
    return jsonify({'success': False, 'error': 'Misiunea nu a fost găsită'})

@app.route('/export_active_missions')
@admin_required
def export_active_missions():
    conn = get_db_connection()
    
    today = date.today().isoformat()
    active_missions = conn.execute('''
        SELECT m.*, d.nume, d.prenume, v.tip, v.nr_inmatriculare 
        FROM missions m 
        LEFT JOIN drivers d ON m.sofer_id = d.id 
        LEFT JOIN vehicles v ON m.vehicle_id = v.id
        WHERE m.data_sfarsit >= ?
    ''', (today,)).fetchall()
    
    conn.close()
    
    text_to_copy = "🚛 *MISIUNI ACTIVE* 🚛\n"
    text_to_copy += "══════════════════\n\n"
    
    for mission in active_missions:
        text_to_copy += f"👤 *Șofer:* {mission['prenume']} {mission['nume']}\n"
        text_to_copy += f"🚗 *Vehicul:* {mission['tip']} - {mission['nr_inmatriculare']}\n"
        text_to_copy += f"📅 *Perioadă:* {mission['data_inceput']} - {mission['data_sfarsit']}\n"
        text_to_copy += f"🎯 *Destinație:* {mission['destinatie']}\n"
        text_to_copy += f"📏 *Distanță:* {mission['distanta']} km\n"
        text_to_copy += f"📞 *Contact:* {mission['persoana_contact']}\n"
        text_to_copy += "────────────────────\n\n"
    
    text_to_copy += "_Trimis din aplicația Misiuni Șoferi_"
    
    return render_template('export.html', export_text=text_to_copy)

# === GESTIONARE ȘOFERI ===
@app.route('/manage_drivers')
@admin_required
def manage_drivers():
    conn = get_db_connection()
    drivers = conn.execute('SELECT * FROM drivers').fetchall()
    conn.close()
    
    return render_template('manage_drivers.html', drivers=drivers)

@app.route('/add_driver', methods=['POST'])
@admin_required
def add_driver():
    driver_id = f"sofer{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO drivers (id, nume, prenume, created_at)
        VALUES (?, ?, ?, ?)
    ''', (
        driver_id,
        request.form.get('nume'),
        request.form.get('prenume'),
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'driver_id': driver_id})

@app.route('/update_driver/<driver_id>', methods=['POST'])
@admin_required
def update_driver(driver_id):
    conn = get_db_connection()
    conn.execute('''
        UPDATE drivers 
        SET nume = ?, prenume = ?, updated_at = ?
        WHERE id = ?
    ''', (
        request.form.get('nume'),
        request.form.get('prenume'),
        datetime.now().isoformat(),
        driver_id
    ))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/delete_driver/<driver_id>')
@admin_required
def delete_driver(driver_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM drivers WHERE id = ?', (driver_id,))
    conn.commit()
    conn.close()
    
    return redirect(url_for('manage_drivers'))

@app.route('/get_driver_data/<driver_id>')
@admin_required
def get_driver_data(driver_id):
    conn = get_db_connection()
    driver = conn.execute('SELECT * FROM drivers WHERE id = ?', (driver_id,)).fetchone()
    conn.close()
    
    if driver:
        return jsonify({'success': True, 'driver': dict(driver)})
    
    return jsonify({'success': False, 'error': 'Șoferul nu a fost găsit'})

# === GESTIONARE VEHICULE ===
@app.route('/manage_vehicles')
@admin_required
def manage_vehicles():
    conn = get_db_connection()
    vehicles = conn.execute('SELECT * FROM vehicles').fetchall()
    conn.close()
    
    return render_template('manage_vehicles.html', vehicles=vehicles)

@app.route('/add_vehicle', methods=['POST'])
@admin_required
def add_vehicle():
    vehicle_id = f"vehicle{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO vehicles (id, tip, nr_inmatriculare, created_at)
        VALUES (?, ?, ?, ?)
    ''', (
        vehicle_id,
        request.form.get('tip'),
        request.form.get('nr_inmatriculare'),
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'vehicle_id': vehicle_id})

@app.route('/update_vehicle/<vehicle_id>', methods=['POST'])
@admin_required
def update_vehicle(vehicle_id):
    conn = get_db_connection()
    conn.execute('''
        UPDATE vehicles 
        SET tip = ?, nr_inmatriculare = ?, updated_at = ?
        WHERE id = ?
    ''', (
        request.form.get('tip'),
        request.form.get('nr_inmatriculare'),
        datetime.now().isoformat(),
        vehicle_id
    ))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/delete_vehicle/<vehicle_id>')
@admin_required
def delete_vehicle(vehicle_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM vehicles WHERE id = ?', (vehicle_id,))
    conn.commit()
    conn.close()
    
    return redirect(url_for('manage_vehicles'))

@app.route('/get_vehicle_data/<vehicle_id>')
@admin_required
def get_vehicle_data(vehicle_id):
    conn = get_db_connection()
    vehicle = conn.execute('SELECT * FROM vehicles WHERE id = ?', (vehicle_id,)).fetchone()
    conn.close()
    
    if vehicle:
        return jsonify({'success': True, 'vehicle': dict(vehicle)})
    
    return jsonify({'success': False, 'error': 'Vehiculul nu a fost găsit'})

@app.route('/driver/<driver_id>')
def driver_view(driver_id):
    conn = get_db_connection()
    
    today = date.today().isoformat()
    missions = conn.execute('''
        SELECT m.*, v.tip, v.nr_inmatriculare 
        FROM missions m 
        LEFT JOIN vehicles v ON m.vehicle_id = v.id
        WHERE m.sofer_id = ? AND m.data_sfarsit >= ?
    ''', (driver_id, today)).fetchall()
    
    driver = conn.execute('SELECT * FROM drivers WHERE id = ?', (driver_id,)).fetchone()
    conn.close()
    
    return render_template('driver_view.html', 
                         missions=missions,
                         driver_info=driver,
                         vehicles=[])

if __name__ == '__main__':
    # Inițializează baza de date
    init_db()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
