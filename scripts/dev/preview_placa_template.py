from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas


OUTPUT_FILE = Path("outputs") / "preview_placas" / "placa_preview_template.pdf"

# Ferramenta oficial de preview visual do template OBRA_CAIO_SUM_V1.
# Ajustes visuais devem ser calibrados aqui antes de migração para app/main.py.


def cm_value(value: float) -> float:
    return value * cm


def draw_centered_text(
    c: canvas.Canvas,
    text: str,
    x_cm: float,
    y_cm: float,
    width_cm: float,
    font_name: str,
    font_size: int,
    color: colors.Color,
) -> None:
    text_width = c.stringWidth(text, font_name, font_size)
    text_object = c.beginText()
    text_object.setTextOrigin(
        cm_value(x_cm) + (cm_value(width_cm) - text_width) / 2,
        cm_value(y_cm),
    )
    text_object.setFont(font_name, font_size)
    text_object.setCharSpace(0)
    text_object.setFillColor(color)
    text_object.textLine(text)
    c.drawText(text_object)


def draw_sum_text(
    c: canvas.Canvas,
    text: str,
    x_cm: float,
    y_cm: float,
    width_cm: float,
    font_name: str,
    font_size: int,
    color: colors.Color,
) -> None:
    gap_su = -7.0
    gap_um = -9.0
    letter_widths = [c.stringWidth(letter, font_name, font_size) for letter in text]
    text_width = sum(letter_widths) + gap_su + gap_um
    x_position = cm_value(x_cm) + (cm_value(width_cm) - text_width) / 2
    y_position = cm_value(y_cm)

    c.setFont(font_name, font_size)
    c.setFillColor(color)
    for index, letter in enumerate(text):
        c.drawString(x_position, y_position, letter)
        x_position += letter_widths[index]
        if index == 0:
            x_position += gap_su
        elif index == 1:
            x_position += gap_um


def gerar_preview() -> Path:
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    largura = cm_value(21.0)
    altura = cm_value(29.7)

    azul_petroleo = colors.HexColor("#005A64")
    amarelo_atencao = colors.HexColor("#F2C230")
    branco = colors.HexColor("#FFFFFF")
    preto = colors.HexColor("#000000")

    c = canvas.Canvas(str(OUTPUT_FILE), pagesize=(largura, altura))
    c.setTitle("Preview local de template de placa")

    c.setFillColor(azul_petroleo)
    c.rect(0, 0, largura, altura, fill=1, stroke=0)

    # Cabeçalho fixo para calibração visual.
    c.setFillColor(azul_petroleo)
    c.rect(0, cm_value(24.2), largura, cm_value(5.5), fill=1, stroke=0)

    triangulo_x = cm_value(1.2)
    triangulo_y = cm_value(25.55)
    triangulo_largura = cm_value(3.0)
    triangulo_altura = cm_value(3.0)

    path = c.beginPath()
    path.moveTo(triangulo_x + triangulo_largura / 2, triangulo_y + triangulo_altura)
    path.lineTo(triangulo_x, triangulo_y)
    path.lineTo(triangulo_x + triangulo_largura, triangulo_y)
    path.close()
    c.setFillColor(amarelo_atencao)
    c.setStrokeColor(branco)
    c.setLineWidth(1.5)
    c.drawPath(path, fill=1, stroke=1)

    c.setFillColor(preto)
    c.setFont("Helvetica-Bold", 32)
    c.drawCentredString(
        triangulo_x + triangulo_largura / 2,
        triangulo_y + cm_value(0.72),
        "!",
    )

    c.setFillColor(branco)
    c.setFont("Helvetica-Bold", 50)
    separador_x = cm_value(13.95)
    cabecalho_texto = "ATENÇÃO"
    cabecalho_x_inicial = triangulo_x + triangulo_largura + cm_value(0.35)
    cabecalho_x_final = separador_x - cm_value(0.35)
    cabecalho_largura = cabecalho_x_final - cabecalho_x_inicial
    cabecalho_texto_largura = c.stringWidth(cabecalho_texto, "Helvetica-Bold", 50)
    c.drawString(
        cabecalho_x_inicial + (cabecalho_largura - cabecalho_texto_largura) / 2,
        cm_value(26.05),
        cabecalho_texto,
    )

    c.setFillColor(branco)
    c.rect(separador_x, cm_value(25.45), cm_value(0.05), cm_value(3.15), fill=1, stroke=0)

    draw_sum_text(
        c,
        text="SUM",
        x_cm=14.65,
        y_cm=26.08,
        width_cm=4.6,
        font_name="Helvetica",
        font_size=46,
        color=branco,
    )

    corpo_x_cm = 1.0
    corpo_largura_cm = 19.0

    c.setFillColor(branco)
    c.rect(cm_value(corpo_x_cm), cm_value(1.8), cm_value(corpo_largura_cm), cm_value(22.4), fill=1, stroke=0)

    c.setFillColor(azul_petroleo)
    c.circle(cm_value(10.5), cm_value(14.3), cm_value(7.3), fill=1, stroke=0)

    c.setFillColor(branco)
    c.setFont("Helvetica-Bold", 95)
    c.drawCentredString(cm_value(10.5), cm_value(13.22), "!")

    draw_centered_text(
        c,
        text="Obrigatório uso de EPI",
        x_cm=corpo_x_cm,
        y_cm=4.75,
        width_cm=corpo_largura_cm,
        font_name="Helvetica-Bold",
        font_size=34,
        color=azul_petroleo,
    )

    draw_centered_text(
        c,
        text="Use capacete, bota e colete nesta área.",
        x_cm=corpo_x_cm,
        y_cm=3.45,
        width_cm=corpo_largura_cm,
        font_name="Helvetica",
        font_size=18,
        color=preto,
    )

    c.showPage()
    c.save()

    return OUTPUT_FILE


def main() -> None:
    arquivo_pdf = gerar_preview()
    print(f"PDF gerado: {arquivo_pdf}")


if __name__ == "__main__":
    main()
