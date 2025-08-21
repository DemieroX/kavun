#!/usr/bin/env python3
# Kavun Interpreter - updated (string-protected translations, Turkish booleans, temizle)
import re, sys, ast, traceback, os

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
