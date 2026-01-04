import requests

# Endpoints to try
VALIDATOR_ENDPOINTS = [
    "https://ddex-workbench.org/api/validator/ern",
    "https://xml-validator.smecde.com/api/validator/ern"
]

def validate_with_workbench(ern_xml: str, profile: str = "AudioAlbum", version: str = "4.3"):
    last_error = None
    
    for url in VALIDATOR_ENDPOINTS:
        print(f"DEBUG: Trying Workbench Validator at {url}")
        try:
            files = {
                "file": ("ern.xml", ern_xml, "application/xml")
            }
            data = {
                "profile": profile,
                "version": version
            }
            
            # Use minimal headers to avoid triggering WAFs or causing redirects
            response = requests.post(url, files=files, data=data, timeout=20)
            
            print(f"DEBUG: Response from {url} status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    return response.json()
                except:
                    print(f"DEBUG: Response from {url} is not JSON")
                    if "DDEX Workbench" in response.text:
                        print(f"DEBUG: Received HTML landing page from {url}")
            
            last_error = f"Status {response.status_code} from {url}"
            if response.status_code == 403:
                print(f"DEBUG: 403 Forbidden from {url} - might be blocked or require auth")
                
        except Exception as e:
            print(f"DEBUG: Error calling {url}: {str(e)}")
            last_error = str(e)

    # If all failed, return error
    return {
        "status": "error",
        "message": f"All validators failed. Last error: {last_error}",
        "raw_response": "Could not get a valid JSON response from any DDEX validator. Check if the services are up or if the XML is too large."
    }