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

def process_chunk(chunk_file, batch_update_time):
    # Re-initialize Django for this process
    import django
    django.setup()
    
    # Import the model here to ensure it's available in this process
    from signatures.models import BurpSuiteSignature
    
    with open(chunk_file, 'r') as file:
        data = json.load(file)
    
    processed_count = 0
    error_count = 0
    
    with transaction.atomic():
        for entry in data:
            try:
                BurpSuiteSignature.objects.update_or_create(
                    id=entry['issue_type_id'],
                    defaults={
                        'name': entry['name'],
                        'description': entry['description'],
                        'remediation': entry.get('remediation', ''),
                        'references': entry.get('references', ''),
                        'vulnerability_classifications': entry.get('vulnerability_classifications', ''),
                        'retired': entry.get('retired', False),
                        'scanner_type': 'BurpSuite',
                        'scg_last_update': batch_update_time,
                    }
                )
                processed_count += 1
            except Exception as e:
                error_count += 1
                print(f"Error processing signature with ID: {entry.get('issue_type_id', 'Unknown')}: {str(e)}")
    
    os.remove(chunk_file)
    return processed_count, error_count

class Command(BaseCommand):
    help = 'Upload BurpSuite signatures from a JSON file using sharding'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='Path to the JSON file')
        parser.add_argument('--chunk_size', type=int, default=1000, help='Number of signatures per chunk')
        parser.add_argument('--max_workers', type=int, default=multiprocessing.cpu_count(), help='Max number of worker processes')

    def handle(self, *args, **options):
        json_file_path = options['json_file']
        chunk_size = options['chunk_size']
        max_workers = options['max_workers']

        self.stdout.write(self.style.SUCCESS(f"Starting sharded BurpSuite signature upload from {json_file_path}"))

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
            process_chunk_partial = partial(process_chunk, batch_update_time=batch_update_time)
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

            self.stdout.write(self.style.SUCCESS(f"Processed BurpSuite signatures in {duration:.2f} seconds"))
            self.stdout.write(self.style.SUCCESS(f"Processed: {total_processed}, Errors: {total_errors}"))

            # Import BurpSuiteSignature here for the final count
            from signatures.models import BurpSuiteSignature
            self.stdout.write(self.style.SUCCESS(f"Total BurpSuite signatures in database: {BurpSuiteSignature.objects.count()}"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred during the upload process: {str(e)}"))
        finally:
            # Cleanup: remove any remaining shard files
            for chunk_file in chunks:
                if os.path.exists(chunk_file):
                    os.remove(chunk_file)
            self.stdout.write(self.style.SUCCESS("Cleaned up temporary shard files."))