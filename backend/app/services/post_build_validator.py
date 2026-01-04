import requests
from lxml import etree
from app.config.ddex import ERN_CONFIG

def validate_xsd(xml_bytes, version, profile):
    config = ERN_CONFIG[(version, profile)]
    schema_url = config["schema"]
    try:
        response = requests.get(schema_url)
        schema_root = etree.fromstring(response.content)
        schema = etree.XMLSchema(schema_root)
        xml_root = etree.fromstring(xml_bytes)
        schema.validate(xml_root)
        return {"valid": True, "errors": []}
    except Exception as e:
        return {"valid": False, "errors": [str(e)]}

def validate_schematron(xml_bytes, profile):
    # Placeholder for Schematron validation
    # In real implementation, load Schematron rules for the profile
    return {"valid": True, "errors": []}

def hash_assets(assets):
    # Placeholder for hashing assets
    return {"hashes": {}}

def validate_zip_integrity(zip_path):
    # Placeholder for ZIP integrity check
    return {"valid": True, "errors": []}

def post_build_validate(xml_bytes, version, profile, assets=None, zip_path=None):
    results = {}
    results["xsd"] = validate_xsd(xml_bytes, version, profile)
    results["schematron"] = validate_schematron(xml_bytes, profile)
    if assets:
        results["hashes"] = hash_assets(assets)
    if zip_path:
        results["zip"] = validate_zip_integrity(zip_path)
    return results