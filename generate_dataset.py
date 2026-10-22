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
    '∂': 'partial, partial differential, del, d, round d, diff, 8706, 2202',
    '∇': 'nabla, del, gradient, grad, 8711, 2207',
    '∫': 'integral, int, integrate, calculus, 8747, 222B',
    '∬': 'double integral, iint, 8748',
    '∭': 'triple integral, iiint, 8749',
    '∮': 'contour integral, oint, surface integral, 8750',
    '∀': 'for all, universal quantifier, forall, 8704',
    '∃': 'exists, there exists, existential quantifier, 8707',
    '∄': 'there does not exist, not exists, nexists, 8708',
    '∅': 'empty set, null set, emptyset, 8709',
    '∈': 'element of, in, belongs to, is in, 8712',
    '∉': 'not an element of, not in, notin, 8713',
    '∋': 'contains, ni, owns, 8715',
    '⊂': 'subset of, proper subset, subset, 8834',
    '⊃': 'superset of, proper superset, supset, 8835',
    '⊆': 'subset or equal, sub, subseteq, 8838',
    '⊇': 'superset or equal, supseteq, 8839',
    '∪': 'union, cup, 8746',
    '∩': 'intersection, cap, 8745',
    '∧': 'logical and, wedge, conjunction, 8743',
    '∨': 'logical or, vee, disjunction, 8744',
    '¬': 'logical not, negation, neg, 172',
    '∴': 'therefore, hence, so, 8756',
    '∵': 'because, since, 8757',
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

latex_map = {
    # ASCII / Latin-1 math & punctuation
    36: r'\$',
    37: r'\%',
    38: r'\&',
    92: r'\backslash',
    95: r'\_',
    123: r'\{',
    125: r'\}',
    126: r'\sim',
    161: r'\textexclamdown',
    163: r'\pounds',
    167: r'\S',
    169: r'\copyright',
    172: r'\neg',
    174: r'\textregistered',
    176: r'^\circ',
    177: r'\pm',
    178: r'^2',
    179: r'^3',
    181: r'\mu',
    182: r'\P',
    183: r'\cdot',
    185: r'^1',
    188: r'\frac{1}{4}',
    189: r'\frac{1}{2}',
    190: r'\frac{3}{4}',
    191: r'\textquestiondown',
    215: r'\times',
    247: r'\div',

    # Greek uppercase
    915: r'\Gamma',
    916: r'\Delta',
    920: r'\Theta',
    923: r'\Lambda',
    926: r'\Xi',
    928: r'\Pi',
    931: r'\Sigma',
    933: r'\Upsilon',
    934: r'\Phi',
    936: r'\Psi',
    937: r'\Omega',

    # Greek lowercase
    945: r'\alpha',
    946: r'\beta',
    947: r'\gamma',
    948: r'\delta',
    949: r'\epsilon',
    950: r'\zeta',
    951: r'\eta',
    952: r'\theta',
    953: r'\iota',
    954: r'\kappa',
    955: r'\lambda',
    956: r'\mu',
    957: r'\nu',
    958: r'\xi',
    960: r'\pi',
    961: r'\rho',
    962: r'\varsigma',
    963: r'\sigma',
    964: r'\tau',
    965: r'\upsilon',
    966: r'\phi',
    967: r'\chi',
    968: r'\psi',
    969: r'\omega',

    # Greek variants
    977: r'\vartheta',
    978: r'\Upsilon',
    981: r'\varphi',
    982: r'\varpi',
    1008: r'\varkappa',
    1009: r'\varrho',
    1013: r'\varepsilon',

    # General Punctuation & Letterlike
    8211: r'--',
    8212: r'---',
    8224: r'\dagger',
    8225: r'\ddagger',
    8226: r'\bullet',
    8230: r'\dots',
    8240: r'\textperthousand',
    8242: r'\prime',
    8450: r'\mathbb{C}',
    8459: r'\mathcal{H}',
    8461: r'\mathbb{H}',
    8463: r'\hbar',
    8465: r'\Im',
    8467: r'\ell',
    8469: r'\mathbb{N}',
    8472: r'\wp',
    8473: r'\mathbb{P}',
    8474: r'\mathbb{Q}',
    8476: r'\Re',
    8477: r'\mathbb{R}',
    8482: r'\texttrademark',
    8484: r'\mathbb{Z}',
    8501: r'\aleph',
    8502: r'\beth',
    8503: r'\gimel',
    8504: r'\daleth',
    8531: r'\frac{1}{3}',
    8532: r'\frac{2}{3}',
    8539: r'\frac{1}{8}',
    8540: r'\frac{3}{8}',
    8541: r'\frac{5}{8}',
    8542: r'\frac{7}{8}',

    # Arrows
    8592: r'\leftarrow',
    8593: r'\uparrow',
    8594: r'\rightarrow',
    8595: r'\downarrow',
    8596: r'\leftrightarrow',
    8597: r'\updownarrow',
    8598: r'\nwarrow',
    8599: r'\nearrow',
    8600: r'\searrow',
    8601: r'\swarrow',
    8602: r'\nleftarrow',
    8603: r'\nrightarrow',
    8604: r'\leftsquigarrow',
    8605: r'\rightsquigarrow',
    8606: r'\twoheadleftarrow',
    8608: r'\twoheadrightarrow',
    8610: r'\leftarrowtail',
    8611: r'\rightarrowtail',
    8612: r'\mapsto',
    8617: r'\hookleftarrow',
    8618: r'\hookrightarrow',
    8619: r'\looparrowleft',
    8620: r'\looparrowright',
    8624: r'\Lsh',
    8625: r'\Rsh',
    8636: r'\leftharpoonup',
    8637: r'\leftharpoondown',
    8638: r'\upharpoonright',
    8639: r'\upharpoonleft',
    8640: r'\rightharpoonup',
    8641: r'\rightharpoondown',
    8642: r'\downharpoonright',
    8643: r'\downharpoonleft',
    8644: r'\rightleftarrows',
    8646: r'\leftrightarrows',
    8647: r'\leftleftarrows',
    8648: r'\upuparrows',
    8649: r'\rightrightarrows',
    8650: r'\downdownarrows',
    8651: r'\leftrightharpoons',
    8652: r'\rightleftharpoons',
    8653: r'\nLeftarrow',
    8654: r'\nLeftrightarrow',
    8655: r'\nRightarrow',
    8656: r'\Leftarrow',
    8657: r'\Uparrow',
    8658: r'\Rightarrow',
    8659: r'\Downarrow',
    8660: r'\Leftrightarrow',
    8661: r'\Updownarrow',

    # Mathematical Operators & Relations (U+2200 to U+22FF)
    8704: r'\forall',
    8705: r'\complement',
    8706: r'\partial',
    8707: r'\exists',
    8708: r'\nexists',
    8709: r'\emptyset',
    8710: r'\Delta',
    8711: r'\nabla',
    8712: r'\in',
    8713: r'\notin',
    8715: r'\ni',
    8716: r'\not\ni',
    8718: r'\blacksquare',
    8719: r'\prod',
    8720: r'\coprod',
    8721: r'\sum',
    8722: r'-',
    8723: r'\mp',
    8724: r'\dotplus',
    8726: r'\setminus',
    8727: r'\ast',
    8728: r'\circ',
    8729: r'\bullet',
    8730: r'\sqrt',
    8731: r'\sqrt[3]',
    8732: r'\sqrt[4]',
    8733: r'\propto',
    8734: r'\infty',
    8736: r'\angle',
    8737: r'\measuredangle',
    8738: r'\sphericalangle',
    8739: r'\mid',
    8740: r'\nmid',
    8741: r'\parallel',
    8742: r'\nparallel',
    8743: r'\wedge',
    8744: r'\vee',
    8745: r'\cap',
    8746: r'\cup',
    8747: r'\int',
    8748: r'\iint',
    8749: r'\iiint',
    8750: r'\oint',
    8751: r'\oiint',
    8752: r'\oiiint',
    8756: r'\therefore',
    8757: r'\because',
    8758: r':',
    8759: r'\Colon',
    8764: r'\sim',
    8765: r'\backsim',
    8768: r'\wr',
    8769: r'\nsim',
    8770: r'\simeq',
    8771: r'\nsimeq',
    8772: r'\cong',
    8773: r'\approxeq',
    8774: r'\ncong',
    8776: r'\approx',
    8777: r'\napprox',
    8781: r'\asymp',
    8784: r'\doteq',
    8785: r'\doteqdot',
    8786: r'\fallingdotseq',
    8787: r'\risingdotseq',
    8796: r'\coloneqq',
    8800: r'\neq',
    8801: r'\equiv',
    8802: r'\nequiv',
    8804: r'\le',
    8805: r'\ge',
    8806: r'\leqq',
    8807: r'\geqq',
    8808: r'\lneqq',
    8809: r'\gneqq',
    8810: r'\ll',
    8811: r'\gg',
    8812: r'\between',
    8814: r'\nless',
    8815: r'\ngtr',
    8816: r'\nleq',
    8817: r'\ngeq',
    8818: r'\lesssim',
    8819: r'\gtrsim',
    8822: r'\lessgtr',
    8823: r'\gtrless',
    8826: r'\prec',
    8827: r'\succ',
    8828: r'\preccurlyeq',
    8829: r'\succcurlyeq',
    8830: r'\precsim',
    8831: r'\succsim',
    8832: r'\nprec',
    8833: r'\nsucc',
    8834: r'\subset',
    8835: r'\supset',
    8836: r'\nsubset',
    8837: r'\nsupset',
    8838: r'\subseteq',
    8839: r'\supseteq',
    8840: r'\nsubseteq',
    8841: r'\nsupseteq',
    8842: r'\subsetneq',
    8843: r'\supsetneq',
    8846: r'\uplus',
    8847: r'\sqsubset',
    8848: r'\sqsupset',
    8849: r'\sqsubseteq',
    8850: r'\sqsupseteq',
    8851: r'\sqcap',
    8852: r'\sqcup',
    8853: r'\oplus',
    8854: r'\ominus',
    8855: r'\otimes',
    8856: r'\oslash',
    8857: r'\odot',
    8858: r'\circledcirc',
    8859: r'\circledast',
    8861: r'\circleddash',
    8862: r'\boxplus',
    8863: r'\boxminus',
    8864: r'\boxtimes',
    8865: r'\boxdot',
    8866: r'\vdash',
    8867: r'\dashv',
    8868: r'\top',
    8869: r'\bot',
    8872: r'\models',
    8875: r'\Vdash',
    8876: r'\nvdash',
    8877: r'\nvDash',
    8878: r'\nVdash',
    8879: r'\nVDash',
    8882: r'\vartriangleleft',
    8883: r'\vartriangleright',
    8884: r'\trianglelefteq',
    8885: r'\trianglerighteq',
    8890: r'\intercal',
    8891: r'\veebar',
    8892: r'\barwedge',
    8896: r'\bigwedge',
    8897: r'\bigvee',
    8898: r'\bigcap',
    8899: r'\bigcup',
    8900: r'\diamond',
    8901: r'\cdot',
    8902: r'\star',
    8904: r'\bowtie',
    8905: r'\ltimes',
    8906: r'\rtimes',
    8907: r'\leftthreetimes',
    8908: r'\rightthreetimes',
    8910: r'\curlyvee',
    8911: r'\curlywedge',
    8912: r'\Subset',
    8913: r'\Supset',
    8914: r'\Cap',
    8915: r'\Cup',
    8920: r'\lll',
    8921: r'\ggg',
    8922: r'\lesseqgtr',
    8923: r'\gtreqless',
    8926: r'\curlyeqprec',
    8927: r'\curlyeqsucc',
    8928: r'\npreccurlyeq',
    8929: r'\nsucccurlyeq',
    8930: r'\ntrianglelefteq',
    8931: r'\ntrianglerighteq',
    8932: r'\ntriangleleft',
    8933: r'\ntriangleright',
    8942: r'\vdots',
    8943: r'\cdots',
    8944: r'\iddots',
    8945: r'\ddots',

    # Technical, brackets & Delimiters
    8968: r'\lceil',
    8969: r'\rceil',
    8970: r'\lfloor',
    8971: r'\rfloor',
    9001: r'\langle',
    9002: r'\rangle',

    # Shapes, Symbols & Dingbats
    9632: r'\blacksquare',
    9633: r'\square',
    9650: r'\blacktriangle',
    9651: r'\triangle',
    9660: r'\blacktriangledown',
    9661: r'\triangledown',
    9674: r'\lozenge',
    9675: r'\circ',
    9679: r'\bullet',
    9733: r'\bigstar',
    9734: r'\star',
    9792: r'\female',
    9794: r'\male',
    9824: r'\spadesuit',
    9825: r'\heartsuit',
    9826: r'\diamondsuit',
    9827: r'\clubsuit',
    9829: r'\heartsuit',
    9830: r'\diamondsuit',
    9837: r'\flat',
    9838: r'\natural',
    9839: r'\sharp',
    10003: r'\checkmark'
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
        
    latex_cmd = latex_map.get(i, "")
    if latex_cmd:
        alias_list.append(latex_cmd)
        clean_latex = latex_cmd.lstrip('\\').replace('{', '').replace('}', '').strip()
        if clean_latex:
            alias_list.append(clean_latex)

    alias_str = " ".join(dict.fromkeys(alias_list))
    
    # Store record
    # [code, display_glyph, name, category, alt_ansi, alt_oem, primary_alt, secondary_alt, html_ent, alias_str, is_ctrl, ctrl_badge, latex]
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
        ctrl_badge,
        latex_cmd
    ])

# Save JS dataset
js_content = "window.ASCII_DATA = " + json.dumps(records, separators=(',', ':')) + ";"
with open("ascii_data.js", "w", encoding="utf-8") as f:
    f.write(js_content)
print(f"ascii_data.js created: {len(js_content.encode('utf-8')) / 1024:.1f} KB, 10,000 records.")

# Generate icons
os.makedirs("icons", exist_ok=True)

# Generate high quality SVG icon (black background, ASCII on top, # underneath)
svg_icon = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <rect width="512" height="512" rx="96" fill="#000000" />
  <text x="256" y="205" font-family="system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'DejaVu Sans', sans-serif" font-weight="900" font-size="116" letter-spacing="4" fill="#ffffff" text-anchor="middle">ASCII</text>
  <text x="256" y="395" font-family="system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'DejaVu Sans', sans-serif" font-weight="900" font-size="230" fill="#ffffff" text-anchor="middle">#</text>
</svg>
'''

with open("icons/icon.svg", "w", encoding="utf-8") as f:
    f.write(svg_icon)

# Generate PNG icons using Pillow
font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def create_png_icon(size, filename, is_squircle=False):
    scale = 2
    canvas_size = size * scale
    img = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 255))
    draw = ImageDraw.Draw(img)
    
    s = canvas_size / 512.0
    f_ascii = ImageFont.truetype(font_path, int(116 * s))
    f_hash = ImageFont.truetype(font_path, int(230 * s))
    
    b_ascii = draw.textbbox((0, 0), "ASCII", font=f_ascii)
    w_ascii = b_ascii[2] - b_ascii[0]
    h_ascii = b_ascii[3] - b_ascii[1]

    b_hash = draw.textbbox((0, 0), "#", font=f_hash)
    w_hash = b_hash[2] - b_hash[0]
    h_hash = b_hash[3] - b_hash[1]

    gap = int(24 * s)
    total_h = h_ascii + gap + h_hash
    start_y = (canvas_size - total_h) // 2

    x_ascii = (canvas_size - w_ascii) // 2 - b_ascii[0]
    y_ascii = start_y - b_ascii[1]

    x_hash = (canvas_size - w_hash) // 2 - b_hash[0]
    y_hash = start_y + h_ascii + gap - b_hash[1]

    draw.text((x_ascii, y_ascii), "ASCII", font=f_ascii, fill=(255, 255, 255, 255))
    draw.text((x_hash, y_hash), "#", font=f_hash, fill=(255, 255, 255, 255))
    
    if is_squircle:
        mask = Image.new("L", (canvas_size, canvas_size), 0)
        mask_draw = ImageDraw.Draw(mask)
        r = int(canvas_size * 0.18)
        mask_draw.rounded_rectangle([0, 0, canvas_size - 1, canvas_size - 1], radius=r, fill=255)
        img.putalpha(mask)
    
    final_img = img.resize((size, size), Image.Resampling.LANCZOS)
    final_img.save(filename)
    print(f"Created {filename} ({size}x{size})")

create_png_icon(512, "icons/icon-512.png", is_squircle=False)
create_png_icon(192, "icons/icon-192.png", is_squircle=False)
create_png_icon(180, "icons/apple-touch-icon.png", is_squircle=False)
create_png_icon(64, "icons/favicon.png", is_squircle=True)
print("Icons generated successfully.")
