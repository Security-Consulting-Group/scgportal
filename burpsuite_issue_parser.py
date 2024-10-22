import xml.etree.ElementTree as ET
import json
import sys
import os
from datetime import datetime
from collections import defaultdict

def safe_find(element, tag):
    found = element.find(tag)
    return found.text if found is not None else None

def format_date(date_string):
    try:
        date_obj = datetime.strptime(date_string, "%a %b %d %H:%M:%S %Z %Y")
        return date_obj.strftime("%Y-%m-%d")
    except ValueError:
        return date_string

def parse_xml_to_json(xml_string):
    root = ET.fromstring(xml_string)
    export_time = root.get('exportTime')
    formatted_export_time = format_date(export_time) if export_time else None
    
    grouped_issues = defaultdict(lambda: {
        'type': None,
        'name': None,
        'host': None,
        'instances': []
    })

    for issue in root.findall('.//issue'):
        issue_type = safe_find(issue, 'type')
        issue_name = safe_find(issue, 'name')
        issue_host = safe_find(issue, 'host')
        
        key = (issue_type, issue_name, issue_host)
        
        issue_data = {
            'path': safe_find(issue, 'path'),
            'location': safe_find(issue, 'location'),
            'severity': safe_find(issue, 'severity'),
            'confidence': safe_find(issue, 'confidence'),
            'issueDetail': safe_find(issue, 'issueDetail'),
            'requests': [req.text for req in issue.findall('.//request') if req.text is not None]
        }
        
        grouped_issues[key]['type'] = issue_type
        grouped_issues[key]['name'] = issue_name
        grouped_issues[key]['host'] = issue_host
        grouped_issues[key]['instances'].append(issue_data)

    return json.dumps({
        'exportTime': formatted_export_time,
        'issues': list(grouped_issues.values())
    }, indent=2)

def main():
    if len(sys.argv) != 2:
        print("Usage: python burpsuite_issue_parser.py <path_to_xml_file>")
        sys.exit(1)

    xml_file_path = sys.argv[1]

    if not os.path.exists(xml_file_path):
        print(f"Error: File '{xml_file_path}' does not exist.")
        sys.exit(1)

    try:
        with open(xml_file_path, 'r', encoding='utf-8') as file:
            xml_string = file.read()

        json_output = parse_xml_to_json(xml_string)

        output_file_path = os.path.splitext(xml_file_path)[0] + '.json'
        with open(output_file_path, 'w', encoding='utf-8') as file:
            file.write(json_output)

        print(f"Conversion completed successfully.")
        print(f"Input XML file: {xml_file_path}")
        print(f"Output JSON file: {output_file_path}")
        print(f"Total characters in JSON output: {len(json_output)}")
        
        json_data = json.loads(json_output)
        print(f"Number of unique issue types: {len(json_data['issues'])}")
        print(f"Export Time: {json_data['exportTime']}")

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()