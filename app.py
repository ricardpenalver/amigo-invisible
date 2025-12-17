from flask import Flask, render_template, request, jsonify
import csv
import os
import io
import requests
from dotenv import load_dotenv

# Load environment variables from .env file (if exists)
load_dotenv()

app = Flask(__name__)

# CSV Configuration (Fallback)
CSV_FILE = 'bbdd-amigoinvisible.csv'

# Supabase Configuration
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
USE_SUPABASE = SUPABASE_URL and SUPABASE_KEY

# Column mapping: Internal name -> CSV header / DB column
COL_MAPPING = {
    'phone': 'ID',
    'name': 'nombre',
    'relationship': 'parentesco',
    'email': 'email'
}
INV_COL_MAPPING = {v: k for k, v in COL_MAPPING.items()}

def get_supabase_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

def load_data():
    """
    Returns a list of dictionaries with internal keys: phone, name, relationship, email
    """
    if USE_SUPABASE:
        try:
            url = f"{SUPABASE_URL}/rest/v1/participants?select=*"
            response = requests.get(url, headers=get_supabase_headers(), timeout=10)
            
            if response.status_code != 200:
                print(f"Error loading from Supabase: {response.text}")
                return []
                
            data = response.json() # List of dicts
            
            normalized_data = []
            if data:
                for row in data:
                    # Supabase/Postgres might return keys in lowercase.
                    # We map them to our internal structure.
                    normalized_row = {
                        'phone': str(row.get('id') or row.get('ID') or "").strip(),
                        'name': row.get('name') or row.get('nombre') or "",
                        'relationship': row.get('relationship') or row.get('parentesco') or "",
                        'email': row.get('email') or ""
                    }
                    normalized_data.append(normalized_row)
            return normalized_data
        except Exception as e:
            print(f"Error loading from Supabase: {e}")
            return []

    # Fallback: Load from CSV
    if not os.path.exists(CSV_FILE):
        return []
    
    data = []
    try:
        with open(CSV_FILE, mode='r', encoding='utf-8') as f:
            # Detect separator if needed, but we enforced semicolon
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                # Row keys are CSV headers (ID, nombre, etc)
                # Map to internal
                internal_row = {
                    'phone': str(row.get(COL_MAPPING['phone'], '')).strip(),
                    'name': row.get(COL_MAPPING['name'], ''),
                    'relationship': row.get(COL_MAPPING['relationship'], ''),
                    'email': row.get(COL_MAPPING['email'], '')
                }
                data.append(internal_row)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return []
        
    return data

def save_email(phone, email):
    if USE_SUPABASE:
        try:
            url = f"{SUPABASE_URL}/rest/v1/participants?id=eq.{phone}"
            # Patch request to update
            response = requests.patch(
                url, 
                json={'email': email}, 
                headers={**get_supabase_headers(), "Prefer": "return=representation"}, # Return data to verify
                timeout=10
            )
            
            if response.status_code not in [200, 204]:
                return False, f"Supabase Error: {response.text}"
            
            data = response.json()
            if not data:
                 return False, "No se encontró el usuario para actualizar."
                 
            return True, ""
        except Exception as e:
            print(f"Error saving to Supabase: {e}")
            return False, str(e)

    # Fallback: Save to CSV
    try:
        # We need to read all, update one, write all.
        # But we need to write back using CSV headers.
        rows = []
        updated = False
        
        # Read existing raw content to preserve structure
        if not os.path.exists(CSV_FILE):
            return False, "Archivo CSV no encontrado"

        fieldnames = ['ID', 'nombre', 'parentesco', 'email']
        
        with open(CSV_FILE, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                # Check match using CSV header 'ID' which maps to phone
                if str(row.get('ID', '')).strip() == phone:
                    row['email'] = email
                    updated = True
                rows.append(row)
        
        if updated:
            with open(CSV_FILE, mode='w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
                writer.writeheader()
                writer.writerows(rows)
            return True, ""
        
        return False, "Usuario no encontrado en CSV"
            
    except Exception as e:
        print(f"Error saving to CSV (Fallback): {e}")
        return False, str(e)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/check_user', methods=['POST'])
def check_user():
    try:
        data = request.json
        phone_input = str(data.get('phone')).strip()
        
        participants = load_data()
        
        # Find user
        user = next((p for p in participants if p['phone'] == phone_input), None)
        
        if not user:
            return jsonify({'found': False, 'message': 'Teléfono no encontrado'}), 200 # Return 200 for JSON visibility
        
        return jsonify({
            'found': True,
            'name': user['name'],
            'message': f"Gracias {user['name']}"
        })
    except Exception as e:
        return jsonify({'found': False, 'message': f'Error interno: {str(e)}'}), 200

@app.route('/api/register_email', methods=['POST'])
def register_email():
    try:
        data = request.json
        phone_input = str(data.get('phone')).strip()
        email_input = str(data.get('email')).strip()
        
        # Verify user exists first
        participants = load_data()
        user_exists = any(p['phone'] == phone_input for p in participants)
        
        if not user_exists:
            return jsonify({'success': False, 'message': 'Usuario no encontrado'}), 200
        
        # Save
        success, error_msg = save_email(phone_input, email_input)
        
        if not success:
             return jsonify({'success': False, 'message': f'Error guardando: {error_msg}'}), 200
        
        # Get user name again manually
        user_name = next((p['name'] for p in participants if p['phone'] == phone_input), "")
        
        return jsonify({
            'success': True,
            'message': f"Gracias {user_name}, tu correo ha sido registrado correctamente."
        })
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        return jsonify({'success': False, 'message': f'Error interno del servidor: {str(e)}'}), 200

if __name__ == '__main__':
    app.run(debug=True, port=8000)
