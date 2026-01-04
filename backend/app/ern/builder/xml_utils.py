from lxml import etree

def E(tag: str, ns: str):
    return f"{{{ns}}}{tag}"

def sub(parent, tag, text=None, ns=None, **attrs):
    if ns is None:
        # Assume ns is in parent
        el = etree.SubElement(parent, tag, **attrs)
    else:
        el = etree.SubElement(parent, E(tag, ns), **attrs)
    if text is not None:
        el.text = str(text)
    return el