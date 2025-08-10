#!/usr/bin/env python3
import ast
import sys
from pathlib import Path

METHODS = {"get", "post", "put", "patch", "delete"}

class RouteIssue:
    def __init__(self, file, line, msg):
        self.file = file
        self.line = line
        self.msg = msg
    def __str__(self):
        return f"{self.file}:{self.line}: {self.msg}"

def is_router_call(dec):
    # @router.<method>(...)
    return (
        isinstance(dec, ast.Call)
        and isinstance(dec.func, ast.Attribute)
        and isinstance(dec.func.value, ast.Name)
        and dec.func.value.id == "router"
        and dec.func.attr in METHODS
    )

def get_kw(dec: ast.Call, name: str):
    for kw in dec.keywords:
        if kw.arg == name:
            return kw.value
    return None

def kw_is_204(kw):
    # status_code=204 OR status.HTTP_204_NO_CONTENT
    if isinstance(kw, ast.Constant) and kw.value == 204:
        return True
    if isinstance(kw, ast.Attribute) and isinstance(kw.value, ast.Name):
        return kw.attr == "HTTP_204_NO_CONTENT" and kw.value.id == "status"
    return False

def value_is_none(node):
    return isinstance(node, ast.Constant) and node.value is None

def returns_dict(fn: ast.FunctionDef):
    for n in ast.walk(fn):
        if isinstance(n, ast.Return):
            # return { ... }
            if isinstance(n.value, ast.Dict):
                return True
            # return JSONResponse(...) / PlainTextResponse(...)
            if isinstance(n.value, ast.Call) and isinstance(n.value.func, ast.Name):
                if n.value.func.id in {"JSONResponse", "PlainTextResponse"}:
                    return True
    return False

def analyze_file(path: Path):
    issues = []
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        route_decorators = [d for d in node.decorator_list if is_router_call(d)]
        for dec in route_decorators:
            method = dec.func.attr
            line = dec.lineno

            # A) Debe tener operation_id
            if get_kw(dec, "operation_id") is None:
                issues.append(RouteIssue(path, line, "Falta operation_id en el decorador"))

            # B) Debe documentar responses
            if get_kw(dec, "responses") is None:
                issues.append(RouteIssue(path, line, "Faltan responses en el decorador"))

            # C) Reglas específicas DELETE 204
            if method == "delete":
                sc = get_kw(dec, "status_code")
                if sc and kw_is_204(sc):
                    # Si es 204, response_model debe ser None y NO debe retornar JSON
                    rm = get_kw(dec, "response_model")
                    if rm is not None and not value_is_none(rm):
                        issues.append(RouteIssue(path, line, "DELETE 204 con response_model != None"))
                    if returns_dict(node):
                        issues.append(RouteIssue(path, line, "DELETE 204 retorna JSON/cuerpo"))
    return issues

def main():
    roots = [Path("app/booking/routes")]
    files = []
    for r in roots:
        files.extend(r.rglob("*.py"))

    all_issues = []
    for f in files:
        all_issues.extend(analyze_file(f))

    if all_issues:
        print("❌ Validación de rutas FALLÓ:\n")
        for i in all_issues:
            print(i)
        print("\nSugerencia: agrega operation_id, responses y respeta 204 sin cuerpo.")
        sys.exit(1)
    else:
        print("✅ Validación de rutas OK.")
        sys.exit(0)

if __name__ == "__main__":
    main()
