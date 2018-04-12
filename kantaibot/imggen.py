from PIL import Image, ImageDraw, ImageFont
import io
import sqlite3
import os
import base64
import ship_stats

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
DB_PATH = os.path.join(DIR_PATH, "../kantaidb.db") # hidden to git

def get_connection():
    return sqlite3.connect(DB_PATH)

def get_image_from_db(shipid, colname):
    query = "SELECT %s FROM ShipBase WHERE ShipID='%s';" % (colname, shipid)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query)
    img_enc = cur.fetchall()[0][0]
    cur.close()
    conn.commit()

    dec = base64.b64decode(img_enc)
    buf = io.BytesIO(dec)
    img = Image.open(buf).convert('RGBA')
    return img

CARD_SIZE = (800, 500)

def generate_ship_card(ship_instance):
    img = Image.new(size=CARD_SIZE, mode="RGB", color=(0, 0, 0))

    base = ship_instance.base()

    backdrop = ship_stats.get_rarity_backdrop(base.rarity, CARD_SIZE)
    img.paste(backdrop)

    use_damaged = False # TODO make this check if ship is damaged

    img_full = get_image_from_db(ship_instance.sid, "Image_Damaged" if use_damaged else "Image_Default")
    img_small = get_image_from_db(ship_instance.sid, "Image_Small_Damaged" if use_damaged else "Image_Small")

    draw = ImageDraw.Draw(img)

    img_w, img_h = img_full.size
    targ_width = int(500 * (img_w / img_h))
    x_offset = int(200 - (targ_width / 2))
    img_full = img_full.resize((targ_width, 500), Image.BICUBIC)
    img_small = img_small.resize((80, 80), Image.LINEAR)
    img.paste(img_full, (x_offset, 0), mask=img_full)
    img.paste(img_small, (710, 10), mask=img_small)

    font = ImageFont.truetype("impact.ttf", 70)
    font_small = ImageFont.truetype("framd.ttf", 40)
    draw_squish_text(img, (550, 220), base.name, font, 490, color=(0, 0, 0))
    draw_squish_text(img, (550, 300), "Level %s | %s" % (ship_instance.level,
        ship_stats.get_ship_type(base.shiptype).full_name), font_small, 490, color=(0, 0, 0))

    r = io.BytesIO(b'')
    img.save(r, format="PNG")
    return r


def draw_squish_text(img, position, text, font, max_width, color=(255, 255, 255), outline=(255, 255, 255), center_height=True, repeat=1):
    draw = ImageDraw.Draw(img)
    w, h = draw.textsize(text, font=font)
    text_img = Image.new(size=(w, h), color=(0, 0, 0, 0), mode="RGBA")
    tdraw = ImageDraw.Draw(text_img)
    draw_outline(tdraw, (0, 0), text, font, color, outline, repeat)
    if (max_width < w):
        text_img = text_img.resize((max_width, h), Image.BILINEAR)
    w, h = text_img.size
    paste_x = int(position[0] - (w / 2))
    if center_height:
        paste_y = int(position[1] - (h / 2))
    else:
        paste_y = position[1]
    img.paste(text_img, (paste_x, paste_y), mask=text_img)
    del draw


def draw_centered_text(draw, position, text, font, color=(255, 255, 255), outline=(255, 255, 255),
                       center_height=True, repeat=1):
    w, h = draw.textsize(text, font=font)
    x, y = position
    if (center_height):
        start_loc = (x - w / 2, y - h / 2)
    else:
        start_loc = (x - w / 2, y)
    draw_outline(draw, start_loc, text, font, color, outline, repeat)


def draw_outline(draw, position, text, font, fill, outline, repeat):
    x, y = position
    for i in range(repeat * 3):
        draw.text((x-1, y-1), text, font=font, fill=outline)
        draw.text((x+1, y-1), text, font=font, fill=outline)
        draw.text((x-1, y-1), text, font=font, fill=outline)
        draw.text((x+1, y+1), text, font=font, fill=outline)
    for i in range(repeat):
        draw.text((x, y), text, font=font, fill=fill)
