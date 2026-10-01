# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import requests
import pandas as pd
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "barama_secret_key"

# 1. FILTRO DE FECHA
@app.template_filter('formato_fecha')
def formato_fecha(fecha_str):
    if not fecha_str:
        return "sin fecha"
    try:
        fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d')
        return fecha_obj.strftime('%d/%m/%Y')
    except Exception:
        return fecha_str

# 2. ENVIAR NOTIFICACIÓN A TELEGRAM
def enviar_notificacion(empresa, operador, falla, reporte_id):
    token = "8044184355:AAHq1hS7lX2o5WzrY3wTX1AZr4a2P4arXV8"
    chat_id = "7212247151" 
    
    texto = (
        f"🆔 *REPORTE # {reporte_id}*\n"
        f"🚨 *NUEVA FALLA DETECTADA*\n\n"
        f"🏢 *Empresa:* {empresa}\n"
        f"👤 *Operador:* {operador}\n"
        f"🛠️ *Falla:* {falla}\n"
        f"📅 *Fecha:* {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    )
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': texto,
        'parse_mode': 'Markdown'
    }
    
    try:
        respuesta = requests.post(url, data=payload)
        print(f"Telegram respuesta: {respuesta.status_code}")
    except Exception as e:
        print(f"Error enviando Telegram: {e}")

# 3. ACTUALIZAR ARCHIVO EXCEL
def actualizar_excel():
    try:
        ruta_carpeta = os.path.dirname(os.path.abspath(__file__))
        nombre_archivo = "Reporte_General_Barama.xlsx"
        ruta_completa = os.path.join(ruta_carpeta, nombre_archivo)
        
        conn = sqlite3.connect('inspecciones.db')
        df_total = pd.read_sql_query("SELECT * FROM registros ORDER BY id DESC", conn)
        conn.close()

        if df_total.empty:
            return

        if os.path.exists(ruta_completa):
            try:
                os.remove(ruta_completa)
            except OSError:
                print("❌ ERROR: Cierre el archivo Excel para actualizarlo.")
                return 

        with pd.ExcelWriter(ruta_completa, engine='openpyxl') as writer:
            df_total.to_excel(writer, sheet_name='HISTORIAL GENERAL', index=False)
            
            empresas = df_total['empresa'].unique()
            for empresa in empresas:
                nom_emp = str(empresa).strip() if empresa else "Sin Nombre"
                df_empresa = df_total[df_total['empresa'] == empresa]
                pestaña = "".join(c for c in nom_emp if c.isalnum() or c in ' -_')[:30]
                df_empresa.to_excel(writer, sheet_name=pestaña, index=False)
        
        print(f"✅ EXCEL ACTUALIZADO EN: {ruta_completa}")
        
    except Exception as e:
        print(f"❌ ERROR EXCEL: {e}")

# 4. RUTA PRINCIPAL (FORMULARIO)
@app.route('/')
def home():
    conn = sqlite3.connect('inspecciones.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM empresas ORDER BY nombre ASC')
    empresas = cursor.fetchall()
    conn.close()
    return render_template('index.html', empresas=empresas)

# 5. GUARDAR REPORTE DE FALLA
@app.route('/ruta_para_guardar', methods=['POST'])
def guardar():
    empresa = request.form.get('empresa')
    fecha = request.form.get('fecha')
    operador = request.form.get('operador')
    horometro = request.form.get('horometro')
    falla = request.form.get('falla')

    if not empresa or not fecha or not operador:
        flash("Error: Todos los campos obligatorios deben llenarse.", "error")
        return redirect(url_for('home'))

    conn = sqlite3.connect('inspecciones.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO registros (empresa, fecha, operador, horometro, falla) 
        VALUES (?, ?, ?, ?, ?)
    ''', (empresa, fecha, operador, horometro, falla))
    
    nro_reporte = cursor.lastrowid 
    conn.commit()
    conn.close()

    enviar_notificacion(empresa, operador, falla, nro_reporte)
    actualizar_excel()

    flash(f"{nro_reporte}", "success_report")
    return redirect(url_for('home'))

# 6. RUTA PARA REGISTRAR EMPRESA
@app.route('/registrar_empresa', methods=['GET', 'POST'])
def registrar_empresa():
    if request.method == 'POST':
        rif = request.form.get('rif')
        nombre = request.form.get('nombre')
        contacto = request.form.get('contacto')
        telefono = request.form.get('telefono')
        direccion = request.form.get('direccion')

        if not nombre:
            flash("El nombre de la empresa es obligatorio.", "error")
            return redirect(url_for('registrar_empresa'))

        conn = sqlite3.connect('inspecciones.db')
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO empresas (rif, nombre, contacto, telefono, direccion)
                VALUES (?, ?, ?, ?, ?)
            ''', (rif, nombre, contacto, telefono, direccion))
            conn.commit()
            flash("✅ Empresa registrada con éxito.", "success")
        except sqlite3.IntegrityError:
            flash("❌ El RIF ya existe en el sistema.", "error")
        except Exception as e:
            flash(f"❌ Error al guardar: {e}", "error")
        finally:
            conn.close()

        return redirect(url_for('registrar_empresa'))

    return render_template('registrar_empresa.html')

# 7. PANEL ADMINISTRATIVO Y REPORTES
@app.route('/admin')
def login_admin():
    return '''
        <div style="max-width: 350px; margin: 80px auto; font-family: Arial, sans-serif; padding: 20px; border: 1px solid #ccc; border-radius: 8px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <h2 style="color: #333;">Inversiones Barama</h2>
            <p style="color: #666; font-size: 14px;">Ingrese la contraseña administrativa</p>
            <form action="/ver_reportes" method="POST">
                <input type="password" name="clave" placeholder="Contraseña" required style="width: 90%; padding: 10px; margin-bottom: 15px; border: 1px solid #ccc; border-radius: 4px;">
                <br>
                <button type="submit" style="background-color: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; width: 95%; font-weight: bold;">Ingresar al Panel</button>
            </form>
            <br>
            <a href="/" style="color: #666; text-decoration: none; font-size: 12px;">← Volver al formulario</a>
        </div>
    '''

@app.route('/ver_reportes', methods=['GET', 'POST'])
def ver_reportes():
    CLAVE_ADMIN = "barama2026"

    if request.method == 'POST':
        clave_ingresada = request.form.get('clave')
        if clave_ingresada != CLAVE_ADMIN:
            return '''
                <div style="text-align: center; margin-top: 50px; font-family: Arial;">
                    <h3 style="color: red;">❌ Clave incorrecta. Acceso denegado.</h3>
                    <a href="/admin">Volver a intentar</a>
                </div>
            '''

    busqueda = request.args.get('busqueda', '')
    conn = sqlite3.connect('inspecciones.db')
    conn.row_factory = sqlite3.Row 
    cursor = conn.cursor()
    if busqueda:
        cursor.execute('SELECT * FROM registros WHERE empresa LIKE ? ORDER BY id DESC', ('%' + busqueda + '%',))
    else:
        cursor.execute('SELECT * FROM registros ORDER BY id DESC')
    reportes = cursor.fetchall()
    conn.close()
    
    return render_template('reportes.html', lista=reportes, busqueda=busqueda)

# 8. CAMBIAR ESTATUS Y ELIMINAR
@app.route('/actualizar_estatus/<int:id>/<string:nuevo_estatus>')
def actualizar_estatus(id, nuevo_estatus):
    conn = sqlite3.connect('inspecciones.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE registros SET estatus = ? WHERE id = ?', (nuevo_estatus, id))
    conn.commit()
    conn.close()
    
    actualizar_excel()
    return redirect(url_for('ver_reportes'))

@app.route('/eliminar_uno/<int:id>')
def eliminar_uno(id):
    conn = sqlite3.connect('inspecciones.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM registros WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('ver_reportes'))

@app.route('/eliminar_masivo', methods=['POST'])
def eliminar_masivo():
    ids_a_borrar = request.form.getlist('registro_id')
    if ids_a_borrar:
        conn = sqlite3.connect('inspecciones.db')
        cursor = conn.cursor()
        for id_reg in ids_a_borrar:
            cursor.execute('DELETE FROM registros WHERE id = ?', (id_reg,))
        conn.commit()
        conn.close()
    return redirect(url_for('ver_reportes'))

# 9. INICIALIZACIÓN DE LA BASE DE DATOS
def init_db():
    conn = sqlite3.connect('inspecciones.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS registros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa TEXT,
            fecha TEXT,
            operador TEXT,
            horometro REAL,
            falla TEXT,
            estatus TEXT DEFAULT 'Pendiente'
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS empresas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rif TEXT UNIQUE,
            nombre TEXT NOT NULL,
            contacto TEXT,
            telefono TEXT,
            direccion TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
