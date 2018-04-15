from PIL import Image, ImageDraw, ImageFont
import io
import sqlite3
import os
import base64
import ship_stats
import userinfo

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
DB_PATH = os.path.join(DIR_PATH, "../kantaidb.db") # hidden to git

def get_connection():
    return sqlite3.connect(DB_PATH)

def get_image_from_db(shipid, colname):
    query = "SELECT %s FROM ShipBase WHERE ShipID=?;" % (colname)
    args = (shipid,)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query, args)
    img_enc = cur.fetchone()[0]
    cur.close()
    conn.commit()

    dec = base64.b64decode(img_enc)
    buf = io.BytesIO(dec)
    img = Image.open(buf).convert('RGBA')
    return img

INVENTORY_SIZE = (800, 400)
INV_SLOTS = (7, 12)
LOWER_PADDING = 40

def generate_inventory_screen(member, page):
    discord_id = member.id
    user = userinfo.get_user(discord_id)
    inv = userinfo.get_user_inventory(discord_id)
    w, h = INVENTORY_SIZE
    sx, sy = INV_SLOTS
    cw = int(w / sx)
    ch = int(h / sy)
    h += LOWER_PADDING

    ships_per_page = sx * sy
    pages_needed = (len(inv.inventory) // ships_per_page) + (0 if len(inv.inventory) % ships_per_page == 0 and len(inv.inventory) > 0 else 1)
    if (page < 1):
        page = 1
    elif (page > pages_needed):
        page = pages_needed

    img = Image.new(size=(w, h), mode="RGB", color=(255, 255, 255))

    draw = ImageDraw.Draw(img)
    shade = False
    indx = 0
    indx += (ships_per_page * (page - 1))
    for xi in range(sx):
        for yi in range(sy):
            ship = inv.inventory[indx] if indx < len(inv.inventory) else None

            x, y = (xi * cw, yi * ch)
            if (shade):
                draw.rectangle((x, y, x + cw, y + ch), fill=(200, 200, 200) if ship else (50, 50, 50))
            elif (not ship):
                draw.rectangle((x, y, x + cw, y + ch), fill=(75, 75, 75))
            if (ship):
                base = ship.base()
                font = ImageFont.truetype("trebucbd.ttf", ch * 5 // 8)
                num_str = "%04d" % (ship.invid) # TODO make ship id
                draw_squish_text(img, (x + cw // 8, y + ch // 2), num_str, font, cw // 4 - 4, color=(0, 0, 0))

                font = ImageFont.truetype("trebucbd.ttf", ch * 3 // 4)
                lvl_str = "L%02d %s" % (ship.level, ship_stats.get_ship_type(base.shiptype).discriminator)
                draw_squish_text(img, (x + 2 + cw * 3 // 4, y + ch // 2), lvl_str, font, cw // 2 - 4, color=(0, 0, 0))

                cir_start_x = x + cw // 4
                cir_start_y = y + 2
                use_damaged = False # TODO check if use damaged image
                ico = get_image_from_db(base.sid, "Image_Small_Damaged" if use_damaged else "Image_Small")
                ico = ico.resize((ch - 4, ch - 4), Image.BILINEAR)
                border_color = ship_stats.RARITY_COLORS[base.rarity - 1]
                draw.ellipse((cir_start_x - 1, cir_start_y - 1, cir_start_x + ch - 3, cir_start_y + ch - 3), fill=border_color)
                img.paste(ico, (cir_start_x, cir_start_y), mask=ico)
            shade = not shade
            indx += 1
        if(sy % 2 == 0):
            shade = not shade

    draw = ImageDraw.Draw(img)
    x, y = (0, INVENTORY_SIZE[1]) # start position of footer
    fw, fh = (w, LOWER_PADDING) # size of footer

    display_name = "%s#%s" % (member.name, member.discriminator)
    font = ImageFont.truetype("framd.ttf", fh * 3 // 4)
    draw.text((x + 10, y + fh // 8), "%s's Ships" % display_name, font=font, fill=(0, 0, 0))

    font = ImageFont.truetype("framdit.ttf", fh // 2)
    pg_txt = "Page %s of %s" % (page, pages_needed)
    pgw, pgh = draw.textsize(pg_txt, font=font)
    pgx, pgy = (fw - pgw - 2, y + fh - pgh - 2)
    draw.text((pgx, pgy), pg_txt, font=font, fill=(50, 50, 50))

    font = ImageFont.truetype("trebucbd.ttf", fh * 3 // 8)
    rsc_x, rsc_y = (fw * 11 // 16, y + 1)

    txt_fuel = "%05d" % (user.fuel)
    txt_ammo = "%05d" % (user.ammo)
    txt_steel = "%05d" % (user.steel)
    txt_bauxite = "%05d" % (user.bauxite)
    txt_ships= "%03d / %03d" % (len(inv.inventory), user.shipslots)

    txt_w, txt_h = draw.textsize(txt_fuel, font)

    ico_size = (fh * 3 // 8 + 2, fh * 3 // 8 + 2)
    ico_fuel = Image.open(DIR_PATH + '/icons/fuel.png').resize(ico_size, Image.LINEAR)
    ico_ammo = Image.open(DIR_PATH + '/icons/ammo.png').resize(ico_size, Image.LINEAR)
    ico_steel = Image.open(DIR_PATH + '/icons/steel.png').resize(ico_size, Image.LINEAR)
    ico_bauxite = Image.open(DIR_PATH + '/icons/bauxite.png').resize(ico_size, Image.LINEAR)
    ico_ships = Image.open(DIR_PATH + '/icons/ship.png').resize(ico_size, Image.LINEAR)

    x_off = ico_size[0] + txt_w + 6
    y_off = ico_size[1] + 2
    toff_x, toff_y = (ico_size[0] + 2, (ico_size[1] - txt_h) // 2)

    draw.text((rsc_x + toff_x, rsc_y + toff_y), txt_fuel, font=font, fill=(0, 0, 0))
    draw.text((rsc_x + toff_x, rsc_y + toff_y + y_off), txt_ammo, font=font, fill=(0, 0, 0))
    draw.text((rsc_x + toff_x + x_off, rsc_y + toff_y), txt_steel, font=font, fill=(0, 0, 0))
    draw.text((rsc_x + toff_x + x_off, rsc_y + toff_y + y_off), txt_bauxite, font=font, fill=(0, 0, 0))
    draw.text((rsc_x + toff_x + x_off * 2, rsc_y + toff_y), txt_ships, font=font, fill=(0, 0, 0))

    img.paste(ico_fuel, (rsc_x, rsc_y), mask=ico_fuel)
    img.paste(ico_ammo, (rsc_x, rsc_y + y_off), mask=ico_fuel)
    img.paste(ico_steel, (rsc_x + x_off, rsc_y), mask=ico_fuel)
    img.paste(ico_bauxite, (rsc_x + x_off, rsc_y + y_off), mask=ico_fuel)
    img.paste(ico_ships, (rsc_x + x_off * 2, rsc_y), mask=ico_ships)

    r = io.BytesIO()
    img.save(r, format="PNG")
    return r


CARD_SIZE = (800, 500)

def generate_ship_card(bot, ship_instance):
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
    draw_squish_text(img, (550, 220), base.name, font, 490, color=(0, 0, 0), outline=(125, 125, 125))
    draw_squish_text(img, (550, 300), "Level %s | %s" % (ship_instance.level,
        ship_stats.get_ship_type(base.shiptype).full_name), font_small, 490, color=(0, 0, 0), outline=(125, 125, 125))

    font = ImageFont.truetype("framdit.ttf", 35)

    display_name="Unknown User"
    for g in bot.guilds:
        owner = g.get_member(ship_instance.owner)
        if (owner):
            display_name = "%s#%s" % (owner.name, owner.discriminator)
            break
    draw_squish_text(img, (550, 450), "Part of %s's fleet" % (display_name), font, 490, color=(25, 25, 25), outline=(175, 175, 175))

    r = io.BytesIO(b'')
    img.save(r, format="PNG")
    return r


def draw_squish_text(img, position, text, font, max_width, color=(255, 255, 255), outline=None, center_height=True, repeat=1):
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
    if (outline):
        for i in range(repeat * 3):
            draw.text((x-1, y-1), text, font=font, fill=outline)
            draw.text((x+1, y-1), text, font=font, fill=outline)
            draw.text((x-1, y-1), text, font=font, fill=outline)
            draw.text((x+1, y+1), text, font=font, fill=outline)
    for i in range(repeat):
        draw.text((x, y), text, font=font, fill=fill)
