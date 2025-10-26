import json
import os
from datetime import datetime

class Database:
    def __init__(self):
        self.users_file = "users.json"
        self.vehicles_file = "vehicles.json"
        self.missions_file = "missions.json"
        self.init_clean_database()
    
    def init_clean_database(self):
        # BAZĂ DE DATE CURATĂ - NU MAI EXISTĂ DATE VECHI
        if not os.path.exists(self.users_file):
            clean_users = {
                "admin": {"password": "admin123", "type": "admin"}
            }
            self.save_data(self.users_file, clean_users)
        
        if not os.path.exists(self.vehicles_file):
            clean_vehicles = {}
            self.save_data(self.vehicles_file, clean_vehicles)
        
        if not os.path.exists(self.missions_file):
            clean_missions = {}
            self.save_data(self.missions_file, clean_missions)
    
    def save_data(self, filename, data):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    
    def load_data(self, filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    
    # Funcții pentru users
    def get_drivers(self):
        users = self.load_data(self.users_file)
        return {uid: data for uid, data in users.items() if data.get('type') == 'driver'}
    
    def verify_admin(self, password):
        users = self.load_data(self.users_file)
        return users.get('admin', {}).get('password') == password
    
    # Funcții pentru vehicles
    def get_vehicles(self):
        return self.load_data(self.vehicles_file)
    
    # Funcții pentru missions
    def get_missions_by_driver(self, driver_id):
        missions = self.load_data(self.missions_file)
        return {mid: data for mid, data in missions.items() if data.get('sofer') == driver_id}
    
    def get_all_missions(self):
        return self.load_data(self.missions_file)
    
    def add_mission(self, mission_data):
        missions = self.load_data(self.missions_file)
        mission_id = f"mission{len(missions) + 1}"
        missions[mission_id] = mission_data
        self.save_data(self.missions_file, missions)
        return mission_id