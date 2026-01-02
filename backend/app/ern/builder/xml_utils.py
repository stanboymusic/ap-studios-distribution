from lxml import etree

ERN_NS = "http://ddex.net/xml/ern/43"
NSMAP = {
    None: ERN_NS,
    "xsi": "http://www.w3.org/2001/XMLSchema-instance"
}

def E(tag: str):
    return f"{{{ERN_NS}}}{tag}"

def sub(parent, tag, text=None, **attrs):
    el = etree.SubElement(parent, E(tag), **attrs)
    if text is not None:
        el.text = str(text)
    return el