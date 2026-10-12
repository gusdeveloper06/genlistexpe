from datetime import datetime
import os
from flask import Flask, render_template, request, send_file
import requests
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Spacer, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = '7995801304:AAG1wN2JHuLvSsbk592wh9woO-0wh9oslis'
TELEGRAM_CHAT_ID = '6995615162'
UPLOAD_FOLDER = './uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Banners en tono Esmeralda Profundo / Lima
def draw_header_footer(canvas, doc):
    canvas.saveState()
    
    # BANNER SUPERIOR (Verde Esmeralda muy oscuro)
    canvas.setFillColor(colors.HexColor('#022c22'))
    canvas.rect(0, letter[1] - 80, letter[0], 80, fill=1, stroke=0)
    
    # Logo / Título
    canvas.setFont("Helvetica-Bold", 26)
    canvas.setFillColor(colors.white)
    canvas.drawString(40, letter[1] - 47, "NOVALINK")
    
    canvas.setFillColor(colors.HexColor('#a3e635')) # Lima 400
    canvas.drawString(178, letter[1] - 47, "V5")
    
    canvas.setFont("Helvetica-Bold", 9)
    canvas.setFillColor(colors.HexColor('#34d399')) # Esmeralda 400
    canvas.drawString(40, letter[1] - 65, "SISTEMA INTEGRAL DE CONTROL DE ENTREGAS")
    
    # BANNER INFERIOR
    canvas.setFillColor(colors.HexColor('#022c22'))
    canvas.rect(0, 0, letter[0], 40, fill=1, stroke=0)
    
    canvas.setFillColor(colors.HexColor('#a3e635'))
    canvas.setFont("Helvetica-Bold", 10)
    canvas.drawString(40, 16, "Generado por NOVALINK V5 | Powered by SOFTLEN")
    
    canvas.restoreState()


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generar', methods=['POST'])
def generar():
    ajustador = request.form.get('ajustador', '').strip().upper()
    companias = request.form.getlist('compania[]')
    siniestros = request.form.getlist('siniestro[]')
    observaciones = request.form.getlist('observaciones[]')

    filas_validas = []
    for i in range(len(siniestros)):
        comp = companias[i].strip() if i < len(companias) else ""
        sin = siniestros[i].strip() if i < len(siniestros) else ""
        obs = observaciones[i].strip() if i < len(observaciones) else ""
        
        if comp or sin:
            filas_validas.append([str(len(filas_validas) + 1), comp.upper(), sin.upper(), obs.upper()])

    if not filas_validas:
        return "Error: Documento vacío.", 400

    fecha_actual = datetime.now().strftime('%d/%m/%Y a las %H:%M hrs')
    timestamp_file = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"NOVA_{ajustador.replace(' ', '_')}_{timestamp_file}.pdf"
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    doc = SimpleDocTemplate(
        filepath, 
        pagesize=letter, 
        rightMargin=40, 
        leftMargin=40, 
        topMargin=110,  
        bottomMargin=60
    )
    
    elementos = []
    styles = getSampleStyleSheet()
    
    # Datos del Ajustador
    info_style = ParagraphStyle('InfoStyle', parent=styles['Normal'], fontSize=11, leading=16, fontName='Helvetica-Bold', textColor=colors.HexColor('#064e3b'))
    elementos.append(Paragraph(f"AJUSTADOR RESPONSABLE: <font color='#15803d'>{ajustador}</font>", info_style))
    elementos.append(Paragraph(f"FECHA DE EMISIÓN: {fecha_actual}", info_style))
    elementos.append(Spacer(1, 20))

    # Tabla
    data_tabla = [["#", "COMPAÑÍA", "NÚMERO DE SINIESTRO", "OBSERVACIONES"]] + filas_validas

    tabla = Table(data_tabla, colWidths=[30, 140, 160, 200])
    tabla.setStyle(TableStyle([
        # Cabecera Verde Bosque
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#064e3b')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#ecfdf5')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'), 
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        
        # Cuerpo (Cebra con un tinte verdoso levísimo)
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#0f172a')),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        
        # Bordes
        ('LINEBELOW', (0, 0), (-1, 0), 3, colors.HexColor('#84cc16')), # Línea lima bajo la cabecera
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
    ]))

    elementos.append(tabla)

    doc.build(elementos, onFirstPage=draw_header_footer, onLaterPages=draw_header_footer)

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
        with open(filepath, 'rb') as pdf_file:
            requests.post(url, data={
                'chat_id': TELEGRAM_CHAT_ID,
                'caption': f"⚡ *NOVALINK V5* ⚡\n_Powered by SOFTLEN_\n\n👨‍💼 Ajustador: {ajustador}\n📑 Siniestros Procesados: {len(filas_validas)}",
                'parse_mode': 'Markdown'
            }, files={'document': pdf_file})
    except Exception as e:
        print(f"Error TG: {e}")

    return send_file(filepath, as_attachment=True, download_name=filename)

if __name__ == '__main__':
    app.run(debug=True, port=5000)