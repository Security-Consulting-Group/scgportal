import os
import django
import json
import multiprocessing
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from datetime import datetime
import time
from tqdm import tqdm
from functools import partial

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.development")
django.setup()

from signatures.models import Signature

def convert_date(date_string):
    if not date_string:
        return None
    try:
        return datetime.strptime(date_string, '%Y/%m/%d').date()
    except ValueError:
        return None

def process_chunk(chunk_file, scanner_type, batch_update_time):
    with open(chunk_file, 'r') as file:
        data = json.load(file)
    
    processed_count = 0
    error_count = 0
    
    with transaction.atomic():
        for entry in data:
            try:
                # Change risk_factor to "Informational" if it's None
                risk_factor = entry.get('risk_factor')
                if risk_factor == "None":
                    risk_factor = "Informational"
                    
                Signature.objects.update_or_create(
                    id=entry['id'],
                    defaults={
                        'plugin_name': entry.get('plugin_name', '')[:1000],
                        'risk_factor': risk_factor[:50],
                        'description': entry.get('description', ''),
                        'solution': entry.get('solution', ''),
                        'synopsis': entry.get('synopsis', ''),
                        'see_also': entry.get('see_also', ''),
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
                        'scanner_type': scanner_type,
                        'scg_last_update': batch_update_time,
                        'agent': entry.get('agent', ''),
                        'cvss3_base_score': entry.get('cvss3_base_score'),
                        'cvss3_vector': entry.get('cvss3_vector', '')[:255],
                        'xref': json.dumps(entry.get('xref', [])),
                    }
                )
                processed_count += 1
            except Exception as e:
                error_count += 1
                print(f"Error processing signature with ID: {entry.get('id', 'Unknown')}: {str(e)}")
    
    os.remove(chunk_file)
    return processed_count, error_count

class Command(BaseCommand):
    help = 'Upload signatures from a JSON file using sharding'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='Path to the JSON file')
        parser.add_argument('scanner_type', type=str, help='Type of scanner')
        parser.add_argument('--chunk_size', type=int, default=1000, help='Number of signatures per chunk')
        parser.add_argument('--max_workers', type=int, default=multiprocessing.cpu_count(), help='Max number of worker processes')

    def handle(self, *args, **options):
        json_file_path = options['json_file']
        scanner_type = options['scanner_type']
        chunk_size = options['chunk_size']
        max_workers = options['max_workers']

        self.stdout.write(self.style.SUCCESS(f"Starting sharded signature upload from {json_file_path}"))

        start_time = time.time()
        batch_update_time = timezone.now()

        try:
            with open(json_file_path, 'r') as file:
                data = json.load(file)

            total_entries = len(data)
            self.stdout.write(self.style.SUCCESS(f"Total entries in JSON file: {total_entries}"))

            # Create tempshardsigs folder if it doesn't exist
            shard_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tempshardsigs')
            os.makedirs(shard_folder, exist_ok=True)
            self.stdout.write(self.style.SUCCESS(f"Using shard folder: {shard_folder}"))

            # Create chunks
            chunks = []
            for i in range(0, total_entries, chunk_size):
                chunk = data[i:i+chunk_size]
                chunk_file = os.path.join(shard_folder, f'temp_chunk_{i}.json')
                with open(chunk_file, 'w') as f:
                    json.dump(chunk, f)
                chunks.append(chunk_file)

            # Process chunks in parallel
            process_chunk_partial = partial(process_chunk, scanner_type=scanner_type, batch_update_time=batch_update_time)
            with multiprocessing.Pool(max_workers) as pool:
                results = list(tqdm(
                    pool.imap(process_chunk_partial, chunks),
                    total=len(chunks),
                    desc="Processing chunks"
                ))

            # Aggregate results
            total_processed = sum(r[0] for r in results)
            total_errors = sum(r[1] for r in results)

            end_time = time.time()
            duration = end_time - start_time

            self.stdout.write(self.style.SUCCESS(f"Processed signatures in {duration:.2f} seconds"))
            self.stdout.write(self.style.SUCCESS(f"Processed: {total_processed}, Errors: {total_errors}"))
            self.stdout.write(self.style.SUCCESS(f"Total signatures in database: {Signature.objects.count()}"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred during the upload process: {str(e)}"))
        finally:
            # Cleanup: remove any remaining shard files
            for chunk_file in chunks:
                if os.path.exists(chunk_file):
                    os.remove(chunk_file)
            self.stdout.write(self.style.SUCCESS("Cleaned up temporary shard files."))