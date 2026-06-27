from dotenv import load_dotenv
load_dotenv()
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
import PyPDF2
import json, os, requests
import datetime
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = os.getenv("TELEGRAM_TOKEN")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DATOS_FILE = "/root/bitacora_bot/bitacora.json"


DOCS_DIR = "/root/bitacora_bot/documentos/"

def cargar_documentos():
    contexto = ""
    for archivo in os.listdir(DOCS_DIR):
        ruta = os.path.join(DOCS_DIR, archivo)
        if archivo.endswith(".txt"):
            try:
                with open(ruta, "r", encoding="utf-8") as f:
                    contexto += f"\n--- {archivo} ---\n{f.read()[:2000]}"
            except:
                pass
        elif archivo.endswith(".pdf"):
            try:
                with open(ruta, "rb") as f:
                    lector = PyPDF2.PdfReader(f)
                    for pag in lector.pages:
                        contexto += pag.extract_text() or ""
            except:
                pass
    return contexto[:6000]

def consultar_deepseek(tareas, api_key):
    contexto_legal = cargar_documentos()
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    prompt = f"Sos asistente para contratistas de vinas de Mendoza (Ley 23.154).\n\nCONTEXTO LEGAL:\n{contexto_legal}\n\nTAREAS:\n{tareas}\n\nOrganizá las tareas en:\n1. Tareas del contrato\n2. Tareas extra que paga el patron\n\nOrganizá por mes con fechas."
    r = requests.post(url, headers=headers, json={
        "model": "deepseek-v4-pro",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 3000
    }, timeout=60)
    if r.status_code == 200:
        return r.json()["choices"][0]["message"]["content"]
    return "Error al consultar DeepSeek"


def generar_pdf(user_id, registros, analisis, perfil={}):
    import re
    ruta_pdf = f"/tmp/bitacora_{user_id}_{datetime.now().strftime('%Y%m%d%H%M')}.pdf"
    doc = SimpleDocTemplate(ruta_pdf, pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    VERDE = colors.HexColor("#1a472a")
    VERDE_CLARO = colors.HexColor("#d8f3dc")
    GRIS = colors.HexColor("#37474f")
    ROJO = colors.HexColor("#b71c1c")
    titulo = ParagraphStyle("T", parent=styles["Title"], fontSize=18,
        textColor=colors.white, alignment=TA_CENTER, fontName="Helvetica-Bold")
    subtitulo = ParagraphStyle("S", parent=styles["Normal"], fontSize=11,
        textColor=colors.white, alignment=TA_CENTER)
    seccion = ParagraphStyle("Sec", parent=styles["Normal"], fontSize=12,
        textColor=VERDE, spaceBefore=12, spaceAfter=6, fontName="Helvetica-Bold")
    normal = ParagraphStyle("N", parent=styles["Normal"], fontSize=10,
        spaceAfter=4, leading=14, textColor=GRIS)
    item_s = ParagraphStyle("I", parent=styles["Normal"], fontSize=10,
        spaceAfter=3, leftIndent=10, leading=13, textColor=GRIS)
    verde_b = ParagraphStyle("VB", parent=styles["Normal"], fontSize=10,
        spaceAfter=3, leftIndent=10, textColor=VERDE, fontName="Helvetica-Bold")
    rojo_b = ParagraphStyle("RB", parent=styles["Normal"], fontSize=10,
        spaceAfter=3, leftIndent=10, textColor=ROJO, fontName="Helvetica-Bold")
    footer_s = ParagraphStyle("F", parent=styles["Normal"], fontSize=8,
        textColor=colors.grey, alignment=TA_CENTER)
    story = []
    fecha_hoy = datetime.now().strftime("%d/%m/%Y")
    enc = Table([
        [Paragraph("BITACORA DEL CONTRATISTA", titulo)],
        [Paragraph("Registro de Tareas - Ano Agricola | Ley 23.154", subtitulo)],
        [Paragraph(f"Generado: {fecha_hoy}", subtitulo)]
    ], colWidths=[17*cm])
    enc.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), VERDE),
        ("TOPPADDING", (0,0), (-1,-1), 14),
        ("BOTTOMPADDING", (0,0), (-1,-1), 14),
        ("LEFTPADDING", (0,0), (-1,-1), 10),
    ]))

    story.append(enc)
    story.append(Spacer(1, 0.3*cm))

    # Datos del contratista
    if perfil:
        datos_perfil = [
            [Paragraph("<b>Contratista:</b>", normal), Paragraph(perfil.get("nombre", "-"), normal)],
            [Paragraph("<b>DNI:</b>", normal), Paragraph(perfil.get("dni", "-"), normal)],
            [Paragraph("<b>Empleador:</b>", normal), Paragraph(perfil.get("empleador", "-"), normal)],
            [Paragraph("<b>CUIL empleador:</b>", normal), Paragraph(perfil.get("cuil_empleador", "-"), normal)],
            [Paragraph("<b>Direccion finca:</b>", normal), Paragraph(perfil.get("direccion", "-"), normal)],
            [Paragraph("<b>Hectareas:</b>", normal), Paragraph(perfil.get("hectareas", "-"), normal)],
            [Paragraph("<b>N INV:</b>", normal), Paragraph(perfil.get("inv", "-"), normal)],
        ]
        tabla_perfil = Table(datos_perfil, colWidths=[4*cm, 13*cm])
        tabla_perfil.setStyle(TableStyle([
            ("GRID", (0,0), (-1,-1), 0.3, colors.lightgrey),
            ("ROWBACKGROUNDS", (0,0), (-1,-1), [VERDE_CLARO, colors.white]),
            ("TOPPADDING", (0,0), (-1,-1), 4),
            ("BOTTOMPADDING", (0,0), (-1,-1), 4),
            ("LEFTPADDING", (0,0), (-1,-1), 8),
        ]))
        story.append(tabla_perfil)
        story.append(Spacer(1, 0.3*cm))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("REGISTRO DE TAREAS", seccion))
    story.append(HRFlowable(width="100%", thickness=2, color=VERDE, spaceAfter=6))
    filas = [[Paragraph("<b>Fecha</b>", normal), Paragraph("<b>Tarea Realizada</b>", normal)]]
    for r in sorted(registros, key=lambda x: x["fecha"]):
        filas.append([Paragraph(r["fecha"][:16], item_s), Paragraph(r["tarea"], item_s)])
    tabla = Table(filas, colWidths=[4*cm, 13*cm])
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), VERDE),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [VERDE_CLARO, colors.white]),
        ("GRID", (0,0), (-1,-1), 0.3, colors.lightgrey),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
    ]))
    story.append(tabla)
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("ANALISIS DEEPSEEK V4", seccion))
    story.append(HRFlowable(width="100%", thickness=2, color=VERDE, spaceAfter=6))
    for linea in analisis.split("\n"):
        linea = linea.strip()
        if not linea:
            story.append(Spacer(1, 0.2*cm))
            continue
        linea_limpia = re.sub(r"[#*_-]", "", linea).strip()
        if not linea_limpia:
            continue
        if any(x in linea.lower() for x in ["corresponde al contrato", "labor ordinaria", "incluida"]):
            story.append(Paragraph(f"OK {linea_limpia}", verde_b))
        elif any(x in linea.lower() for x in ["extra", "paga el patron", "no corresponde"]):
            story.append(Paragraph(f"EXTRA {linea_limpia}", rojo_b))
        else:
            story.append(Paragraph(linea_limpia, normal))
    story.append(Spacer(1, 1*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey, spaceAfter=4))
    story.append(Paragraph("Bot Bitacora Contratista | Ley 23.154 | DeepSeek V4", footer_s))
    doc.build(story)
    return ruta_pdf


PERFIL_FILE = "/root/bitacora_bot/perfiles.json"

PREGUNTAS_PERFIL = [
    ("nombre", "Nombre y apellido del contratista:"),
    ("dni", "DNI del contratista:"),
    ("empleador", "Nombre y apellido del empleador:"),
    ("cuil_empleador", "CUIL del empleador:"),
    ("direccion", "Direccion de la finca:"),
    ("hectareas", "Cantidad de hectareas del contrato:"),
    ("inv", "N INV de la finca (ej: E-16305):")
]

def cargar_perfiles():
    if os.path.exists(PERFIL_FILE):
        with open(PERFIL_FILE, "r") as f:
            return json.load(f)
    return {}

def guardar_perfiles(perfiles):
    with open(PERFIL_FILE, "w") as f:
        json.dump(perfiles, f, ensure_ascii=False, indent=2)

def cargar_datos():
    if os.path.exists(DATOS_FILE):
        with open(DATOS_FILE, "r") as f:
            return json.load(f)
    return {}

def guardar_datos(datos):
    with open(DATOS_FILE, "w") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📝 Registrar Tarea", callback_data="tarea")],
        [InlineKeyboardButton("📋 Ver Este Mes", callback_data="ver")],
        [InlineKeyboardButton("📄 Generar PDF", callback_data="pdf")],
        [InlineKeyboardButton("👤 Mi Perfil", callback_data="perfil")],
        [InlineKeyboardButton("❓ Ayuda", callback_data="ayuda")]
    ]
    await update.message.reply_text(
        "📒 *Bitácora del Contratista*\n\nRegistrá tus tareas diarias.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def registrar_tarea(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📝 Describí la tarea que realizaste hoy.\n"
        "Incluí: qué hiciste, en qué sector, si corresponde al contrato o es extra."
    )
    context.user_data["esperando_tarea"] = True

async def mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    texto = update.message.text

    if context.user_data.get("esperando_tarea"):
        datos = cargar_datos()
        if user_id not in datos:
            datos[user_id] = []
        
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
        datos[user_id].append({
            "fecha": fecha,
            "tarea": texto
        })
        guardar_datos(datos)
        context.user_data["esperando_tarea"] = False
        await update.message.reply_text(f"✅ Tarea registrada el {fecha}")
    else:
        await update.message.reply_text("Usá /tarea para registrar una tarea.")

async def ver(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    datos = cargar_datos()
    
    if user_id not in datos or not datos[user_id]:
        await update.message.reply_text("No hay registros todavía.")
        return
    
    mes_actual = datetime.now().strftime("%Y-%m")
    registros = [r for r in datos[user_id] if r["fecha"].startswith(mes_actual)]
    
    if not registros:
        await update.message.reply_text("No hay registros este mes.")
        return
    
    texto = f"📋 *Registros de {mes_actual}:*\n\n"
    for r in registros:
        texto += f"📅 {r['fecha']}\n{r['tarea']}\n\n"
    
    await update.message.reply_text(texto, parse_mode="Markdown")

async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📒 *Bitácora del Contratista*\n\n"
        "/tarea - Registrar tarea del día\n"
        "/ver - Ver registros del mes actual\n"
        "/pdf - Generar PDF ordenado por fecha\n\n"
        "Registrá cada tarea que hacés, especificando si es del contrato o extra.",
        parse_mode="Markdown"
    )


async def pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    datos = cargar_datos()
    if user_id not in datos or not datos[user_id]:
        await update.message.reply_text("No hay registros para generar PDF.")
        return
    await update.message.reply_text("Generando PDF con DeepSeek V4...")
    tareas_texto = "\n".join([f"{r['fecha']}: {r['tarea']}" for r in datos[user_id]])
    analisis = consultar_deepseek(tareas_texto, DEEPSEEK_API_KEY)
    ruta_pdf = generar_pdf(user_id, datos[user_id], analisis, cargar_perfiles().get(user_id, {}))
    with open(ruta_pdf, "rb") as f:
        await update.message.reply_document(f, filename="bitacora_contratista.pdf")
    os.unlink(ruta_pdf)


async def boton(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)

    if query.data == "tarea":
        await query.message.reply_text(
            "Describe la tarea que realizaste hoy.\nIncluye: que hiciste, en que sector, si es del contrato o extra."
        )
        context.user_data["esperando_tarea"] = True

    elif query.data == "ver":
        datos = cargar_datos()
        if user_id not in datos or not datos[user_id]:
            await query.message.reply_text("No hay registros todavia.")
            return
        mes_actual = datetime.now().strftime("%Y-%m")
        registros = [r for r in datos[user_id] if r["fecha"].startswith(mes_actual)]
        if not registros:
            await query.message.reply_text("No hay registros este mes.")
            return
        texto = f"Registros de {mes_actual}:\n\n"
        for r in registros:
            texto += f"{r['fecha']}\n{r['tarea']}\n\n"
        await query.message.reply_text(texto)

    elif query.data == "pdf":
        datos = cargar_datos()
        if user_id not in datos or not datos[user_id]:
            await query.message.reply_text("No hay registros para generar PDF.")
            return
        await query.message.reply_text("Generando PDF con DeepSeek V4...")
        tareas_texto = "\n".join([f"{r['fecha']}: {r['tarea']}" for r in datos[user_id]])
        analisis = consultar_deepseek(tareas_texto, DEEPSEEK_API_KEY)
        ruta_pdf = generar_pdf(user_id, datos[user_id], analisis, cargar_perfiles().get(user_id, {}))
        with open(ruta_pdf, "rb") as f:
            await query.message.reply_document(f, filename="bitacora.pdf")
        os.unlink(ruta_pdf)

    elif query.data == "perfil":
        perfiles = cargar_perfiles()
        if user_id in perfiles:
            p = perfiles[user_id]
            texto = (
                f"TUS DATOS:\n\n"
                f"Nombre: {p.get('nombre', '-')}\n"
                f"DNI: {p.get('dni', '-')}\n"
                f"Empleador: {p.get('empleador', '-')}\n"
                f"CUIL empleador: {p.get('cuil_empleador', '-')}\n"
                f"Direccion finca: {p.get('direccion', '-')}\n"
                f"Hectareas: {p.get('hectareas', '-')}\n"
                f"N INV: {p.get('inv', '-')}\n\n"
                f"Para actualizar manda /perfil"
            )
            await query.message.reply_text(texto)
        else:
            context.user_data["perfil_paso"] = 0
            context.user_data["perfil_temp"] = {}
            await query.message.reply_text(PREGUNTAS_PERFIL[0][1])

    elif query.data == "ayuda":
        await query.message.reply_text(
            "BITACORA DEL CONTRATISTA\n\n"
            "Registra Tarea: Describe que hiciste hoy\n"
            "Ver Este Mes: Ver todas las tareas del mes\n"
            "Generar PDF: PDF completo con analisis DeepSeek V4\n\n"
            "Podes registrar con fecha manual: 2026-04-30: texto de la tarea"
        )

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("tarea", registrar_tarea))
    app.add_handler(CommandHandler("ver", ver))
    app.add_handler(CommandHandler("ayuda", ayuda))
    app.add_handler(CommandHandler("pdf", pdf))
    app.add_handler(CallbackQueryHandler(boton))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mensaje))
    print("✅ Bitácora Bot iniciado")
    app.run_polling()

if __name__ == "__main__":
    main()
