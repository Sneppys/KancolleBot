from PIL import Image, ImageDraw, ImageFont
import io

CARD_SIZE = (500, 500)

def generate_ship_card(ship_instance):
    img = Image.new(size=CARD_SIZE, mode="RGB", color=(0, 0, 0))

    draw = ImageDraw.Draw(img)
    draw.ellipse((0, 0, 500, 500), fill=(255, 0, 0))

    font = ImageFont.truetype("arial.ttf", 50)
    draw.text((200, 100), "Fuck", fill=(0, 0, 0), font=font)
    draw.text((200, 300), "Python", fill=(0, 0, 0), font=font)

    r = io.BytesIO(b'')
    img.save(r, format="PNG")
    return r
