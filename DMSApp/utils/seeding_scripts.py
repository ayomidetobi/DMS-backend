import json
import os
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime

from bs4 import BeautifulSoup
from django.db import IntegrityError, transaction
from django.utils.dateparse import parse_date

from ..models import Document, Entity
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def convert_date_to_standard_format(date_string):
    if not date_string or not isinstance(date_string, str):
        logger.warning("Invalid date input provided.")
        return None
    try:
        return datetime.strptime(date_string, '%d-%m-%Y').date()
    except ValueError:
        logger.error(f"Invalid date format: {date_string}")
        return None

def extract_metadata_and_text_from_html(file_path):

    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        with open(file_path, "r", encoding="utf-8", errors="replace") as file:
            soup = BeautifulSoup(file, "html.parser")

        def get_metadata_value(label):

            label_td = soup.find("td", string=lambda x: x and label in x)
            if not label_td:
                return None
            sibling_td = label_td.find_next_sibling("td")
            if sibling_td:
                return sibling_td.get_text(strip=True, separator=" ").replace("\xa0", " ").strip()
            return None


        metadata = {
            "process_number": get_metadata_value("Processo:"),
            "tribunal": get_metadata_value("Relator:"),
            "descriptors": get_metadata_value("Descritores:"),
            "date": get_metadata_value("Data do Acordão:"),
            "decision": get_metadata_value("Decisão:"),
            "summary": get_metadata_value("Sumário:"),
        }


        metadata = {key: value if value else "" for key, value in metadata.items()}

       
        missing_fields = [key for key, value in metadata.items() if not value]
        if missing_fields:
            logger.warning(
                f"Warning: Missing metadata fields in file {file_path}: {', '.join(missing_fields)}"
            )
        

        main_text_section = soup.find("td", string=lambda x: x and "Decisão Texto Integral:" in x)
        if main_text_section:
            sibling_td = main_text_section.find_next_sibling("td")
            if sibling_td:
                main_text = sibling_td.get_text(strip=True, separator="\n")
            else:
                main_text = ""
        else:
            main_text = ""
        return metadata, main_text
    
    except FileNotFoundError as fnfe:
        logger.error(fnfe)
        raise
    except Exception as e:
        logger.error(f"Error parsing HTML structure in file {file_path}: {e}")
        raise ValueError(f"Error parsing HTML file: {file_path}")


def load_json_file(json_file):
    try:
        if not os.path.exists(json_file):
            raise FileNotFoundError(f"JSON file not found: {json_file}")
        
        with open(json_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError as fnfe:
        logger.error(fnfe)
        return {}
    except json.JSONDecodeError as jde:
        logger.error(f"Error decoding JSON file {json_file}: {jde}")
        return {}


def process_html_and_json_files(file_name, data_folder):

    if file_name.endswith(".html"):
        try:
            html_path = os.path.join(data_folder, file_name)
            metadata, main_text = extract_metadata_and_text_from_html(html_path)
            if not metadata:
                return None, []
            document = Document(
                process_number=metadata["process_number"],
                tribunal=metadata["tribunal"],
                summary=metadata["summary"],
                decision=metadata["decision"],
                date=convert_date_to_standard_format(metadata["date"]),
                descriptors=metadata["descriptors"],
                main_text=main_text,
            )

            json_file = os.path.join(data_folder, file_name.replace(".html", ".json"))
            entities = load_json_file(json_file)["entities"] if os.path.exists(json_file) else []

            entity_list = [
                Entity(
                    document=document,
                    name=entity.get("name", ""),
                    label=entity.get("label", ""),
                    url=entity.get("url", ""),
                )
                for entity in entities
            ]
            return document, entity_list
        except Exception as e:
            logger.error(f"Error processing file {file_name}: {e}")
            return None, []
    logger.warning(f"File {file_name} does not end with '.html'. Skipping.")
    return None, []
def process_file_safely(file, data_folder):
    try:
        return process_html_and_json_files(file, data_folder)
    except Exception as e:
        logger.error(f"Error processing file {file}: {e}")
        return None, []

def populate_database_with_files(data_folder="data/", max_workers=4):
    documents_to_create = []
    entities_to_create = []


    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_html_and_json_files, file, data_folder): file for file in os.listdir(data_folder)}

        for future in as_completed(futures):
            try:
                document, entities = future.result()
                if document:
                    documents_to_create.append(document)
                    entities_to_create.extend(entities)
            except Exception as e:
                logger.error(f"Error processing a file: {e}")


    for doc in documents_to_create:
        try:
            with transaction.atomic():
                Document.objects.create(
                    process_number=doc.process_number,
                    tribunal=doc.tribunal,
                    summary=doc.summary,
                    decision=doc.decision,
                    date=doc.date,
                    descriptors=doc.descriptors,
                    main_text=doc.main_text,
                )
        except IntegrityError:
            logger.warning(f"Document with process_number '{doc.process_number}' already exists. Skipping.")


    for entity in entities_to_create:
        try:
            with transaction.atomic():
                Entity.objects.create(
                    document=Document.objects.get(process_number=entity.document.process_number),
                    name=entity.name,
                    label=entity.label,
                    url=entity.url,
                )
        except IntegrityError:
            logger.warning(f"Entity with name '{entity.name}' already exists. Skipping.")
        except Document.DoesNotExist:
            logger.warning(f"Document for entity '{entity.name}' not found. Skipping.")

    logger.info("Database seeding completed successfully.")

