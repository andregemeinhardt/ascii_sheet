import unicodedata, json, html.entities, os
from PIL import Image, ImageDraw, ImageFont

# CP1252 mappings
char_to_cp1252 = {}
cp1252_to_char = {}
for b in range(256):
    try:
        ch = bytes([b]).decode('cp1252')
        code_str = f"0{b:03d}" if b < 1000 else str(b)
        char_to_cp1252[ch] = code_str
        cp1252_to_char[code_str] = ch
    except:
        pass

# DOS CP437 mapping
dos_cp437_controls = {
    1: '☺', 2: '☻', 3: '♥', 4: '♦', 5: '♣', 6: '♠', 7: '•', 8: '◘',
    9: '○', 10: '◙', 11: '♂', 12: '♀', 13: '♪', 14: '♫', 15: '☼',
    16: '►', 17: '◄', 18: '↕', 19: '‼', 20: '¶', 21: '§', 22: '▬',
    23: '↨', 24: '↑', 25: '↓', 26: '→', 27: '←', 28: '∟', 29: '↔',
    30: '▲', 31: '▼', 127: '⌂'
}

char_to_cp437 = {}
for b in range(256):
    if b in dos_cp437_controls:
        ch = dos_cp437_controls[b]
    else:
        try:
            ch = bytes([b]).decode('cp437')
        except:
            ch = None
    if ch:
        char_to_cp437[ch] = str(b)

ascii_ctrl_info = {
    0: ('NUL', 'Null char'), 1: ('SOH', 'Start of Heading'), 2: ('STX', 'Start of Text'),
    3: ('ETX', 'End of Text'), 4: ('EOT', 'End of Transmission'), 5: ('ENQ', 'Enquiry'),
    6: ('ACK', 'Acknowledge'), 7: ('BEL', 'Bell / Beep'), 8: ('BS', 'Backspace'),
    9: ('TAB', 'Horizontal Tab'), 10: ('LF', 'Line Feed / Newline'), 11: ('VT', 'Vertical Tab'),
    12: ('FF', 'Form Feed / Page Break'), 13: ('CR', 'Carriage Return'), 14: ('SO', 'Shift Out'),
    15: ('SI', 'Shift In'), 16: ('DLE', 'Data Link Escape'), 17: ('DC1', 'Device Control 1'),
    18: ('DC2', 'Device Control 2'), 19: ('DC3', 'Device Control 3'), 20: ('DC4', 'Device Control 4'),
    21: ('NAK', 'Negative Acknowledge'), 22: ('SYN', 'Synchronous Idle'), 23: ('ETB', 'End of Transmission Block'),
    24: ('CAN', 'Cancel'), 25: ('EM', 'End of Medium'), 26: ('SUB', 'Substitute'),
    27: ('ESC', 'Escape'), 28: ('FS', 'File Separator'), 29: ('GS', 'Group Separator'),
    30: ('RS', 'Record Separator'), 31: ('US', 'Unit Separator'), 32: ('SPC', 'Space'),
    127: ('DEL', 'Delete')
}

curated_aliases = {
    '±': 'plus minus, plus-minus, plusminus, +-, pm, add subtract, sign',
    '‰': 'permille, per mille, promille, per thousand, pro mille, permil, 0137, thousandth',
    '‱': 'per ten thousand, basis point, ten thousandth',
    'µ': 'mu, greek mu, micro, micron, micro sign, 0181, 230',
    'μ': 'mu, greek small letter mu, micro, 956',
    'Μ': 'capital mu, greek capital letter mu',
    '€': 'euro, eur, currency euro, money, 0128, 8364',
    '£': 'pound, gbp, sterling, pound sign, 0163, 156',
    '¥': 'yen, jpy, yuan, cny, 0165, 157',
    '¢': 'cent, cents, currency, 0162, 155',
    '¤': 'currency sign, money',
    '°': 'degree, degrees, deg, temperature, celsius, fahrenheit, 0176, 248',
    '©': 'copyright, copr, (c), 0169',
    '®': 'registered, trademark registered, (r), 0174',
    '™': 'trademark, trade mark, tm, (tm), 0153, 8482',
    '•': 'bullet, dot, bullet point, 0149, 7',
    '·': 'middle dot, interpunct, centered dot, 0183, 250',
    '…': 'ellipsis, dots, three dots, 0133, 8230',
    '–': 'en dash, endash, short dash, 0150, 8211',
    '—': 'em dash, emdash, long dash, 0151, 8212',
    '“': 'left double quote, opening double quote, 0147, 8220',
    '”': 'right double quote, closing double quote, 0148, 8221',
    '‘': 'left single quote, opening single quote, 0145, 8216',
    '’': 'right single quote, apostrophe, 0146, 8217',
    '«': 'left guillemet, double angle quote, 0171, 174',
    '»': 'right guillemet, double angle quote, 0187, 175',
    '‹': 'single left pointing angle quote, 0139',
    '›': 'single right pointing angle quote, 0155',
    '÷': 'division, divide, div, obelus, 0247, 246',
    '×': 'multiplication, multiply, times, cross, 0215, 158',
    '√': 'square root, sqrt, radical, 251, 8730',
    '∞': 'infinity, infinite, lemniscate, forever, 8734, 236',
    '≈': 'almost equal, approx, approximately, 247, 8776',
    '≠': 'not equal, unequal, !=, 8800',
    '≡': 'identical to, equivalent, congruent, 240, 8801',
    '≤': 'less than or equal, <=, le, 243, 8804',
    '≥': 'greater than or equal, >=, ge, 242, 8805',
    '∑': 'sum, summation, sigma, 228, 8721',
    '∏': 'product, capital pi, 8719',
    'π': 'pi, greek small letter pi, 227, 960',
    'Π': 'capital pi, greek capital letter pi, 928',
    'Ω': 'omega, ohm, greek capital letter omega, 234, 937',
    'ω': 'small omega, greek small letter omega, 969',
    'α': 'alpha, greek small letter alpha, 224, 945',
    'β': 'beta, greek small letter beta, 225, 946',
    'γ': 'gamma, greek small letter gamma, 947',
    'Γ': 'capital gamma, greek capital letter gamma, 226, 915',
    'δ': 'delta, greek small letter delta, 235, 948',
    'Δ': 'capital delta, triangle, difference, laplace, 916',
    'ε': 'epsilon, greek small letter epsilon, 238, 949',
    'θ': 'theta, greek small letter theta, 233, 952',
    'Θ': 'capital theta, greek capital letter theta, 232, 920',
    'λ': 'lambda, greek small letter lambda, 955',
    'Λ': 'capital lambda, greek capital letter lambda, 923',
    'σ': 'sigma, greek small letter sigma, 229, 963',
    'Σ': 'capital sigma, sum, greek capital letter sigma, 228, 931',
    'τ': 'tau, greek small letter tau, 231, 964',
    'φ': 'phi, greek small letter phi, 237, 966',
    'Φ': 'capital phi, greek capital letter phi, 232, 934',
    'ψ': 'psi, greek small letter psi, 968',
    'Ψ': 'capital psi, greek capital letter psi, 936',
    '♥': 'heart, love, heart suit, 3, 9829',
    '♡': 'white heart, heart outline, 9825',
    '♦': 'diamond, diamond suit, 4, 9830',
    '♢': 'white diamond, diamond outline, 9826',
    '♣': 'club, club suit, 5, 9827',
    '♧': 'white club, club outline, 9824',
    '♠': 'spade, spade suit, 6, 9824',
    '♤': 'white spade, spade outline, 9828',
    '★': 'star, black star, favorite, 9733',
    '☆': 'star, white star, empty star, outline star, 9734',
    '☺': 'smiley, smile, happy, face, white smiling face, 1, 9786',
    '☻': 'black smiley, happy face, 2, 9787',
    '☹': 'frowning face, sad, unhappy, 9785',
    '☼': 'sun, sun with rays, sunny, 15, 9788',
    '☽': 'crescent moon, moon, 9789',
    '☾': 'crescent moon, moon, 9790',
    '♀': 'female, woman, venus, gender, 12, 9792',
    '♂': 'male, man, mars, gender, 11, 9794',
    '♪': 'eighth note, music, musical note, sound, 13, 9834',
    '♫': 'beamed eighth notes, music, song, audio, 14, 9835',
    '♬': 'beamed sixteenth notes, music, 9836',
    '✓': 'check, tick, check mark, correct, yes, 10003',
    '✔': 'heavy check mark, tick, check, ok, 10004',
    '✗': 'ballot x, cross, wrong, no, cancel, 10007',
    '✘': 'heavy ballot x, cross, fail, 10008',
    '→': 'right arrow, arrow right, east, 26, 8594',
    '←': 'left arrow, arrow left, west, 27, 8592',
    '↑': 'up arrow, arrow up, north, 24, 8593',
    '↓': 'down arrow, arrow down, south, 25, 8595',
    '↔': 'left right arrow, horizontal arrow, 29, 8596',
    '↕': 'up down arrow, vertical arrow, 18, 8597',
    '↖': 'north west arrow, up left arrow, 8598',
    '↗': 'north east arrow, up right arrow, 8599',
    '↘': 'south east arrow, down right arrow, 8600',
    '↙': 'south west arrow, down left arrow, 8601',
    '▲': 'up triangle, black up-pointing triangle, 30, 9650',
    '▼': 'down triangle, black down-pointing triangle, 31, 9660',
    '►': 'right pointer, play, black right-pointing pointer, 16, 9658',
    '◄': 'left pointer, reverse, black left-pointing pointer, 17, 9668',
    '■': 'black square, square, 254, 9632',
    '□': 'white square, square outline, 9633',
    '○': 'white circle, circle outline, 9, 9675',
    '●': 'black circle, bullet, filled circle, 9679',
    '½': 'half, one half, 1/2, fraction, 0189, 171',
    '¼': 'one quarter, fourth, 1/4, fraction, 0188, 172',
    '¾': 'three quarters, 3/4, fraction, 0190',
    '⅓': 'one third, 1/3, fraction, 8531',
    '⅔': 'two thirds, 2/3, fraction, 8532',
    '⅛': 'one eighth, 1/8, fraction, 8539',
    '⅜': 'three eighths, 3/8, fraction, 8540',
    '⅝': 'five eighths, 5/8, fraction, 8541',
    '⅞': 'seven eighths, 7/8, fraction, 8542',
    '¹': 'superscript 1, power of 1, 0185',
    '²': 'superscript 2, squared, power of 2, 0178, 253',
    '³': 'superscript 3, cubed, power of 3, 0179, 252',
    '⁰': 'superscript 0, 8304',
    '⁴': 'superscript 4, 8308',
    '⁵': 'superscript 5, 8309',
    '§': 'section, section sign, paragraph, legal, 0167, 21',
    '¶': 'pilcrow, paragraph sign, paragraph break, 0182, 20',
    '¿': 'inverted question mark, spanish question mark, 0191, 168',
    '¡': 'inverted exclamation mark, spanish exclamation mark, 0161, 173',
    '℃': 'celsius, degree celsius, centigrade, temperature, 8451',
    '℉': 'fahrenheit, degree fahrenheit, temperature, 8457',
    '№': 'numero sign, number sign, 8470',
    '℠': 'service mark, sm, 8480',
    '℅': 'care of, 8453',
    '℮': 'estimated symbol, e-mark, 8494',
    '⌂': 'house, home, 127',
    '░': 'light shade, shading, block, 176, 9617',
    '▒': 'medium shade, shading, block, 177, 9618',
    '▓': 'dark shade, shading, block, 178, 9619',
    '█': 'full block, solid block, rectangle, 219, 9608',
    '▄': 'lower half block, 220, 9604',
    '▀': 'upper half block, 223, 9600',
    '▌': 'left half block, 9612',
    '▐': 'right half block, 9616',
    '─': 'horizontal line, box drawing, 196, 9472',
    '│': 'vertical line, box drawing, 179, 9474',
    '┌': 'box top left, corner, 218, 9484',
    '┐': 'box top right, corner, 191, 9488',
    '└': 'box bottom left, corner, 192, 9492',
    '┘': 'box bottom right, corner, 217, 9496',
    '├': 'box vertical right, tee, 195, 9500',
    '┤': 'box vertical left, tee, 180, 9508',
    '┬': 'box down horizontal, tee, 194, 9516',
    '┴': 'box up horizontal, tee, 193, 9524',
    '┼': 'box cross, plus, intersection, 197, 9532',
    '═': 'double horizontal, 205, 9552',
    '║': 'double vertical, 186, 9553',
    '╔': 'double top left, 201, 9554',
    '╗': 'double top right, 187, 9557',
    '╚': 'double bottom left, 200, 9562',
    '╝': 'double bottom right, 188, 9565'
}

def get_category(code, name):
    if code < 32 or code == 127:
        return 'Control'
    if 32 <= code <= 126:
        return 'ASCII'
    if 128 <= code <= 255:
        return 'Latin-1'
    if 0x0370 <= code <= 0x03FF or 0x1F00 <= code <= 0x1FFF:
        return 'Greek'
    if 0x0400 <= code <= 0x04FF:
        return 'Cyrillic'
    if 0x2000 <= code <= 0x206F:
        return 'Punctuation'
    if 0x2070 <= code <= 0x209F:
        return 'Super/Sub'
    if 0x20A0 <= code <= 0x20CF:
        return 'Currency'
    if 0x2100 <= code <= 0x214F:
        return 'Letterlike'
    if 0x2150 <= code <= 0x218F:
        return 'Numbers'
    if 0x2190 <= code <= 0x21FF or 0x27F0 <= code <= 0x27FF or 0x2900 <= code <= 0x297F:
        return 'Arrows'
    if 0x2200 <= code <= 0x22FF:
        return 'Math'
    if 0x2300 <= code <= 0x23FF:
        return 'Technical'
    if 0x2500 <= code <= 0x257F:
        return 'Box Drawing'
    if 0x2580 <= code <= 0x259F:
        return 'Block Elements'
    if 0x25A0 <= code <= 0x25FF:
        return 'Geometric Shapes'
    if 0x2600 <= code <= 0x26FF:
        return 'Symbols'
    if 0x2700 <= code <= 0x27BF:
        return 'Dingbats'
    
    n = name.upper()
    if any(k in n for k in ['CURRENCY', 'DOLLAR', 'EURO', 'POUND', 'CENT', 'YEN', 'PESO', 'FRANC', 'LIRA', 'RUBLE', 'WON']):
        return 'Currency'
    if any(k in n for k in ['MATHEMATICAL', 'PLUS', 'MINUS', 'EQUAL', 'ROOT', 'SUM', 'INTEGRAL', 'DIVID', 'MULTIPL', 'ANGLE', 'INFINITY']):
        return 'Math'
    if 'ARROW' in n:
        return 'Arrows'
    if 'GREEK' in n:
        return 'Greek'
    if 'CYRILLIC' in n:
        return 'Cyrillic'
    if any(k in n for k in ['HEART', 'STAR', 'SMILE', 'SUN', 'MOON', 'NOTE', 'MUSIC', 'CHECK', 'BALLOT', 'CROSS', 'SYMBOL']):
        return 'Symbols'
    return 'Other'

records = []
for i in range(10000):
    ch = chr(i)
    name = unicodedata.name(ch, '')
    cat_code = unicodedata.category(ch)
    
    display_glyph = ch
    is_ctrl = False
    ctrl_badge = ""
    notes = ""
    
    if i in ascii_ctrl_info:
        is_ctrl = True
        ctrl_badge = ascii_ctrl_info[i][0]
        if i in dos_cp437_controls:
            display_glyph = dos_cp437_controls[i]
        else:
            display_glyph = ctrl_badge
        if not name:
            name = f"{ascii_ctrl_info[i][0]} ({ascii_ctrl_info[i][1]})"
    elif 128 <= i <= 159:
        # C1 Control or Windows-1252 character
        is_ctrl = True
        try:
            cp_ch = bytes([i]).decode('cp1252')
            display_glyph = cp_ch
            cp_name = unicodedata.name(cp_ch, '')
            name = f"Win-1252 [{cp_ch}]: {cp_name or 'Control'}"
            notes = f"Alt 0{i:03d} in Windows"
        except:
            name = f"C1 Control U+{i:04X}"
    elif not name:
        name = f"U+{i:04X}"
    
    category = get_category(i, name)
    
    # Alt codes
    alt_ansi = ""
    alt_oem = ""
    alt_dec = str(i)
    
    # 1. Check ANSI (CP1252)
    if ch in char_to_cp1252:
        alt_ansi = char_to_cp1252[ch]
    elif display_glyph in char_to_cp1252:
        alt_ansi = char_to_cp1252[display_glyph]
    elif i < 256:
        alt_ansi = f"0{i:03d}"
        
    # 2. Check OEM (CP437)
    if ch in char_to_cp437:
        alt_oem = char_to_cp437[ch]
    elif display_glyph in char_to_cp437:
        alt_oem = char_to_cp437[display_glyph]
        
    # 3. Special famous Alt-code overrides to ensure 100% accuracy:
    if i == 177: # ±
        alt_ansi = "0177"
        alt_oem = "241"
    elif i == 8240: # ‰
        alt_ansi = "0137"
        alt_oem = ""
    elif i == 181: # µ
        alt_ansi = "0181"
        alt_oem = "230"
    elif i == 956: # μ (Greek small mu)
        alt_ansi = ""
        alt_oem = ""
    elif i == 8364: # €
        alt_ansi = "0128"
    elif i == 169: # ©
        alt_ansi = "0169"
    elif i == 174: # ®
        alt_ansi = "0174"
    elif i == 8482: # ™
        alt_ansi = "0153"
    elif i == 176: # °
        alt_ansi = "0176"
        alt_oem = "248"
    elif i == 9829: # ♥
        alt_oem = "3"
    elif i == 9786: # ☺
        alt_oem = "1"
    elif i == 8594: # →
        alt_oem = "26"
    elif i == 8734: # ∞
        alt_oem = "236"
    elif i == 8730: # √
        alt_oem = "251"
    elif i == 247: # ÷
        alt_ansi = "0247"
        alt_oem = "246"
    elif i == 215: # ×
        alt_ansi = "0215"
        alt_oem = "158"
        
    # Primary & Secondary display string for Alt key
    primary_alt = ""
    secondary_alt = ""
    
    if i < 32 and alt_oem:
        # DOS/CP437 control graphic symbols: Alt + 1, Alt + 3, Alt + 15
        primary_alt = f"Alt + {alt_oem}"
        if i >= 1:
            secondary_alt = f"Alt + 0{i:03d}"
    elif i == 177: # ±
        primary_alt = "Alt + 0177"
        secondary_alt = "Alt + 241 (or Alt + 177)"
    elif i == 8240: # ‰
        primary_alt = "Alt + 0137"
        secondary_alt = "Alt + 8240"
    elif i == 181: # µ (Micro)
        primary_alt = "Alt + 0181"
        secondary_alt = "Alt + 230 (or Alt + 181)"
    elif i == 956: # μ (Greek mu)
        primary_alt = "Alt + 956"
        secondary_alt = "Alt + 0181 (Micro sign)"
    elif i == 8364: # €
        primary_alt = "Alt + 0128"
        secondary_alt = "Alt + 8364"
    elif i == 176: # °
        primary_alt = "Alt + 0176"
        secondary_alt = "Alt + 248"
    elif i == 169: # ©
        primary_alt = "Alt + 0169"
        secondary_alt = "Alt + 169"
    elif i == 8482: # ™
        primary_alt = "Alt + 0153"
        secondary_alt = "Alt + 8482"
    elif i == 9829: # ♥
        primary_alt = "Alt + 3"
        secondary_alt = "Alt + 9829"
    elif i == 8734: # ∞
        primary_alt = "Alt + 8734"
        secondary_alt = "Alt + 236"
    elif i == 8730: # √
        primary_alt = "Alt + 8730"
        secondary_alt = "Alt + 251"
    elif i == 247: # ÷
        primary_alt = "Alt + 0247"
        secondary_alt = "Alt + 246"
    elif i == 215: # ×
        primary_alt = "Alt + 0215"
        secondary_alt = "Alt + 158"
    elif 32 <= i <= 126:
        primary_alt = f"Alt + {i}"
        secondary_alt = f"Alt + 0{i:03d}"
    elif alt_ansi and i < 256:
        primary_alt = f"Alt + {alt_ansi}"
        if alt_oem and alt_oem != str(i):
            secondary_alt = f"Alt + {alt_oem}"
        else:
            secondary_alt = f"Alt + {i}"
    elif alt_ansi and i >= 256:
        primary_alt = f"Alt + {alt_ansi}"
        secondary_alt = f"Alt + {i}"
    elif alt_oem:
        primary_alt = f"Alt + {alt_oem}"
        if str(i) != alt_oem:
            secondary_alt = f"Alt + {i}"
    else:
        primary_alt = f"Alt + {i}"
        
    # Extra aliases for search
    alias_list = []
    if ch in curated_aliases:
        alias_list.extend([x.strip() for x in curated_aliases[ch].split(',')])
    if display_glyph in curated_aliases and display_glyph != ch:
        alias_list.extend([x.strip() for x in curated_aliases[display_glyph].split(',')])
        
    html_ent = html.entities.codepoint2name.get(i, "")
    if html_ent:
        alias_list.append(html_ent)
        alias_list.append(f"&{html_ent};")
        
    alias_str = " ".join(dict.fromkeys(alias_list))
    
    # Store record
    # [code, display_glyph, name, category, alt_ansi, alt_oem, primary_alt, secondary_alt, html_ent, alias_str, is_ctrl, ctrl_badge]
    records.append([
        i,
        display_glyph,
        name,
        category,
        alt_ansi,
        alt_oem,
        primary_alt,
        secondary_alt,
        html_ent,
        alias_str,
        1 if is_ctrl else 0,
        ctrl_badge
    ])

# Save JS dataset
js_content = "window.ASCII_DATA = " + json.dumps(records, separators=(',', ':')) + ";"
with open("ascii_data.js", "w", encoding="utf-8") as f:
    f.write(js_content)
print(f"ascii_data.js created: {len(js_content.encode('utf-8')) / 1024:.1f} KB, 10,000 records.")

# Generate icons
os.makedirs("icons", exist_ok=True)

# Generate high quality SVG icon
svg_icon = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0f172a" />
      <stop offset="100%" stop-color="#020617" />
    </linearGradient>
    <linearGradient id="primary" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#38bdf8" />
      <stop offset="100%" stop-color="#6366f1" />
    </linearGradient>
    <linearGradient id="accent" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#f43f5e" />
      <stop offset="100%" stop-color="#fb923c" />
    </linearGradient>
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="16" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>
  </defs>
  <!-- Background -->
  <rect width="512" height="512" rx="112" fill="url(#bg)" />
  <rect x="8" y="8" width="496" height="496" rx="104" fill="none" stroke="#1e293b" stroke-width="4" />
  
  <!-- Keycap base: Alt Key -->
  <g transform="translate(64, 80)">
    <!-- Keyboard key frame -->
    <rect x="0" y="0" width="168" height="110" rx="20" fill="#1e293b" stroke="#334155" stroke-width="3" />
    <rect x="6" y="6" width="156" height="88" rx="16" fill="#0f172a" />
    <text x="84" y="62" font-family="system-ui, -apple-system, sans-serif" font-weight="800" font-size="34" fill="#94a3b8" text-anchor="middle">ALT</text>
  </g>
  
  <!-- Plus Symbol -->
  <text x="264" y="152" font-family="system-ui, -apple-system, sans-serif" font-weight="900" font-size="44" fill="#64748b" text-anchor="middle">+</text>

  <!-- Number Keycap: 0177 -->
  <g transform="translate(304, 80)">
    <rect x="0" y="0" width="144" height="110" rx="20" fill="#1e293b" stroke="#334155" stroke-width="3" />
    <rect x="6" y="6" width="132" height="88" rx="16" fill="#0f172a" />
    <text x="72" y="62" font-family="monospace, Courier" font-weight="800" font-size="30" fill="#38bdf8" text-anchor="middle">0177</text>
  </g>

  <!-- Giant Glowing Symbol in center: ± -->
  <g filter="url(#glow)">
    <text x="256" y="380" font-family="system-ui, -apple-system, sans-serif" font-weight="900" font-size="180" fill="url(#primary)" text-anchor="middle">±</text>
  </g>

  <!-- Small accent symbols around -->
  <text x="96" y="440" font-family="system-ui, sans-serif" font-weight="bold" font-size="52" fill="#818cf8" text-anchor="middle">‰</text>
  <text x="416" y="440" font-family="system-ui, sans-serif" font-weight="bold" font-size="52" fill="#f43f5e" text-anchor="middle">µ</text>
  <text x="96" y="270" font-family="system-ui, sans-serif" font-weight="bold" font-size="44" fill="#34d399" text-anchor="middle">∞</text>
  <text x="416" y="270" font-family="system-ui, sans-serif" font-weight="bold" font-size="44" fill="#fbbf24" text-anchor="middle">€</text>
</svg>'''

with open("icons/icon.svg", "w", encoding="utf-8") as f:
    f.write(svg_icon)

# Generate PNG icons using Pillow
def create_png_icon(size, filename):
    img = Image.new("RGBA", (size, size), (15, 23, 42, 255))
    draw = ImageDraw.Draw(img)
    
    # Rounded corners
    r = int(size * 0.22)
    # Border
    draw.rounded_rectangle([2, 2, size - 3, size - 3], radius=r, outline=(51, 65, 85, 255), width=max(2, size // 100))
    
    # Header badges (ALT + 0177)
    # Scale coordinates
    s = size / 512.0
    
    # Alt button
    alt_box = [int(64 * s), int(70 * s), int(220 * s), int(170 * s)]
    draw.rounded_rectangle(alt_box, radius=int(14 * s), fill=(30, 41, 59, 255), outline=(71, 85, 105, 255), width=max(1, int(3 * s)))
    
    # 0177 button
    num_box = [int(290 * s), int(70 * s), int(448 * s), int(170 * s)]
    draw.rounded_rectangle(num_box, radius=int(14 * s), fill=(30, 41, 59, 255), outline=(56, 189, 248, 255), width=max(1, int(3 * s)))
    
    # Draw simple text using default font or drawn shapes
    # Let's draw the symbols nicely
    # Central ± symbol:
    # Horizontal line
    cx = size // 2
    cy = int(size * 0.62)
    bar_w = int(size * 0.44)
    bar_h = max(4, int(size * 0.05))
    
    # Plus vertical
    draw.rectangle([cx - bar_h // 2, cy - bar_w // 2, cx + bar_h // 2, cy + bar_w // 2 - int(size * 0.08)], fill=(56, 189, 248, 255))
    # Plus horizontal
    draw.rectangle([cx - bar_w // 2, cy - int(size * 0.04), cx + bar_w // 2, cy - int(size * 0.04) + bar_h], fill=(56, 189, 248, 255))
    # Minus horizontal
    draw.rectangle([cx - bar_w // 2, cy + int(size * 0.15), cx + bar_w // 2, cy + int(size * 0.15) + bar_h], fill=(99, 102, 241, 255))
    
    # Accent dots (permille style dots)
    d_r = max(3, int(size * 0.04))
    draw.ellipse([int(size * 0.2) - d_r, int(size * 0.45) - d_r, int(size * 0.2) + d_r, int(size * 0.45) + d_r], fill=(129, 140, 248, 255))
    draw.ellipse([int(size * 0.8) - d_r, int(size * 0.78) - d_r, int(size * 0.8) + d_r, int(size * 0.78) + d_r], fill=(244, 63, 94, 255))
    draw.ellipse([int(size * 0.8) - d_r, int(size * 0.45) - d_r, int(size * 0.8) + d_r, int(size * 0.45) + d_r], fill=(52, 211, 153, 255))

    img.save(filename)
    print(f"Created {filename} ({size}x{size})")

create_png_icon(192, "icons/icon-192.png")
create_png_icon(512, "icons/icon-512.png")
create_png_icon(180, "icons/apple-touch-icon.png")
create_png_icon(64, "icons/favicon.png")
print("Icons generated successfully.")
