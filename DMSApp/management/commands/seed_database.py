from django.core.management.base import BaseCommand
from DMSApp.utils.seeding_scripts import seed_database_parallel # Import your function
import os


class Command(BaseCommand):
    help = 'Seeds the database with documents and entities from the specified data folder.'

    def add_arguments(self, parser):
        # Add an optional argument for the data folder path
        parser.add_argument(
            '--data_folder',
            type=str,
            default="data/",
            help='Path to the folder containing the data files (default: "data/").'
        )
        parser.add_argument(
            '--workers',
            type=int,
            default=4,
            help='Number of parallel workers to use for processing (default: 4).'
        )

    def handle(self, *args, **kwargs):
        # Read arguments
        data_folder = kwargs['data_folder']
        max_workers = kwargs['workers']

        # Validate the data folder
        if not os.path.isdir(data_folder):
            self.stderr.write(f"Error: The specified data folder '{data_folder}' does not exist.")
            return

        # Call the seeding function
        self.stdout.write(f"Starting database seeding from folder: {data_folder} with {max_workers} workers...")
        try:
            seed_database_parallel(data_folder=data_folder, max_workers=max_workers)
            self.stdout.write("Database seeding completed successfully.")
        except Exception as e:
            self.stderr.write(f"An error occurred during seeding: {e}")
