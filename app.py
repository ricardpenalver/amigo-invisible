from flask import Flask, render_template, request, jsonify
import pandas as pd
import os

app = Flask(__name__)
DATA_FILE = 'bbdd-amigoinvisible.csv'

# Column mapping: Internal name -> CSV header
COL_MAPPING = {
    'phone': 'ID',
    'name': 'nombre',
    'relationship': 'parentesco',
    'email': 'email'
}

# Reverse mapping for loading
INV_COL_MAPPING = {v: k for k, v in COL_MAPPING.items()}

def load_data():
    if not os.path.exists(DATA_FILE):
        return pd.DataFrame(columns=list(COL_MAPPING.keys()))
    
    # Read with semicolon separator
    df = pd.read_csv(DATA_FILE, sep=';', dtype={'ID': str})
    
    # Rename columns to internal names
    df = df.rename(columns=INV_COL_MAPPING)
    
    # Ensure all internal columns exist
    for col in COL_MAPPING.keys():
        if col not in df.columns:
            df[col] = ''
            
    return df

def save_data(df):
    # Rename back to CSV headers
    df_save = df.rename(columns=COL_MAPPING)
    
    # Save with semicolon separator
    df_save.to_csv(DATA_FILE, sep=';', index=False)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/check_user', methods=['POST'])
def check_user():
    data = request.json
    phone_input = str(data.get('phone')).strip()
    
    df = load_data()
    
    # Check if phone exists
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
    
    df = load_data()
    
    if phone_input not in df['phone'].values:
        return jsonify({'success': False, 'message': 'Usuario no encontrado'}), 404
    
    # Update email
    df.loc[df['phone'] == phone_input, 'email'] = email_input
    save_data(df)
    
    # Get user name again for the success message
    user_name = df[df['phone'] == phone_input].iloc[0]['name']
    
    return jsonify({
        'success': True,
        'message': f"Gracias {user_name}, tu correo ha sido registrado correctamente."
    })

if __name__ == '__main__':
    app.run(debug=True, port=8000)
