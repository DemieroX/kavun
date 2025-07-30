# --- The Kavun Language Interpreter V0.1---
# Bu Kavun dilinin ilk interpreter programıdır.
# Fonksiyonlar dışında çoğu özellik basit de olsa çalışmaktadır.
# age_checker.kvn hariç bütün örnek dosyaları çalışmaktadır.
#
# Çalıştırmak için: python interpreter.py dosya.kvn

#!/usr/bin/env python3
import re, sys

# -- Exceptions for control flow
class BreakLoop(Exception): pass
class ContinueLoop(Exception): pass
class ReturnFunction(Exception):
    def __init__(self, value):
        self.value = value

variables = {}
functions = {}

def evaluate(expr: str):
    """
    1) Detect and execute Kavun function calls of the form:
         <arg-list> ile <fname> işi
    2) Rewrite Turkish ops → Python ops
    3) eval() under our `variables`
    """
    e = expr.strip()

    # 1) FUNCTION‐CALL SHORTCUT
    #    <anything> ile <word> işi
    m = re.match(r'^(?P<args>.+?)\s+ile\s+(?P<fname>\w+)\s+işi$', e)
    if m:
        raw_args = m.group('args')
        fname    = m.group('fname')
        if fname not in functions:
            raise RuntimeError(f"Undefined function: {fname}")
        # evaluate each argument recursively
        arg_vals = [evaluate(a.strip()) for a in raw_args.split(',')]
        return call_function(fname, arg_vals)

    # 2) TURKISH → PYTHON REWRITES
    # postfix forms
    e = re.sub(r'(\S+)\s+(\S+)\s+eşit\b',   r'\1 == \2', e)
    e = re.sub(r'(\S+)\s+(\S+)\s+farklı\b', r'\1 != \2', e)
    # infix forms
    e = re.sub(r'\beşit\b',     '==',  e)
    e = re.sub(r'\bfarklı\b',   '!=',  e)
    e = re.sub(r'\bküçüktür\b', '<',   e)
    e = re.sub(r'\bbüyüktür\b', '>',   e)
    e = re.sub(r'\bve\b',       'and', e)
    e = re.sub(r'\bveya\b',     'or',  e)
    e = re.sub(r'\bdeğil\b',    'not', e)

    # 3) FALL BACK TO PYTHON
    try:
        return eval(e, {}, variables)
    except Exception as ex:
        raise RuntimeError(f"Invalid expression [{expr}]: {ex}")

def call_function(fname, arg_values):
    """
    Bind arguments, run the body, catch ReturnFunction,
    then restore `variables` and return the result.
    """
    params, body = functions[fname]
    # backup
    backup = dict(variables)
    for name, val in zip(params, arg_values):
        variables[name] = val

    try:
        run_block(body, 0)
        ret = None
    except ReturnFunction as r:
        ret = r.value

    # restore
    variables.clear()
    variables.update(backup)
    return ret

def run_block(lines, start=0):
    idx = start
    while idx < len(lines):
        raw  = lines[idx]
        line = raw.strip()

        # skip blank or comment
        if not line or line.startswith("//"):
            idx += 1
            continue

        # end of block
        if line == "bitir":
            return idx + 1

        # loop controls
        if line == "kır":
            raise BreakLoop()
        if line == "devam":
            raise ContinueLoop()

        # 1) Function return
        m = re.match(r'^(.+)\s+dön$', line)
        if m:
            val = evaluate(m.group(1).strip())
            raise ReturnFunction(val)

        # 2) Assignment: var eşittir expr
        m = re.match(r'^(.+?)\s*(?:eşittir|=)\s*(.+)$', line)
        if m:
            var  = m.group(1).strip()
            expr = m.group(2).strip()
            if expr == "cevap()":
                inp = input()
                variables[var] = int(inp) if inp.isdigit() else inp
            else:
                variables[var] = evaluate(expr)
            idx += 1
            continue

        # 3) Print: <expr> yaz
        m = re.match(r'^(.+)\s+yaz$', line)
        if m:
            try:
                print(evaluate(m.group(1).strip()))
            except Exception as ex:
                print(f"[Hata satır {idx+1}] Yazdırma hatası: {ex}")
            idx += 1
            continue

        # 4) If‐Else chain
        if line.endswith(" ise:"):
            clauses, ptr = [], idx
            # collect if/elif
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

            # optional plain else
            if ptr < len(lines) and lines[ptr].strip() == "yoksa:":
                ptr += 1
                else_body = []
                while ptr < len(lines) and lines[ptr].strip() != "bitir":
                    else_body.append(lines[ptr])
                    ptr += 1
                clauses.append(('else', None, else_body))

            # skip trailing bitir(s)
            while ptr < len(lines) and lines[ptr].strip() == "bitir":
                ptr += 1

            # execute first matching
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

        # 5) While loop
        m = re.match(r'^(.+?)\s+iken:$', line)
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

        # 6) For loop
        m = re.match(r'^(\w+)\s+için\s+(\d+)\s+den\s+(\d+)\s+kadar:$', line)
        if m:
            var     = m.group(1)
            lo, hi  = int(m.group(2)), int(m.group(3))
            ptr     = idx + 1
            body    = []
            while ptr < len(lines) and lines[ptr].strip() != "bitir":
                body.append(lines[ptr]); ptr += 1
            for i in range(lo, hi + 1):
                variables[var] = i
                try:
                    run_block(body, 0)
                except ContinueLoop:
                    continue
                except BreakLoop:
                    break
            idx = ptr + 1
            continue

        # 7) Function definition
        m = re.match(r'^(.+?)\s+ile\s+(.+?)\s+işi:$', line)
        if m:
            raw_args = m.group(1)
            fname    = m.group(2).strip()
            params   = [a.strip() for a in raw_args.split(',') if a.strip()]
            ptr      = idx + 1
            body     = []
            while ptr < len(lines) and lines[ptr].strip() != "bitir":
                body.append(lines[ptr]); ptr += 1
            functions[fname] = (params, body)
            idx = ptr + 1
            continue

        # 8) Void function call
        m = re.match(r'^(.+?)\s+ile\s+(.+?)\s+işi$', line)
        if m:
            # just eval to trigger side effects
            try:
                evaluate(f"{m.group(1)} ile {m.group(2)} işi")
            except Exception as ex:
                print(f"[Hata satır {idx+1}] {ex}")
            idx += 1
            continue

        # unknown
        print(f"[Hata satır {idx+1}] Tanınmayan komut: {line}")
        idx += 1

    return idx

def main():
    if len(sys.argv) != 2:
        print(f"Kullanım: {sys.argv[0]} <dosya.kvn>")
        sys.exit(1)
    lines = open(sys.argv[1], encoding="utf-8").read().splitlines()
    try:
        run_block(lines, 0)
    except Exception as e:
        print(f"Çalışma zamanı hatası: {e}")

if __name__ == "__main__":
    main()
