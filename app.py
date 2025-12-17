from flask import Flask, render_template, request, jsonify
import pandas as pd
import os
from supabase import create_client, Client
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

def load_data():
    if USE_SUPABASE:
        try:
            supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            response = supabase.table('participants').select("*").execute()
            data = response.data
            
            # Convert to DataFrame to match existing logic structure
            df = pd.DataFrame(data)
            
            # Map columns: Supabase returns 'id' (lowercase) usually, but we defined schema above.
            # However, SQL is case insensitive but response keys might be lowercase.
            # Let's handle standard Supabase lowercase response.
            # Participant table: id, name, relationship, email
            
            # Helper to normalize keys if needed
            if not df.empty:
                 # If we created table with "ID", "nombre"... it might return as such or lowercase.
                 # Best practice in Postgres is snake_case. 
                 # Task Plan said: id, name, relationship, email.
                 # But we need to match internal names: phone, name, relationship, email
                 
                 # Let's map whatever we get to internal
                 # Expected DB columns: id, name, relationship, email
                 rename_map = {
                     'id': 'phone',
                     'ID': 'phone',
                     'nombre': 'name', 
                     'name': 'name',
                     'parentesco': 'relationship',
                     'relationship': 'relationship',
                     'email': 'email'
                 }
                 df = df.rename(columns=rename_map)
            else:
                 return pd.DataFrame(columns=['phone', 'name', 'relationship', 'email'])
                 
            return df
        except Exception as e:
            print(f"Error loading from Supabase: {e}")
            # Fallback to CSV if connection fails? Or return empty?
            # Let's return empty to avoid confusion if config is wrong
            return pd.DataFrame(columns=['phone', 'name', 'relationship', 'email'])

    # Fallback: Load from CSV
    if not os.path.exists(CSV_FILE):
        return pd.DataFrame(columns=list(COL_MAPPING.keys()))
    
    df = pd.read_csv(CSV_FILE, sep=';', dtype={'ID': str})
    df = df.rename(columns=INV_COL_MAPPING)
    for col in COL_MAPPING.keys():
        if col not in df.columns:
            df[col] = ''
    return df

def save_email(phone, email):
    if USE_SUPABASE:
        try:
            supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            # Update user where id == phone
            data, count = supabase.table('participants').update({'email': email}).eq('id', phone).execute()
            return True
        except Exception as e:
            print(f"Error saving to Supabase: {e}")
            return False

    # Fallback: Save to CSV
    df = load_data() # This loads from CSV if USE_SUPABASE is false
    if phone in df['phone'].values:
        df.loc[df['phone'] == phone, 'email'] = email
        
        # Save back
        df_save = df.rename(columns=COL_MAPPING)
        df_save.to_csv(CSV_FILE, sep=';', index=False)
        return True
    return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/check_user', methods=['POST'])
def check_user():
    data = request.json
    phone_input = str(data.get('phone')).strip()
    
    df = load_data()
    
    # Check if phone exists
    if df.empty:
         return jsonify({'found': False, 'message': 'Base de datos no disponible'}), 404

    user = df[df['phone'] == phone_input]
    
    if user.empty:
        return jsonify({'found': False, 'message': 'Teléfono no encontrado'}), 404
    
    user_data = user.iloc[0]
    return jsonify({
        'found': True,
        'name': user_data['name'],
        'message': f"Gracias {user_data['name']}"
    })

@app.route('/api/register_email', methods=['POST'])
def register_email():
    data = request.json
    phone_input = str(data.get('phone')).strip()
    email_input = str(data.get('email')).strip()
    
    # Verify user exists first
    df = load_data()
    if phone_input not in df['phone'].values:
        return jsonify({'success': False, 'message': 'Usuario no encontrado'}), 404
    
    # Save
    success = save_email(phone_input, email_input)
    
    if not success:
         return jsonify({'success': False, 'message': 'Error guardando datos'}), 500
    
    # Get user name again for the success message
    user_name = df[df['phone'] == phone_input].iloc[0]['name']
    
    return jsonify({
        'success': True,
        'message': f"Gracias {user_name}, tu correo ha sido registrado correctamente."
    })

if __name__ == '__main__':
    app.run(debug=True, port=8000)
