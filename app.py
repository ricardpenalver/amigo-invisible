from flask import Flask, render_template, request, jsonify
import csv
import os
import io
import json
import urllib.request
import urllib.error
from dotenv import load_dotenv
import matcher
import email_service

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
            req = urllib.request.Request(url, headers=get_supabase_headers())
            
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status != 200:
                    print(f"Error loading from Supabase: Status {response.status}")
                    return []
                
                # Manual decode
                data = json.loads(response.read().decode('utf-8'))
            
            normalized_data = []
            if data:
                for row in data:
                    normalized_row = {
                        'phone': str(row.get('id') or row.get('ID') or "").strip(),
                        'name': row.get('name') or row.get('nombre') or "",
                        'relationship': row.get('relationship') or row.get('parentesco') or "",
                        'email': row.get('email') or ""
                    }
                    normalized_data.append(normalized_row)
            return normalized_data
        except urllib.error.HTTPError as e:
            print(f"HTTP Error in load_data: {e.code} - {e.read().decode()}")
            return []
        except Exception as e:
            print(f"Error loading from Supabase: {e}")
            return []

    # Fallback: Load from CSV
    if not os.path.exists(CSV_FILE):
        return []
    
    data = []
    try:
        with open(CSV_FILE, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
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
            headers = get_supabase_headers()
            headers["Prefer"] = "return=representation"
            
            # Prepare data
            data = json.dumps({'email': email}).encode('utf-8')
            
            # PATCH method needs to be specified as Request doesn't support it directly via method arg in older python versions simply?
            # method='PATCH' is supported in Python 3.3+
            req = urllib.request.Request(url, data=data, headers=headers, method='PATCH')
            
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status not in [200, 204]:
                    return False, f"Supabase Error: Status {response.status}"
                
                response_data = json.loads(response.read().decode('utf-8'))
                if not response_data:
                     return False, "No se encontró el usuario para actualizar."
                     
                return True, ""
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            print(f"HTTP Error saving to Supabase: {e.code} - {error_body}")
            return False, f"HTTP Error {e.code}: {error_body}"
        except Exception as e:
            print(f"Error saving to Supabase: {e}")
            return False, str(e)

    # Fallback: Save to CSV
    try:
        # We need to read all, update one, write all.
        rows = []
        updated = False
        
        if not os.path.exists(CSV_FILE):
             return False, "Archivo CSV no encontrado"

        fieldnames = ['ID', 'nombre', 'parentesco', 'email']
        
        with open(CSV_FILE, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
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

@app.route('/api/admin/draw', methods=['POST'])
def run_draw():
    try:
        # 1. Verify Admin Secret Key
        provided_key = request.args.get('key')
        admin_key = os.environ.get("ADMIN_SECRET_KEY")
        
        if not admin_key or provided_key != admin_key:
            return jsonify({'success': False, 'message': 'No autorizado'}), 401
            
        # 2. Load participants
        participants = load_data()
        
        # 3. Filter only those who have provided an email
        valid_participants = [p for p in participants if p.get('email')]
        
        if len(valid_participants) < 2:
            return jsonify({'success': False, 'message': 'No hay suficientes participantes con email registrado'}), 400
            
        # 4. Generate assignments
        assignments = matcher.generate_assignments(valid_participants)
        
        if not assignments:
            return jsonify({'success': False, 'message': 'No se pudo generar un sorteo válido con las restricciones actuales'}), 500
            
        # 5. Send emails
        results = []
        for giver, receiver in assignments:
            success = email_service.send_assignment_email(
                giver['email'], 
                giver['name'], 
                receiver['name']
            )
            results.append({'giver': giver['name'], 'success': success})
            
        return jsonify({
            'success': True,
            'message': f'Sorteo completado. Se enviaron {len(results)} correos.',
            'results': results
        })
        
    except Exception as e:
        print(f"CRITICAL ERROR during draw: {e}")
        return jsonify({'success': False, 'message': f'Error interno: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8000)
