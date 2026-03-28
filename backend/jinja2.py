from __future__ import annotations
import re
from pathlib import Path

class FileSystemLoader:
    def __init__(self, root: str): self.root = Path(root)
    def load(self, name: str) -> str: return (self.root / name).read_text(encoding="utf-8")

def select_autoescape(_types): return True

class Template:
    def __init__(self, env, name, source):
        self.env = env; self.name = name; self.source = source

    def render(self, **context):
        source = self.source
        extends = re.search(r'{%\s*extends\s+"([^"]+)"\s*%}', source)
        if extends:
            base_name = extends.group(1)
            block = re.search(r'{%\s*block\s+content\s*%}(.*?){%\s*endblock\s*%}', source, flags=re.S)
            body = block.group(1) if block else ""
            base = self.env.loader.load(base_name)
            source = re.sub(r'{%\s*block\s+content\s*%}{%\s*endblock\s*%}', body, base, flags=re.S)

        source = re.sub(
            r'{%\s*if\s+([^%]+?)\s*%}(.*?){%\s*endif\s*%}',
            lambda m: m.group(2) if bool(_eval_expr(m.group(1).strip(), context)) else "",
            source,
            flags=re.S
        )
        source = re.sub(
            r'{{\s*(.*?)\s*}}',
            lambda m: "" if (_eval_expr(m.group(1).strip(), context) is None) else str(_eval_expr(m.group(1).strip(), context)),
            source,
            flags=re.S
        )
        return source

class Environment:
    def __init__(self, loader, autoescape=True):
        self.loader = loader; self.autoescape = autoescape
    def get_template(self, name: str): return Template(self, name, self.loader.load(name))

def _eval_expr(expr: str, context: dict):
    expr = expr.strip()
    if "|" in expr:
        base, *filters = [p.strip() for p in expr.split("|")]
        value = _eval_py(base, context)
        for f in filters:
            if f.startswith("default("):
                arg = f[len("default("):-1]
                dv = _eval_py(arg, context)
                if value in (None, "", False): value = dv
            elif f == "upper":
                value = str(value).upper() if value is not None else value
        return value
    return _eval_py(expr, context)

def _eval_py(expr: str, context: dict):
    try:
        return eval(expr, {"__builtins__": {}, "str": str, "int": int, "float": float, "bool": bool}, dict(context))
    except Exception:
        return context.get(expr)
