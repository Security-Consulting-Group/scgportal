import os
import json
import multiprocessing
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from datetime import datetime
import time
from tqdm import tqdm
from functools import partial
from django.conf import settings
import ijson 

def convert_date(date_string):
    if not date_string:
        return None
    try:
        return datetime.strptime(date_string, '%Y/%m/%d').date()
    except ValueError:
        return None

def process_chunk(entries, batch_update_time):
    # Import the model here to ensure it's available in this process
    from signatures.models import NessusSignature

    processed_count = 0
    error_count = 0

    with transaction.atomic():
        for entry in entries:
            try:
                risk_factor = entry.get('risk_factor')
                if risk_factor == "None":
                    risk_factor = "Informational"

                NessusSignature.objects.update_or_create(
                    id=entry['id'],
                    defaults={
                        'name': entry.get('plugin_name', '')[:1000],
                        'risk_factor': risk_factor[:20],
                        'description': entry.get('description', ''),
                        'solution': entry.get('solution', ''),
                        'synopsis': entry.get('synopsis', ''),
                        'references': entry.get('see_also', ''),
                        'plugin_modification_date': convert_date(entry.get('plugin_modification_date')),
                        'cvss_base_score': entry.get('cvss_base_score'),
                        'cvss_vector': entry.get('cvss_vector', '')[:255],
                        'cve': json.dumps(entry.get('cve', [])),
                        'exploitability_ease': entry.get('exploitability_ease', '')[:255],
                        'exploit_code_maturity': entry.get('exploit_code_maturity', '')[:50],
                        'cpe': entry.get('cpe', ''),
                        'vpr_score': entry.get('vpr_score'),
                        'epss_score': entry.get('epss_score'),
                        'family_name': entry.get('family_name', '')[:255],
                        'scanner_type': 'Nessus',
                        'scg_last_update': batch_update_time,
                        'agent': entry.get('agent', ''),
                        'cvss3_base_score': entry.get('cvss3_base_score'),
                        'cvss3_vector': entry.get('cvss3_vector', '')[:255],
                        'xref': json.dumps(entry.get('xref', [])),
                    }
                )
                processed_count += 1
                if processed_count % 100 == 0:
                    print(f"Processed {processed_count} signatures")
            except Exception as e:
                error_count += 1
                print(f"Error processing signature with ID: {entry.get('id', 'Unknown')}: {str(e)}")

    return processed_count, error_count

class Command(BaseCommand):
    help = 'Upload Nessus signatures from a JSON file using streaming'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='Path to the JSON file')
        parser.add_argument('--batch_size', type=int, default=100, help='Number of signatures per batch')

    def handle(self, *args, **options):
        json_file_path = options['json_file']
        batch_size = options['batch_size']

        self.stdout.write(self.style.SUCCESS(f"Starting streaming Nessus signature upload from {json_file_path}"))

        start_time = time.time()
        batch_update_time = timezone.now()
        
        total_processed = 0
        total_errors = 0
        current_batch = []

        try:
            # Count total items first
            self.stdout.write(self.style.SUCCESS("Counting total items..."))
            total_items = sum(1 for _ in open(json_file_path, 'r')) - 2  # subtract 2 for the array brackets
            self.stdout.write(self.style.SUCCESS(f"Total items to process: {total_items}"))

            # Process the file in streaming mode
            with open(json_file_path, 'rb') as file:
                parser = ijson.items(file, 'item')
                
                for entry in tqdm(parser, total=total_items, desc="Processing signatures"):
                    current_batch.append(entry)
                    
                    if len(current_batch) >= batch_size:
                        processed, errors = process_chunk(current_batch, batch_update_time)
                        total_processed += processed
                        total_errors += errors
                        current_batch = []
                        
                        self.stdout.write(self.style.SUCCESS(
                            f"Progress: {total_processed}/{total_items} "
                            f"({(total_processed/total_items*100):.2f}%)"
                        ))

                # Process remaining items
                if current_batch:
                    processed, errors = process_chunk(current_batch, batch_update_time)
                    total_processed += processed
                    total_errors += errors

            end_time = time.time()
            duration = end_time - start_time

            self.stdout.write(self.style.SUCCESS(f"Processed Nessus signatures in {duration:.2f} seconds"))
            self.stdout.write(self.style.SUCCESS(f"Processed: {total_processed}, Errors: {total_errors}"))

            # Show final count
            from signatures.models import NessusSignature
            self.stdout.write(self.style.SUCCESS(
                f"Total Nessus signatures in database: {NessusSignature.objects.count()}"
            ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred during the upload process: {str(e)}"))