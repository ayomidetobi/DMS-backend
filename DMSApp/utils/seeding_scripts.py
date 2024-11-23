from datetime import datetime
import json
import os
import unicodedata
from concurrent.futures import ThreadPoolExecutor

from bs4 import BeautifulSoup
from django.db import IntegrityError, transaction
from django.utils.dateparse import parse_date

from ..models import Document, Entity


def normalize_text(text):
    if text:
        return unicodedata.normalize("NFKD", text).encode("ASCII", "ignore").decode("utf-8")
    return text
def parse_custom_date(date_string):
    try:
        return datetime.strptime(date_string, '%d-%m-%Y').date()
    except ValueError:
        print(f"Invalid date format: {date_string}")
        return None

def parse_html(file_path):

    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as file:
            soup = BeautifulSoup(file, "html.parser")

        def get_metadata_value(label):

            normalized_label = normalize_text(label)
            label_td = soup.find("td", text=lambda x: x and normalized_label in normalize_text(x))
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
            print(
                f"Warning: Missing metadata fields in file {file_path}: {', '.join(missing_fields)}"
            )
        

        main_text_section = soup.find("td", text=lambda x: x and "Decisão Texto Integral:" in x)
        print("Found main_text_section:", main_text_section is not None)
        if main_text_section:
            sibling_td = main_text_section.find_next_sibling("td")
            if sibling_td:
                main_text = sibling_td.get_text(strip=True, separator="\n")
            else:
                main_text = ""
        else:
            main_text = ""
        return metadata, main_text
    
    except Exception as e:
        raise ValueError(f"Error parsing HTML structure in file {file_path}: {e}")


def parse_json(json_file):

    with open(json_file, "r", encoding="utf-8") as f:
        return json.load(f)


def process_file(file_name, data_folder):

    if file_name.endswith(".html"):
        try:
            html_path = os.path.join(data_folder, file_name)
            metadata, main_text = parse_html(html_path)

            document = Document(
                process_number=metadata["process_number"],
                tribunal=metadata["tribunal"],
                summary=metadata["summary"],
                decision=metadata["decision"],
                date=parse_custom_date(metadata["date"]),
                descriptors=metadata["descriptors"],
                main_text=main_text,
            )

            json_file = os.path.join(data_folder, file_name.replace(".html", ".json"))
            entities = parse_json(json_file)["entities"] if os.path.exists(json_file) else []

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
            print(f"Error processing file {file_name}: {e}")
            return None, []
    return None, []


def seed_database_parallel(data_folder="data/", max_workers=4):
    """
    Parallel version of the seeder for faster processing of large datasets.
    Handles uniqueness errors gracefully.
    """
    documents_to_create = []
    entities_to_create = []


    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = executor.map(
            lambda file: process_file(file, data_folder), os.listdir(data_folder)
        )

    for document, entities in results:
        if document:
            documents_to_create.append(document)
            entities_to_create.extend(entities)


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
            print(f"Document with process_number '{doc.process_number}' already exists. Skipping.")


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
            print(f"Entity with name '{entity.name}' already exists. Skipping.")
        except Document.DoesNotExist:
            print(f"Document for entity '{entity.name}' not found. Skipping.")

    print("Database seeding completed successfully.")
