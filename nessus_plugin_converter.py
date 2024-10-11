import json

def extract_attributes(plugin):
    attributes = plugin.get('attributes', [])
    extracted = {}
    
    for attr in attributes:
        name = attr.get('attribute_name')
        value = attr.get('attribute_value')
        
        if name in [
            "agent", "cpe", "cve", "cvss3_base_score", "cvss3_vector",
            "cvss_base_score", "cvss_vector", "xref", "plugin_name",
            "description", "synopsis", "risk_factor", "see_also",
            "solution", "epss_score", "vpr_score", "exploitability_ease",
            "exploit_code_maturity", "plugin_modification_date"
        ]:
            if name in ["cve", "xref"]:
                extracted.setdefault(name, []).append(value)
            else:
                extracted[name] = value
    
    # Add id and family_name
    extracted['id'] = plugin.get('id')
    extracted['family_name'] = plugin.get('family_name')
    
    return extracted

def main():
    with open('list_plugins.json', 'r') as f:
        data = json.load(f)
    
    extracted_data = [extract_attributes(plugin) for plugin in data]
    
    with open('output.json', 'w') as f:
        json.dump(extracted_data, f, indent=2)

if __name__ == "__main__":
    main()