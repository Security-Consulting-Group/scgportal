import xml.etree.ElementTree as ET
import json
import sys
import os
from datetime import datetime

# Check if the correct number of arguments is provided
if len(sys.argv) != 2:
    print("Usage: python nessus_report_converter.py <path/file.nessus>")
    sys.exit(1)

# Get the file path from command-line argument
file_path = sys.argv[1]

# Check if the file exists
if not os.path.exists(file_path):
    print(f"Error: File '{file_path}' not found.")
    sys.exit(1)

# Parse the Nessus file
nessus_report = ET.parse(file_path)
root = nessus_report.getroot()

severity_processed_tag = root.find("./Policy/Preferences/ServerPreferences/preference[name='severity_processed']/value").text

alert_reports = []
data = {
    "date": f"{severity_processed_tag[:4]}-{severity_processed_tag[4:6]}-{severity_processed_tag[6:8]}",
    "inventory": root.find(".//preference[name='TARGET']/value").text.strip().split(','),
    "alert_report": alert_reports
}

for host in root.iter('ReportHost'):
    for report_item in host.findall('ReportItem'):
        alert_report = {
            'plugin_id': int(report_item.get('pluginID')),
            # 'solution': report_item.find('solution').text if report_item.find('solution') is not None else 'N/A',
            'target_affected': host.get('name'),
            'os': host.find(".//tag[@name='os']").text if host.find(".//tag[@name='os']") is not None else 'N/A'
        }
        alert_reports.append(alert_report)

# Create 'parsed_report' folder if it doesn't exist
parsed_report_folder = 'parsed_report'
os.makedirs(parsed_report_folder, exist_ok=True)

# Generate output JSON file name with timestamp
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
original_filename = os.path.splitext(os.path.basename(file_path))[0]
output_file = f"{original_filename}_{timestamp}.json"
output_path = os.path.join(parsed_report_folder, output_file)

# Write the JSON data to the output file
with open(output_path, 'w') as f:
    json.dump(data, f, indent=4)

print(f"Data has been saved to {output_path}")