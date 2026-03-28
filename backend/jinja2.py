"""Very small fallback subset of jinja2 used for local tests/runtime when package is unavailable."""
from __future__ import annotations

import re
from pathlib import Path


class FileSystemLoader:
    def __init__(self, root: str):
        self.root = Path(root)

    def load(self, name: str) -> str:
        return (self.root / name).read_text(encoding="utf-8")


def select_autoescape(_types):
    return True


class Template:
    def __init__(self, env: "Environment", name: str, source: str):
        self.env = env
        self.name = name
        self.source = source

    def render(self, **context) -> str:
        source = self.source

        extends_match = re.search(r'{%\s*extends\s+"([^"]+)"\s*%}', source)
        if extends_match:
            base_name = extends_match.group(1)
            block_match = re.search(r'{%\s*block\s+content\s*%}(.*?){%\s*endblock\s*%}', source, flags=re.S)
            block_content = block_match.group(1) if block_match else ""
            base = self.env.loader.load(base_name)
            source = re.sub(r'{%\s*block\s+content\s*%}{%\s*endblock\s*%}', block_content, base, flags=re.S)

        source = self._render_conditionals(source, context)
        return self._render_vars(source, context)

    def _render_conditionals(self, source: str, context: dict) -> str:
        pattern = re.compile(r'{%\s*if\s+([^%]+?)\s*%}(.*?){%\s*endif\s*%}', re.S)

        def repl(match):
            expr = match.group(1).strip()
            body = match.group(2)
            return body if bool(_eval_expr(expr, context)) else ""

        return pattern.sub(repl, source)

    def _render_vars(self, source: str, context: dict) -> str:
        pattern = re.compile(r'{{\s*(.*?)\s*}}', re.S)

        def repl(match):
            expr = match.group(1).strip()
            value = _eval_expr(expr, context)
            return "" if value is None else str(value)

        return pattern.sub(repl, source)


class Environment:
    def __init__(self, loader: FileSystemLoader, autoescape=True):
        self.loader = loader
        self.autoescape = autoescape

    def get_template(self, name: str) -> Template:
        return Template(self, name, self.loader.load(name))


def _eval_expr(expr: str, context: dict):
    expr = expr.strip()

    if "|" in expr:
        base_expr, *filters = [part.strip() for part in expr.split("|")]
        value = _eval_python(base_expr, context)
        for f in filters:
            if f.startswith("default("):
                arg = f[len("default("):-1]
                default_value = _eval_python(arg, context)
                if value in (None, "", False):
                    value = default_value
            elif f == "upper":
                value = str(value).upper() if value is not None else value
        return value

    return _eval_python(expr, context)


def _eval_python(expr: str, context: dict):
    safe_locals = dict(context)
    safe_globals = {"__builtins__": {}, "str": str, "int": int, "float": float, "bool": bool}
    try:
        return eval(expr, safe_globals, safe_locals)
    except Exception:
        return context.get(expr)
