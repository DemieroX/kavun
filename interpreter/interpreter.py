# --- The Kavun Language Interpreter V0.5---
# Bu Kavun dilinin Python tabanlı interpreter programıdır.
# Çalıştırmak için: python interpreter.py dosya.kvn

#!/usr/bin/env python3
import re, sys, ast, traceback, os

class BreakLoop(Exception): pass   # Exception used to break out of loops  # Exception: break statement
class ContinueLoop(Exception): pass   # Exception used to continue loops  # Exception: continue statement
class ReturnFunction(Exception):   # Exception used to return a value from a function  # Exception: return from function
    def __init__(self, value):
        self.value = value

# Çalışma zamanı durumları
env = [{}]               # Environment stack; env[0] is global, env[-1] is current frame               # Çerçeve yığını; env[0] global, env[-1] güncel
functions = {}           # Function definitions: name -> (params, body)           # isim -> (params, body_lines)
expr_cache = {}          # Cache for compiled expressions          # ifade metni -> derlenmiş kod
call_trace = []          # Call trace for error reporting          # çağrı yığını (hata raporları için)

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
    merged = {}
    for frame in env:
        merged.update(frame)
    return merged

def split_args(s: str):   # Split function call arguments by top-level commas
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

def parse_input_value(s: str):   # Parse input into int, float, bool, or string
    s = s.strip()
    if s.lower() == 'true': return True
    if s.lower() == 'false': return False
    if re.fullmatch(r'[+-]?\d+', s): return int(s)
    if re.fullmatch(r'[+-]?\d+\.\d*', s): return float(s)
    return s

def kv_add(a, b):   # Safe addition/concatenation between strings and numbers
    try:
        return a + b
    except Exception:
        return str(a) + str(b)

class AddTransformer(ast.NodeTransformer):   # AST transformer to replace '+' with kv_add
    def visit_BinOp(self, node):
        self.generic_visit(node)
        if isinstance(node.op, ast.Add):
            return ast.copy_location(
                ast.Call(func=ast.Name(id='kv_add', ctx=ast.Load()),
                         args=[node.left, node.right], keywords=[]),
                node
            )
        return node

def translate_ops(e: str):   # Translate Turkish operators to Python equivalents
    e = re.sub(r'(\S+)\s+(\S+)\s+eşit\b',   r'\1 == \2', e)
    e = re.sub(r'(\S+)\s+(\S+)\s+farklı\b', r'\1 != \2', e)
    e = re.sub(r'\beşit\b',     '==',  e)
    e = re.sub(r'\bfarklı\b',   '!=',  e)
    e = re.sub(r'\bküçüktür\b', '<',   e)
    e = re.sub(r'\bbüyüktür\b', '>',   e)
    e = re.sub(r'\bve\b',       'and', e)
    e = re.sub(r'\bveya\b',     'or',  e)
    e = re.sub(r'\bdeğil\b',    'not', e)
    return e

def evaluate(expr: str):   # Evaluate a Kavun expression
    e = expr.strip()

    m = re.match(r'^(?P<args>.+?)\s+ile\s+(?P<fname>\w+)\s+işi$', e)
    if m:
        raw_args = m.group('args')
        fname    = m.group('fname')
        if fname not in functions:
            raise RuntimeError(f"Tanınmayan fonksiyon: {fname}")
        arg_vals = [evaluate(a.strip()) for a in split_args(raw_args)]
        return call_function(fname, arg_vals)

    m = re.match(r'^iş\s+(?P<fname>\w+)\s*\((?P<args>.*)\)\s*$', e)
    if m:
        fname = m.group('fname')
        if fname not in functions:
            raise RuntimeError(f"Tanınmayan fonksiyon: {fname}")
        raw_args = m.group('args').strip()
        arg_vals = [] if raw_args == '' else [evaluate(a.strip()) for a in split_args(raw_args)]
        return call_function(fname, arg_vals)

    translated = translate_ops(e)
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

def call_function(fname, arg_values):   # Call a user-defined function
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

def run_block(lines, start=0):   # Run a block of Kavun code line by line  # Main interpreter loop, executes lines
    idx = start
    while idx < len(lines):
        if call_trace:
            call_trace[-1]['line'] = idx + 1
        raw  = lines[idx]
        line = raw.strip()

        if not line or line.startswith("//"):
            idx += 1
            continue

        if line == "bitir":
            return idx + 1

        if line == "kır":
            raise BreakLoop()
        if line == "devam":
            raise ContinueLoop()

        if line == "dön":
            raise ReturnFunction(None)
        m = re.match(r'^(.+)\s+dön$', line)
        if m:
            val = evaluate(m.group(1).strip())
            raise ReturnFunction(val)

        m = re.match(r'^(.+?)\s*(?:eşittir|=)\s*(.+)$', line)  # Variable assignment
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

        m = re.match(r'^(.+)\s+yaz$', line)  # Print statement
        if m:
            try:
                print(evaluate(m.group(1).strip()))
            except Exception as ex:
                print(f"[Hata satır {idx+1}] Yazdırma hatası: {ex}")
            idx += 1
            continue

        if line.endswith(" ise:"):  # If-Else chain
            clauses, ptr = [], idx
            while ptr < len(lines):
                ln = lines[ptr].strip()
                m2 = re.match(r'^(yoksa\s+)?(.+?)\s+ise:$', ln)
                if not m2: break
                is_elif = bool(m2.group(1))
                cond    = m2.group(2).strip()
                ptr    += 1
                body    = []
                while ptr < len(lines):
                    nxt = lines[ptr].strip()
                    if nxt.endswith(" ise:") or nxt.startswith("yoksa") or nxt=="bitir":
                        break
                    body.append(lines[ptr])
                    ptr += 1
                clauses.append(('elif' if is_elif else 'if', cond, body))

            if ptr < len(lines) and lines[ptr].strip() == "yoksa:":
                ptr += 1
                else_body = []
                while ptr < len(lines) and lines[ptr].strip() != "bitir":
                    else_body.append(lines[ptr])
                    ptr += 1
                clauses.append(('else', None, else_body))

            while ptr < len(lines) and lines[ptr].strip() == "bitir":
                ptr += 1

            executed = False
            for typ, cond, body in clauses:
                if not executed and typ in ("if", "elif") and evaluate(cond):
                    run_block(body, 0)
                    executed = True
                elif not executed and typ == "else":
                    run_block(body, 0)
                    executed = True

            idx = ptr
            continue

        m = re.match(r'^(.+?)\s+iken:$', line)  # While loop
        if m:
            cond = m.group(1).strip()
            ptr  = idx + 1
            body = []
            while ptr < len(lines) and lines[ptr].strip() != "bitir":
                body.append(lines[ptr]); ptr += 1
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

        m = re.match(r'^(\w+)\s+için\s+([+-]?\d+)\s+den\s+([+-]?\d+)\s+kadar:$', line)  # For loop
        if m:
            var     = m.group(1)
            lo, hi  = int(m.group(2)), int(m.group(3))
            ptr     = idx + 1
            body    = []
            while ptr < len(lines) and lines[ptr].strip() != "bitir":
                body.append(lines[ptr]); ptr += 1
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

        m = re.match(r'^(.+?)\s+ile\s+(.+?)\s+işi:$', line)  # Function definition
        if m:
            raw_args = m.group(1)
            fname    = m.group(2).strip()
            params   = [a.strip() for a in split_args(raw_args)]
            ptr      = idx + 1
            body     = []
            while ptr < len(lines) and lines[ptr].strip() != "bitir":
                body.append(lines[ptr]); ptr += 1
            functions[fname] = (params, body)
            idx = ptr + 1
            continue

        m = re.match(r'^(.+?)\s+ile\s+(.+?)\s+işi$', line)  # Function call (style 1)
        if m:
            try:
                evaluate(f"{m.group(1)} ile {m.group(2)} işi")
            except Exception as ex:
                print(f"[Hata satır {idx+1}] {ex}")
            idx += 1
            continue
        m = re.match(r'^iş\s+(\w+)\s*\((.*)\)\s*$', line)  # Function call (style 2)
        if m:
            try:
                evaluate(line)
            except Exception as ex:
                print(f"[Hata satır {idx+1}] {ex}")
            idx += 1
            continue

        print(f"[Hata satır {idx+1}] Tanınmayan komut: {line}")
        idx += 1

    return idx

def print_runtime_error(exc):   # Print runtime errors with call trace
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

def main():   # Program entry point
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
        print("------- The Kavun Language Interpreter V0.5-------")
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
        print("KAVUN: Çalıştırılan dosya boş. Denemeniz için bir 'Merhaba Dünya' örneği:")
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
