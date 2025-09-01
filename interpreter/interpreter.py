#!/usr/bin/env python3
# Kavun Interpreter - updated (string-protected translations, Turkish booleans, temizle)
import re, sys, ast, traceback, os, random, math, json, time, datetime
import colorama
from colorama import Fore, Back, Style
import threading

# --- Exceptions for control flow ---
class BreakLoop(Exception): pass   # used by 'kır'
class ContinueLoop(Exception): pass  # used by 'devam'
class ReturnFunction(Exception):      # used by 'dön <expr>' or 'dön'
    def __init__(self, value):
        self.value = value

# --- Runtime state ---
env = [{}]               # stack of variable frames; env[0] is global
functions = {}           # user-defined functions: name -> (params, body_lines)
expr_cache = {}          # cache compiled expressions
call_trace = []          # simple call trace for error messages

# --- Built-in functions ---
def builtin_rastgele(min_val=1, max_val=100):
    """Rastgele sayı üret"""
    return random.randint(min_val, max_val)

def builtin_ondalık_rastgele():
    """0 ile 1 arasında ondalık rastgele sayı"""
    return random.random()

def builtin_karekök(sayi):
    """Sayının karekökünü al"""
    return math.sqrt(sayi)

def builtin_kuvvet(taban, us):
    """Tabanın üssünü al"""
    return math.pow(taban, us)

def builtin_mutlak(sayi):
    """Sayının mutlak değerini al"""
    return abs(sayi)

def builtin_yuvarla(sayi, basamak=0):
    """Sayıyı yuvarla"""
    return round(sayi, basamak)

def builtin_sin(sayi):
    """Sinüs değerini hesapla"""
    return math.sin(sayi)

def builtin_cos(sayi):
    """Kosinüs değerini hesapla"""
    return math.cos(sayi)

def builtin_tan(sayi):
    """Tanjant değerini hesapla"""
    return math.tan(sayi)

def builtin_log(sayi):
    """Doğal logaritma"""
    return math.log(sayi)

def builtin_log10(sayi):
    """10 tabanında logaritma"""
    return math.log10(sayi)

def builtin_bekle(saniye):
    """Belirtilen saniye kadar bekle"""
    time.sleep(saniye)

def builtin_şimdi():
    """Şu anki zamanı döndür"""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def builtin_tarih():
    """Bugünün tarihini döndür"""
    return datetime.datetime.now().strftime("%d/%m/%Y")

def builtin_saat():
    """Şu anki saati döndür"""
    return datetime.datetime.now().strftime("%H:%M:%S")

def builtin_liste_oluştur(*elemanlar):
    """Yeni liste oluştur"""
    return list(elemanlar)

def builtin_liste_ekle(liste, eleman):
    """Listeye eleman ekle"""
    if not isinstance(liste, list):
        raise RuntimeError("İlk parametre liste olmalı")
    liste.append(eleman)
    return liste

def builtin_liste_uzunluk(liste):
    """Listenin uzunluğunu döndür"""
    if not isinstance(liste, list):
        raise RuntimeError("Parametre liste olmalı")
    return len(liste)

def builtin_liste_eleman(liste, index):
    """Listenin belirtilen indeksindeki elemanı döndür"""
    if not isinstance(liste, list):
        raise RuntimeError("İlk parametre liste olmalı")
    if index < 0 or index >= len(liste):
        raise RuntimeError("Geçersiz indeks")
    return liste[index]

def builtin_liste_sil(liste, index):
    """Listeden belirtilen indeksteki elemanı sil"""
    if not isinstance(liste, list):
        raise RuntimeError("İlk parametre liste olmalı")
    if index < 0 or index >= len(liste):
        raise RuntimeError("Geçersiz indeks")
    return liste.pop(index)

def builtin_metin_uzunluk(metin):
    """Metnin uzunluğunu döndür"""
    return len(str(metin))

def builtin_metin_kes(metin, baslangic, bitis=None):
    """Metni kes"""
    metin = str(metin)
    if bitis is None:
        return metin[baslangic:]
    return metin[baslangic:bitis]

def builtin_metin_bul(metin, aranan):
    """Metinde arama yap, bulunursa indeks döndür"""
    metin = str(metin)
    aranan = str(aranan)
    try:
        return metin.index(aranan)
    except ValueError:
        return -1

def builtin_metin_degistir(metin, eski, yeni):
    """Metindeki eski kısmı yeni ile değiştir"""
    return str(metin).replace(str(eski), str(yeni))

def builtin_büyük_harf(metin):
    """Metni büyük harfe çevir"""
    return str(metin).upper()

def builtin_küçük_harf(metin):
    """Metni küçük harfe çevir"""
    return str(metin).lower()

def builtin_dosya_oku(dosya_adi):
    """Dosyayı oku"""
    try:
        with open(dosya_adi, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        raise RuntimeError(f"Dosya bulunamadı: {dosya_adi}")
    except Exception as e:
        raise RuntimeError(f"Dosya okuma hatası: {e}")

def builtin_dosya_yaz(dosya_adi, icerik):
    """Dosyaya yaz"""
    try:
        with open(dosya_adi, 'w', encoding='utf-8') as f:
            f.write(str(icerik))
        return True
    except Exception as e:
        raise RuntimeError(f"Dosya yazma hatası: {e}")

def builtin_dosya_ekle(dosya_adi, icerik):
    """Dosyaya ekle"""
    try:
        with open(dosya_adi, 'a', encoding='utf-8') as f:
            f.write(str(icerik))
        return True
    except Exception as e:
        raise RuntimeError(f"Dosya ekleme hatası: {e}")

def builtin_dosya_var_mi(dosya_adi):
    """Dosyanın var olup olmadığını kontrol et"""
    return os.path.exists(dosya_adi)

def builtin_dosya_sil(dosya_adi):
    """Dosyayı sil"""
    try:
        os.remove(dosya_adi)
        return True
    except FileNotFoundError:
        return False
    except Exception as e:
        raise RuntimeError(f"Dosya silme hatası: {e}")

def builtin_klasor_oluştur(klasor_adi):
    """Klasör oluştur"""
    try:
        os.makedirs(klasor_adi, exist_ok=True)
        return True
    except Exception as e:
        raise RuntimeError(f"Klasör oluşturma hatası: {e}")

def builtin_klasor_listesi(klasor_adi="."):
    """Klasördeki dosyaları listele"""
    try:
        return os.listdir(klasor_adi)
    except Exception as e:
        raise RuntimeError(f"Klasör listesi alma hatası: {e}")

# Initialize colorama for cross-platform colored output
colorama.init()

# Animation state
animation_running = False
animation_thread = None

# --- New Built-in Functions ---

def builtin_kırmızı_yaz(metin):
    """Metni kırmızı renkte yazdır"""
    print(Fore.RED + str(metin) + Style.RESET_ALL)

def builtin_yesil_yaz(metin):
    """Metni yeşil renkte yazdır"""
    print(Fore.GREEN + str(metin) + Style.RESET_ALL)

def builtin_sarı_yaz(metin):
    """Metni sarı renkte yazdır"""
    print(Fore.YELLOW + str(metin) + Style.RESET_ALL)

def builtin_mavi_yaz(metin):
    """Metni mavi renkte yazdır"""
    print(Fore.BLUE + str(metin) + Style.RESET_ALL)

def builtin_mor_yaz(metin):
    """Metni mor renkte yazdır"""
    print(Fore.MAGENTA + str(metin) + Style.RESET_ALL)

def builtin_turkuaz_yaz(metin):
    """Metni turkuaz renkte yazdır"""
    print(Fore.turkuaz + str(metin) + Style.RESET_ALL)

def builtin_animasyonlu_yaz(metin):
    """Metni animasyonlu olarak yazdır"""
    global animation_running
    animation_running = True
    
    def animate():
        global animation_running
        chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        i = 0
        while animation_running:
            print(f"\r{chars[i % len(chars)]} {metin}", end="", flush=True)
            time.sleep(0.1)
            i += 1
        print()  # New line when done
    
    animation_thread = threading.Thread(target=animate)
    animation_thread.start()

def builtin_animasyon_durdur():
    """Animasyonu durdur"""
    global animation_running
    animation_running = False
    if animation_thread:
        animation_thread.join()

def builtin_üçgen_çiz(boyut):
    """ASCII üçgen çiz"""
    for i in range(boyut):
        print(" " * (boyut - i - 1) + "*" * (2 * i + 1))

def builtin_kare_çiz(boyut):
    """ASCII kare çiz"""
    for i in range(boyut):
        if i == 0 or i == boyut - 1:
            print("*" * boyut)
        else:
            print("*" + " " * (boyut - 2) + "*")

def builtin_kalp_çiz():
    """ASCII kalp çiz"""
    heart = [
        "  ***   ***  ",
        " ***** ***** ",
        "************* ",
        " *********** ",
        "  *********  ",
        "   *******   ",
        "    *****    ",
        "     ***     ",
        "      *      "
    ]
    for line in heart:
        print(Fore.RED + line + Style.RESET_ALL)

def builtin_grafik_çiz(veriler):
    """Basit çubuk grafik çiz"""
    if not veriler:
        return
    
    max_val = max(veriler)
    for i, val in enumerate(veriler):
        bar_length = int((val / max_val) * 20)
        bar = "█" * bar_length
        print(f"{i+1:2d}: {bar} {val}")

def builtin_sözlük_oluştur(*elemanlar):
    """Yeni sözlük oluştur"""
    if len(elemanlar) % 2 != 0:
        raise RuntimeError("Sözlük için anahtar-değer çiftleri gerekli")
    
    sözlük = {}
    for i in range(0, len(elemanlar), 2):
        sözlük[elemanlar[i]] = elemanlar[i + 1]
    return sözlük

def builtin_sözlük_eleman(sözlük, anahtar):
    """Sözlükten eleman al"""
    if not isinstance(sözlük, dict):
        raise RuntimeError("İlk parametre sözlük olmalı")
    return sözlük.get(anahtar)

def builtin_sözlük_ekle(sözlük, anahtar, deger):
    """Sözlüğe eleman ekle"""
    if not isinstance(sözlük, dict):
        raise RuntimeError("İlk parametre sözlük olmalı")
    sözlük[anahtar] = deger
    return sözlük

def builtin_sözlük_sil(sözlük, anahtar):
    """Sözlükten eleman sil"""
    if not isinstance(sözlük, dict):
        raise RuntimeError("İlk parametre sözlük olmalı")
    if anahtar in sözlük:
        return sözlük.pop(anahtar)
    return None

def builtin_sözlük_anahtarlar(sözlük):
    """Sözlüğün anahtarlarını döndür"""
    if not isinstance(sözlük, dict):
        raise RuntimeError("Parametre sözlük olmalı")
    return list(sözlük.keys())

def builtin_sözlük_değerler(sözlük):
    """Sözlüğün değerlerini döndür"""
    if not isinstance(sözlük, dict):
        raise RuntimeError("Parametre sözlük olmalı")
    return list(sözlük.values())

def builtin_sözlük_uzunluk(sözlük):
    """Sözlüğün uzunluğunu döndür"""
    if not isinstance(sözlük, dict):
        raise RuntimeError("Parametre sözlük olmalı")
    return len(sözlük)

# Built-in functions dictionary
builtin_functions = {
    'rastgele': builtin_rastgele,
    'ondalık_rastgele': builtin_ondalık_rastgele,
    'karekök': builtin_karekök,
    'kuvvet': builtin_kuvvet,
    'mutlak': builtin_mutlak,
    'yuvarla': builtin_yuvarla,
    'sin': builtin_sin,
    'cos': builtin_cos,
    'tan': builtin_tan,
    'log': builtin_log,
    'log10': builtin_log10,
    'bekle': builtin_bekle,
    'şimdi': builtin_şimdi,
    'tarih': builtin_tarih,
    'saat': builtin_saat,
    'liste_oluştur': builtin_liste_oluştur,
    'liste_ekle': builtin_liste_ekle,
    'liste_uzunluk': builtin_liste_uzunluk,
    'liste_eleman': builtin_liste_eleman,
    'liste_sil': builtin_liste_sil,
    'metin_uzunluk': builtin_metin_uzunluk,
    'metin_kes': builtin_metin_kes,
    'metin_bul': builtin_metin_bul,
    'metin_degistir': builtin_metin_degistir,
    'büyük_harf': builtin_büyük_harf,
    'küçük_harf': builtin_küçük_harf,
    'dosya_oku': builtin_dosya_oku,
    'dosya_yaz': builtin_dosya_yaz,
    'dosya_ekle': builtin_dosya_ekle,
    'dosya_var_mi': builtin_dosya_var_mi,
    'dosya_sil': builtin_dosya_sil,
    'klasor_oluştur': builtin_klasor_oluştur,
    'klasor_listesi': builtin_klasor_listesi,
    # Yeni renkli yazdırma fonksiyonları
    'kırmızı_yaz': builtin_kırmızı_yaz,
    'yesil_yaz': builtin_yesil_yaz,
    'sarı_yaz': builtin_sarı_yaz,
    'mavi_yaz': builtin_mavi_yaz,
    'mor_yaz': builtin_mor_yaz,
    'turkuaz_yaz': builtin_turkuaz_yaz,
    'animasyonlu_yaz': builtin_animasyonlu_yaz,
    'animasyon_durdur': builtin_animasyon_durdur,
    # Çizim fonksiyonları
    'üçgen_çiz': builtin_üçgen_çiz,
    'kare_çiz': builtin_kare_çiz,
    'kalp_çiz': builtin_kalp_çiz,
    'grafik_çiz': builtin_grafik_çiz,
    # Sözlük işlemleri
    'sözlük_oluştur': builtin_sözlük_oluştur,
    'sözlük_eleman': builtin_sözlük_eleman,
    'sözlük_ekle': builtin_sözlük_ekle,
    'sözlük_sil': builtin_sözlük_sil,
    'sözlük_anahtarlar': builtin_sözlük_anahtarlar,
    'sözlük_değerler': builtin_sözlük_değerler,
    'sözlük_uzunluk': builtin_sözlük_uzunluk,
}

# --- Helpers ---
def current_frame():
    return env[-1]

def push_frame(frame=None, name=None):
    env.append({} if frame is None else dict(frame))
    call_trace.append({'name': name or '<anon>', 'line': None})

def pop_frame():
    env.pop()
    call_trace.pop()

def set_var(name, value):
    current_frame()[name] = value

def get_var_mapping():
    # merge frames for eval locals (later frames override earlier)
    merged = {}
    for frame in env:
        merged.update(frame)
    # Add built-in functions to the merged environment
    merged.update(builtin_functions)
    return merged

# split top-level comma-separated args (handles parentheses nesting)
def split_args(s: str):
    parts, buf, depth = [], [], 0
    i = 0
    while i < len(s):
        ch = s[i]
        if ch == '(':
            depth += 1; buf.append(ch)
        elif ch == ')':
            depth = max(0, depth - 1); buf.append(ch)
        elif ch == ',' and depth == 0:
            parts.append(''.join(buf).strip()); buf = []
        else:
            buf.append(ch)
        i += 1
    if buf:
        parts.append(''.join(buf).strip())
    return [p for p in parts if p != '']

# Collect a block of lines until the matching 'bitir', handling nested blocks.
def collect_block(lines, ptr):
    """
    Collect lines of a block starting at ptr until the matching 'bitir' for this block.
    Nested blocks (lines ending with ':') are tracked with a depth counter.
    Returns (body_list, ptr_index_of_matching_bitir).
    """
    body = []
    depth = 0
    while ptr < len(lines):
        ln = lines[ptr].strip()
        # if closing for this block, stop (do not consume it)
        if ln == 'bitir' and depth == 0:
            break
        # nested block start (e.g., '... ise:', '... iken:', '... işi:')
        if ln.endswith(':'):
            depth += 1
            body.append(lines[ptr])
            ptr += 1
            continue
        # closing of an inner block
        if ln == 'bitir' and depth > 0:
            depth -= 1
            body.append(lines[ptr])
            ptr += 1
            continue
        body.append(lines[ptr])
        ptr += 1
    return body, ptr

# parse user input into int/float/bool/string (supports Turkish 'doğru'/'yanlış')
def parse_input_value(s: str):
    s = s.strip()
    low = s.lower()
    if low == 'true' or low == 'doğru':
        return True
    if low == 'false' or low == 'yanlış':
        return False
    if re.fullmatch(r'[+-]?\d+', s):
        return int(s)
    if re.fullmatch(r'[+-]?\d+\.\d*', s):
        return float(s)
    return s

# safe plus: try arithmetic, else stringify and concat
def kv_add(a, b):
    try:
        return a + b
    except Exception:
        return str(a) + str(b)

# AST transform to turn '+' into kv_add(a, b)
class AddTransformer(ast.NodeTransformer):
    def visit_BinOp(self, node):
        self.generic_visit(node)
        if isinstance(node.op, ast.Add):
            return ast.copy_location(
                ast.Call(func=ast.Name(id='kv_add', ctx=ast.Load()),
                         args=[node.left, node.right], keywords=[]),
                node
            )
        return node

# translate Turkish operators/keywords inside expressions to Python
# NOTE: This function expects input where string literals have been replaced
# with placeholders, so it can safely translate without touching string content.
def translate_ops(e: str):
    # relational phrases first (keep flexible)
    e = re.sub(r'(\S+)\s+(\S+)\s+eşit\b',   r'\1 == \2', e)
    e = re.sub(r'(\S+)\s+(\S+)\s+farklı\b', r'\1 != \2', e)
    e = re.sub(r'\beşit\b',     '==',  e)
    e = re.sub(r'\bfarklı\b',   '!=',  e)
    e = re.sub(r'\bküçüktür\b', '<',   e)
    e = re.sub(r'\bbüyüktür\b', '>',   e)
    # boolean literals (Turkish)
    e = re.sub(r'\bdoğru\b', 'True', e)
    e = re.sub(r'\byanlış\b', 'False', e)
    # logical operators
    e = re.sub(r'\bve\b',       'and', e)
    e = re.sub(r'\bveya\b',     'or',  e)
    e = re.sub(r'\bdeğil\b',    'not', e)
    return e

# Helper: replace string literals with placeholders so translators don't touch them
def shield_strings(expr: str):
    """
    Replace string literals with placeholders.
    Returns (shielded_expr, placeholders_list)
    placeholders_list is list of original string literals in order: ['"abc"', "'a\\'b'"]
    Note: pattern intentionally does NOT treat backslashes as escapes. Kavun
    strings may contain raw backslashes (even before the closing quote).
    """
    # Use a simple "match until next same-quote" pattern so we do not treat \ as escape.
    pattern = re.compile(r'(\"[^\"]*\"|\'[^\']*\')', re.UNICODE)
    placeholders = []
    def repl(m):
        placeholders.append(m.group(0))
        return f"__KAVUN_STR_{len(placeholders)-1}__"
    shielded = pattern.sub(repl, expr)
    return shielded, placeholders

def restore_strings(expr: str, placeholders):
    # Replace placeholders with safe Python string literals using repr to
    # preserve backslashes and quotes exactly as intended by the user.
    for i, s in enumerate(placeholders):
        inner = s[1:-1]  # remove surrounding quotes
        expr = expr.replace(f"__KAVUN_STR_{i}__", repr(inner))
    return expr

# evaluate an expression (supports both call styles and Python-like expressions)
def evaluate(expr: str):
    e = expr.strip()
    shielded, placeholders = shield_strings(e)
    e2 = shielded

    # 1) Call style: "<args> ile <fname> işi"
    m = re.match(r'^(?P<args>.+?)\s+ile\s+(?P<fname>\w+)\s+işi$', e2)
    if m:
        raw_args = m.group('args')
        fname    = m.group('fname')
        if fname not in functions:
            raise RuntimeError(f"Tanınmayan fonksiyon: {fname}")
        arg_vals = [evaluate(a.strip()) for a in split_args(raw_args)]
        return call_function(fname, arg_vals)

    # 2) Call style: "iş <fname>(arg1, arg2, ...)"
    m = re.match(r'^iş\s+(?P<fname>\w+)\s*\((?P<args>.*)\)\s*$', e2)
    if m:
        fname = m.group('fname')
        if fname not in functions:
            raise RuntimeError(f"Tanınmayan fonksiyon: {fname}")
        raw_args = m.group('args').strip()
        arg_vals = [] if raw_args == '' else [evaluate(a.strip()) for a in split_args(raw_args)]
        return call_function(fname, arg_vals)

    # 3) Translate Turkish ops and compile with AST transform (kv_add)
    translated = translate_ops(e2)
    # restore string literals into safe Python string literals
    translated = restore_strings(translated, placeholders)

    key = translated
    code_obj = expr_cache.get(key)
    if code_obj is None:
        try:
            tree = ast.parse(translated, mode='eval')
            tree = AddTransformer().visit(tree)
            ast.fix_missing_locations(tree)
            code_obj = compile(tree, '<kavun-expr>', 'eval')
            expr_cache[key] = code_obj
        except Exception:
            try:
                code_obj = compile(translated, '<kavun-expr>', 'eval')
                expr_cache[key] = code_obj
            except Exception as ex2:
                raise RuntimeError(f"Geçersiz ifade [{expr}]: {ex2}")

    local_map = get_var_mapping()
    try:
        return eval(code_obj, {'kv_add': kv_add}, local_map)
    except Exception as ex:
        raise RuntimeError(f"İfade değerlendirme hatası [{expr}]: {ex}")

# call a user function by name (simple dispatcher)
def call_function(fname, arg_values):
    if fname not in functions:
        raise RuntimeError(f"Tanınmayan fonksiyon: {fname}")
    params, body = functions[fname]
    if len(arg_values) < len(params):
        arg_values = arg_values + [None] * (len(params) - len(arg_values))

    push_frame({}, name=fname)
    for name, val in zip(params, arg_values):
        set_var(name, val)

    ret = None
    try:
        run_block(body, 0)
    except ReturnFunction as r:
        ret = r.value
    finally:
        pop_frame()
    return ret

# Main interpreter loop: execute lines of a block
def run_block(lines, start=0):
    idx = start
    while idx < len(lines):
        if call_trace:
            call_trace[-1]['line'] = idx + 1
        raw  = lines[idx]
        line = raw.strip()

        # skip blanks and comments
        if not line or line.startswith("//"):
            idx += 1
            continue

        # end of a block
        if line == "bitir":
            return idx + 1

        # console clear: 'temizle'
        if line == "temizle":
            # Cross-platform clear
            try:
                if os.name == 'nt':
                    os.system('cls')
                else:
                    os.system('clear')
            except Exception:
                # fallback: lots of newlines
                print("\n" * 80)
            idx += 1
            continue

        # yeni satır: 'yeni_satır'
        if line == "yeni_satır":
            print()
            idx += 1
            continue

        # bekle: 'X saniye bekle'
        m = re.match(r'^(\d+(?:\.\d+)?)\s+saniye\s+bekle$', line)
        if m:
            try:
                time.sleep(float(m.group(1)))
            except Exception as ex:
                print(f"[Hata satır {idx+1}] Bekleme hatası: {ex}")
            idx += 1
            continue

        # liste oluştur: 'liste_adi eşittir [eleman1, eleman2, ...]'
        m = re.match(r'^(\w+)\s+eşittir\s+\[(.*)\]$', line)
        if m:
            var_name = m.group(1)
            elements_str = m.group(2).strip()
            if elements_str:
                elements = [evaluate(e.strip()) for e in split_args(elements_str)]
            else:
                elements = []
            set_var(var_name, elements)
            idx += 1
            continue

        # liste elemanına erişim: 'eleman eşittir liste_adi[0]'
        m = re.match(r'^(\w+)\s+eşittir\s+(\w+)\[(\d+)\]$', line)
        if m:
            var_name = m.group(1)
            list_name = m.group(2)
            index = int(m.group(3))
            list_var = get_var_mapping().get(list_name)
            if not isinstance(list_var, list):
                print(f"[Hata satır {idx+1}] {list_name} bir liste değil")
            elif index < 0 or index >= len(list_var):
                print(f"[Hata satır {idx+1}] Geçersiz indeks: {index}")
            else:
                set_var(var_name, list_var[index])
            idx += 1
            continue

        # liste elemanı değiştir: 'liste_adi[0] eşittir yeni_deger'
        m = re.match(r'^(\w+)\[(\d+)\]\s+eşittir\s+(.+)$', line)
        if m:
            list_name = m.group(1)
            index = int(m.group(2))
            new_value = evaluate(m.group(3).strip())
            list_var = get_var_mapping().get(list_name)
            if not isinstance(list_var, list):
                print(f"[Hata satır {idx+1}] {list_name} bir liste değil")
            elif index < 0 or index >= len(list_var):
                print(f"[Hata satır {idx+1}] Geçersiz indeks: {index}")
            else:
                list_var[index] = new_value
                set_var(list_name, list_var)
            idx += 1
            continue

        # liste elemanı ekle: 'liste_adi.ekle(eleman)'
        m = re.match(r'^(\w+)\.ekle\((.+)\)$', line)
        if m:
            list_name = m.group(1)
            element = evaluate(m.group(2).strip())
            list_var = get_var_mapping().get(list_name)
            if not isinstance(list_var, list):
                print(f"[Hata satır {idx+1}] {list_name} bir liste değil")
            else:
                list_var.append(element)
                set_var(list_name, list_var)
            idx += 1
            continue

        # liste elemanı sil: 'liste_adi.sil(0)'
        m = re.match(r'^(\w+)\.sil\((\d+)\)$', line)
        if m:
            list_name = m.group(1)
            index = int(m.group(2))
            list_var = get_var_mapping().get(list_name)
            if not isinstance(list_var, list):
                print(f"[Hata satır {idx+1}] {list_name} bir liste değil")
            elif index < 0 or index >= len(list_var):
                print(f"[Hata satır {idx+1}] Geçersiz indeks: {index}")
            else:
                list_var.pop(index)
                set_var(list_name, list_var)
            idx += 1
            continue

        # metin işlemleri: 'metin_adi.uzunluk()'
        m = re.match(r'^(\w+)\.uzunluk\(\)$', line)
        if m:
            var_name = m.group(1)
            text_var = get_var_mapping().get(var_name, "")
            set_var(var_name + "_uzunluk", len(str(text_var)))
            idx += 1
            continue

        # metin büyük harf: 'metin_adi.büyük_harf()'
        m = re.match(r'^(\w+)\.büyük_harf\(\)$', line)
        if m:
            var_name = m.group(1)
            text_var = get_var_mapping().get(var_name, "")
            set_var(var_name + "_büyük", str(text_var).upper())
            idx += 1
            continue

        # metin küçük harf: 'metin_adi.küçük_harf()'
        m = re.match(r'^(\w+)\.küçük_harf\(\)$', line)
        if m:
            var_name = m.group(1)
            text_var = get_var_mapping().get(var_name, "")
            set_var(var_name + "_küçük", str(text_var).lower())
            idx += 1
            continue

        # dosya işlemleri: 'dosya_oku("dosya.txt")'
        m = re.match(r'^dosya_oku\("([^"]+)"\)$', line)
        if m:
            try:
                dosya_adi = m.group(1)
                icerik = builtin_dosya_oku(dosya_adi)
                set_var("dosya_içerik", icerik)
            except Exception as ex:
                print(f"[Hata satır {idx+1}] {ex}")
            idx += 1
            continue

        # dosya yaz: 'dosya_yaz("dosya.txt", icerik)'
        m = re.match(r'^dosya_yaz\("([^"]+)",\s*(.+)\)$', line)
        if m:
            try:
                dosya_adi = m.group(1)
                icerik = evaluate(m.group(2).strip())
                builtin_dosya_yaz(dosya_adi, icerik)
            except Exception as ex:
                print(f"[Hata satır {idx+1}] {ex}")
            idx += 1
            continue

        # klasör listesi: 'klasor_listesi()'
        if line == "klasor_listesi()":
            try:
                dosyalar = builtin_klasor_listesi()
                set_var("dosya_listesi", dosyalar)
                print("Klasördeki dosyalar:")
                for dosya in dosyalar:
                    print(f"  - {dosya}")
            except Exception as ex:
                print(f"[Hata satır {idx+1}] {ex}")
            idx += 1
            continue

        # zaman bilgileri
        if line == "şimdi()":
            set_var("su_an", builtin_şimdi())
            idx += 1
            continue

        if line == "tarih()":
            set_var("bugun", builtin_tarih())
            idx += 1
            continue

        if line == "saat()":
            set_var("su_saat", builtin_saat())
            idx += 1
            continue

        # rastgele sayı: 'rastgele_sayi()'
        if line == "rastgele_sayi()":
            set_var("rastgele", builtin_rastgele())
            idx += 1
            continue

        # rastgele sayı aralık: '1 ile 10 arasi_rastgele()'
        m = re.match(r'^(\d+)\s+ile\s+(\d+)\s+arasi_rastgele\(\)$', line)
        if m:
            min_val = int(m.group(1))
            max_val = int(m.group(2))
            set_var("rastgele", builtin_rastgele(min_val, max_val))
            idx += 1
            continue

        # rastgele sayı aralık: 'gizli_sayi eşittir 1 ile 100 arasi_rastgele()'
        m = re.match(r'^(\w+)\s+eşittir\s+(\d+)\s+ile\s+(\d+)\s+arasi_rastgele\(\)$', line)
        if m:
            var_name = m.group(1)
            min_val = int(m.group(2))
            max_val = int(m.group(3))
            set_var(var_name, builtin_rastgele(min_val, max_val))
            idx += 1
            continue

        # renkli yazdırma: 'metin kırmızı_yaz'
        m = re.match(r'^(.+)\s+kırmızı_yaz$', line)
        if m:
            try:
                metin = evaluate(m.group(1).strip())
                builtin_kırmızı_yaz(metin)
            except Exception as ex:
                print(f"[Hata satır {idx+1}] Kırmızı yazdırma hatası: {ex}")
            idx += 1
            continue

        # renkli yazdırma: 'metin yesil_yaz'
        m = re.match(r'^(.+)\s+yesil_yaz$', line)
        if m:
            try:
                metin = evaluate(m.group(1).strip())
                builtin_yesil_yaz(metin)
            except Exception as ex:
                print(f"[Hata satır {idx+1}] Yeşil yazdırma hatası: {ex}")
            idx += 1
            continue

        # renkli yazdırma: 'metin sarı_yaz'
        m = re.match(r'^(.+)\s+sarı_yaz$', line)
        if m:
            try:
                metin = evaluate(m.group(1).strip())
                builtin_sarı_yaz(metin)
            except Exception as ex:
                print(f"[Hata satır {idx+1}] Sarı yazdırma hatası: {ex}")
            idx += 1
            continue

        # renkli yazdırma: 'metin mavi_yaz'
        m = re.match(r'^(.+)\s+mavi_yaz$', line)
        if m:
            try:
                metin = evaluate(m.group(1).strip())
                builtin_mavi_yaz(metin)
            except Exception as ex:
                print(f"[Hata satır {idx+1}] Mavi yazdırma hatası: {ex}")
            idx += 1
            continue

        # renkli yazdırma: 'metin mor_yaz'
        m = re.match(r'^(.+)\s+mor_yaz$', line)
        if m:
            try:
                metin = evaluate(m.group(1).strip())
                builtin_mor_yaz(metin)
            except Exception as ex:
                print(f"[Hata satır {idx+1}] Mor yazdırma hatası: {ex}")
            idx += 1
            continue

        # renkli yazdırma: 'metin turkuaz_yaz'
        m = re.match(r'^(.+)\s+turkuaz_yaz$', line)
        if m:
            try:
                metin = evaluate(m.group(1).strip())
                builtin_turkuaz_yaz(metin)
            except Exception as ex:
                print(f"[Hata satır {idx+1}] Turkuaz yazdırma hatası: {ex}")
            idx += 1
            continue

        # animasyonlu yazdırma: 'metin animasyonlu_yaz'
        m = re.match(r'^(.+)\s+animasyonlu_yaz$', line)
        if m:
            try:
                metin = evaluate(m.group(1).strip())
                builtin_animasyonlu_yaz(metin)
            except Exception as ex:
                print(f"[Hata satır {idx+1}] Animasyonlu yazdırma hatası: {ex}")
            idx += 1
            continue

        # animasyon durdur: 'animasyon_durdur'
        if line == "animasyon_durdur":
            builtin_animasyon_durdur()
            idx += 1
            continue

        # çizim komutları: 'üçgen_çiz(5)'
        m = re.match(r'^üçgen_çiz\((\d+)\)$', line)
        if m:
            try:
                boyut = int(m.group(1))
                builtin_üçgen_çiz(boyut)
            except Exception as ex:
                print(f"[Hata satır {idx+1}] Üçgen çizme hatası: {ex}")
            idx += 1
            continue

        # çizim komutları: 'kare_çiz(4)'
        m = re.match(r'^kare_çiz\((\d+)\)$', line)
        if m:
            try:
                boyut = int(m.group(1))
                builtin_kare_çiz(boyut)
            except Exception as ex:
                print(f"[Hata satır {idx+1}] Kare çizme hatası: {ex}")
            idx += 1
            continue

        # çizim komutları: 'kalp_çiz()'
        if line == "kalp_çiz()":
            try:
                builtin_kalp_çiz()
            except Exception as ex:
                print(f"[Hata satır {idx+1}] Kalp çizme hatası: {ex}")
            idx += 1
            continue

        # grafik çiz: 'grafik_çiz([1, 3, 2, 5, 4])'
        m = re.match(r'^grafik_çiz\(\[(.*)\]\)$', line)
        if m:
            try:
                veriler_str = m.group(1).strip()
                if veriler_str:
                    veriler = [evaluate(v.strip()) for v in split_args(veriler_str)]
                else:
                    veriler = []
                builtin_grafik_çiz(veriler)
            except Exception as ex:
                print(f"[Hata satır {idx+1}] Grafik çizme hatası: {ex}")
            idx += 1
            continue

        # sözlük oluştur: 'sözlük_adi eşittir {"anahtar1": deger1, "anahtar2": deger2}'
        m = re.match(r'^(\w+)\s+eşittir\s+\{(.*)\}$', line)
        if m:
            try:
                var_name = m.group(1)
                pairs_str = m.group(2).strip()
                if pairs_str:
                    # Basit sözlük parsing
                    pairs = []
                    current_key = None
                    current_value = None
                    in_quotes = False
                    quote_char = None
                    buffer = ""
                    
                    for char in pairs_str:
                        if char in ['"', "'"] and not in_quotes:
                            in_quotes = True
                            quote_char = char
                            buffer += char
                        elif char == quote_char and in_quotes:
                            in_quotes = False
                            buffer += char
                        elif char == ':' and not in_quotes:
                            current_key = buffer.strip().strip('"\'')
                            buffer = ""
                        elif char == ',' and not in_quotes:
                            current_value = buffer.strip().strip('"\'')
                            pairs.extend([current_key, current_value])
                            buffer = ""
                        else:
                            buffer += char
                    
                    if buffer.strip():
                        current_value = buffer.strip().strip('"\'')
                        pairs.extend([current_key, current_value])
                    
                    sözlük = builtin_sözlük_oluştur(*pairs)
                else:
                    sözlük = {}
                set_var(var_name, sözlük)
            except Exception as ex:
                print(f"[Hata satır {idx+1}] Sözlük oluşturma hatası: {ex}")
            idx += 1
            continue

        # sözlük elemanına erişim: 'eleman eşittir sözlük_adi["anahtar"]'
        m = re.match(r'^(\w+)\s+eşittir\s+(\w+)\["([^"]+)"\]$', line)
        if m:
            try:
                var_name = m.group(1)
                dict_name = m.group(2)
                key = m.group(3)
                dict_var = get_var_mapping().get(dict_name)
                if not isinstance(dict_var, dict):
                    print(f"[Hata satır {idx+1}] {dict_name} bir sözlük değil")
                else:
                    value = builtin_sözlük_eleman(dict_var, key)
                    set_var(var_name, value)
            except Exception as ex:
                print(f"[Hata satır {idx+1}] Sözlük erişim hatası: {ex}")
            idx += 1
            continue

        # sözlük elemanı değiştir: 'sözlük_adi["anahtar"] eşittir yeni_deger'
        m = re.match(r'^(\w+)\["([^"]+)"\]\s+eşittir\s+(.+)$', line)
        if m:
            try:
                dict_name = m.group(1)
                key = m.group(2)
                new_value = evaluate(m.group(3).strip())
                dict_var = get_var_mapping().get(dict_name)
                if not isinstance(dict_var, dict):
                    print(f"[Hata satır {idx+1}] {dict_name} bir sözlük değil")
                else:
                    builtin_sözlük_ekle(dict_var, key, new_value)
                    set_var(dict_name, dict_var)
            except Exception as ex:
                print(f"[Hata satır {idx+1}] Sözlük değiştirme hatası: {ex}")
            idx += 1
            continue

        # loop controls
        if line == "kır":
            raise BreakLoop()
        if line == "devam":
            raise ContinueLoop()

        # return from function
        if line == "dön":
            raise ReturnFunction(None)
        m = re.match(r'^(.+)\s+dön$', line)
        if m:
            val = evaluate(m.group(1).strip())
            raise ReturnFunction(val)

        # assignment: "var eşittir expr" or "var = expr"
        m = re.match(r'^(.+?)\s*(?:eşittir|=)\s*(.+)$', line)
        if m:
            var  = m.group(1).strip()
            expr = m.group(2).strip()
            if expr == "cevap()":
                inp = input()
                set_var(var, parse_input_value(inp))
            else:
                set_var(var, evaluate(expr))
            idx += 1
            continue

        # print: "<expr> yaz"
        m = re.match(r'^(.+)\s+yaz$', line)
        if m:
            try:
                print(evaluate(m.group(1).strip()))
            except Exception as ex:
                print(f"[Hata satır {idx+1}] Yazdırma hatası: {ex}")
            idx += 1
            continue

        # If-Else chain handling (collect clauses using collect_block)
        if line.endswith(" ise:"):
            clauses, ptr = [], idx
            # collect consecutive if/elif clauses
            while ptr < len(lines):
                ln = lines[ptr].strip()
                m2 = re.match(r'^(yoksa\s+)?(.+?)\s+ise:$', ln)
                if not m2:
                    break
                is_elif = bool(m2.group(1))
                cond    = m2.group(2).strip()
                ptr += 1
                body, ptr = collect_block(lines, ptr)
                clauses.append(('elif' if is_elif else 'if', cond, body))

            # optional else "yoksa:"
            if ptr < len(lines) and lines[ptr].strip() == "yoksa:":
                ptr += 1
                else_body, ptr = collect_block(lines, ptr)
                clauses.append(('else', None, else_body))

            # execute first matching clause
            executed = False
            for typ, cond, body in clauses:
                if not executed and typ in ("if", "elif") and evaluate(cond):
                    try:
                        run_block(body, 0)
                    except ContinueLoop:
                        # continue inside current containing loop
                        pass
                    except BreakLoop:
                        # propagate break to outer loop handler
                        raise
                    executed = True
                elif not executed and typ == "else":
                    try:
                        run_block(body, 0)
                    except ContinueLoop:
                        pass
                    except BreakLoop:
                        raise
                    executed = True

            # skip the closing 'bitir' for the whole if-else block
            idx = ptr + 1
            continue

        # While loop: "<cond> iken:" ... "bitir"
        m = re.match(r'^(.+?)\s+iken:$', line)
        if m:
            cond = m.group(1).strip()
            ptr  = idx + 1
            body, ptr = collect_block(lines, ptr)
            try:
                while evaluate(cond):
                    try:
                        run_block(body, 0)
                    except ContinueLoop:
                        continue
            except BreakLoop:
                pass
            idx = ptr + 1
            continue

        # For loop: "i için X den Y kadar:" ... "bitir"
        m = re.match(r'^(\w+)\s+için\s+([+-]?\d+)\s+den\s+([+-]?\d+)\s+kadar:$', line)
        if m:
            var     = m.group(1)
            lo, hi  = int(m.group(2)), int(m.group(3))
            ptr     = idx + 1
            body, ptr = collect_block(lines, ptr)
            for i in range(lo, hi + 1):
                set_var(var, i)
                try:
                    run_block(body, 0)
                except ContinueLoop:
                    continue
                except BreakLoop:
                    break
            idx = ptr + 1
            continue

        # Function definition: "a, b ile topla işi:" ... "bitir"
        m = re.match(r'^(.+?)\s+ile\s+(.+?)\s+işi:$', line)
        if m:
            raw_args = m.group(1)
            fname    = m.group(2).strip()
            params   = [a.strip() for a in split_args(raw_args)]
            ptr      = idx + 1
            body, ptr = collect_block(lines, ptr)
            functions[fname] = (params, body)
            idx = ptr + 1
            continue

        # Void function call statements (both styles)
        m = re.match(r'^(.+?)\s+ile\s+(.+?)\s+işi$', line)
        if m:
            try:
                evaluate(f"{m.group(1)} ile {m.group(2)} işi")
            except Exception as ex:
                print(f"[Hata satır {idx+1}] {ex}")
            idx += 1
            continue
        m = re.match(r'^iş\s+(\w+)\s*\((.*)\)\s*$', line)
        if m:
            try:
                evaluate(line)
            except Exception as ex:
                print(f"[Hata satır {idx+1}] {ex}")
            idx += 1
            continue

        # unknown command
        print(f"[Hata satır {idx+1}] Tanınmayan komut: {line}")
        idx += 1

    return idx

# Print a short runtime trace (Turkish)
def print_runtime_error(exc):
    print("Çalışma zamanı hatası:", exc)
    if call_trace:
        print("Çağrı yığını (son çağrı en üstte):")
        for frame in reversed(call_trace):
            name = frame.get('name', '<anon>')
            line = frame.get('line')
            if line is None:
                print(f"  - {name}")
            else:
                print(f"  - {name} (satır {line})")
    print("Hata detaylarını görmek için ortam değişkeni KAVUN_DEBUG=1 ile tekrar çalıştırın.")

def main():
    if len(sys.argv) != 2:
        print(" __    __                                        ")
        print("|  \\  /  \\                                       ")
        print("| $$ /  $$ ______  __     __  __    __  _______  ")
        print("| $$/  $$ |      \\|  \\   /  \\|  \\  |  \\|       \\ ")
        print("| $$  $$   \\$$$$$$\\\\$$\\ /  $$| $$  | $$| $$$$$$$\\")
        print("| $$$$$\\  /      $$ \\$$\\  $$ | $$  | $$| $$  | $$")
        print("| $$ \\$$\\|  $$$$$$$  \\$$ $$  | $$__/ $$| $$  | $$")
        print("| $$  \\$$\\\\$$    $$   \\$$$    \\$$    $$| $$  | $$")
        print(" \\$$   \\$$ \\$$$$$$$    \\$      \\$$$$$$  \\$$   \\$$")
        print("")
        print("----- The Kavun Language Interpreter V0.6-------")
        print("")
        print("Kullanım: python interpreter.py <dosya.kvn>")
        print("")
        sys.exit(1)
    path = sys.argv[1]
    try:
        lines = open(path, encoding='utf-8').read().splitlines()
    except FileNotFoundError:
        print(f"Dosya bulunamadı: {path}")
        sys.exit(1)

    non_blank = [ln for ln in lines if ln.strip() and not ln.strip().startswith("//")]
    if len(non_blank) == 0:
        print("Çalıştırılan dosya boş. Bir 'Merhaba Dünya' örneği ile başlayabilirsiniz:")
        print('\"Merhaba Dünya\" yaz')
        sys.exit(0)

    call_trace.append({'name': '<main>', 'line': None})
    try:
        run_block(lines, 0)
    except Exception as e:
        print_runtime_error(e)
        if os.environ.get('KAVUN_DEBUG') == '1':
            traceback.print_exc()
    finally:
        call_trace.clear()

if __name__ == "__main__":
    main()
