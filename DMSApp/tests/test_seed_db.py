import pytest
from unittest.mock import patch, mock_open, MagicMock
import os
from datetime import datetime
from bs4 import BeautifulSoup
from DMSApp.models import Document, Entity
from DMSApp.utils.seeding_scripts import normalize_text, parse_html, parse_json, process_file, seed_database_parallel

# Mock Django models for testing
@pytest.fixture
def mock_document():
    return MagicMock(spec=Document)

@pytest.fixture
def mock_entity():
    return MagicMock(spec=Entity)


def test_normalize_text():
    assert normalize_text("ação") == "acao"
    assert normalize_text("café") == "cafe"
    assert normalize_text("São João") == "Sao Joao"
    assert normalize_text("") == ""


@patch("builtins.open", new_callable=mock_open, read_data="<html><body><td>Processo:</td><td>12345</td></body></html>")
def test_parse_html(mock_file):
    metadata, main_text = parse_html("test.html")
    assert metadata["process_number"] == "12345"
    assert main_text == ""


@patch("builtins.open", new_callable=mock_open, read_data='{"entities": [{"name": "Entity1", "label": "Label1", "url": "http://example.com"}]}')
def test_parse_json(mock_file):
    entities = parse_json("test.json")
    assert len(entities["entities"]) == 1
    assert entities["entities"][0]["name"] == "Entity1"
    assert entities["entities"][0]["label"] == "Label1"


@patch("os.path.exists", return_value=True)
@patch("builtins.open", side_effect=[
    mock_open(read_data="<html><body><td>Processo:</td><td>12345</td></body></html>").return_value,
    mock_open(read_data='{"entities": [{"name": "Entity1", "label": "Label1", "url": "http://example.com"}]}').return_value
])
def test_process_file(mock_open, mock_exists):
    document, entities = process_file("test.html", "data")
    assert document.process_number == "12345"
    assert len(entities) == 1
    assert entities[0].name == "Entity1"
    assert entities[0].label == "Label1"


@pytest.mark.django_db
@patch("os.listdir", return_value=["test1.html", "test2.html"])
@patch("DMSApp.utils.seeding_scripts.process_file", side_effect=[
    # Simulate one valid file and one invalid file
    (MagicMock(spec=Document, process_number="12345"), [
        MagicMock(spec=Entity, name="Entity1", label="Label1", url="http://example.com")
    ]),
    (None, [])  # Simulate an invalid file returning no data
])
@patch("DMSApp.models.Document.objects.create")
@patch("DMSApp.models.Document.objects.get")
@patch("DMSApp.models.Entity.objects.create")
def test_seed_database_parallel(
    mock_create_entity, mock_get_document, mock_create_document, mock_process_file, mock_listdir
):
    # Mock Document.objects.get to return the created document
    mock_document = MagicMock(spec=Document, process_number="12345")
    mock_get_document.return_value = mock_document

    # Call the function
    seed_database_parallel(data_folder="data")

    # Debugging: Print mock call arguments to verify behavior
    print("Document Mock Call Args:", mock_create_document.call_args_list)
    print("Entity Mock Call Args:", mock_create_entity.call_args_list)

    # Assert Document.objects.create was called for the valid document
    assert mock_create_document.call_count == 1, "Expected Document.objects.create to be called once."

    # Assert Entity.objects.create was called for the associated entity
    assert mock_create_entity.call_count == 1, "Expected Entity.objects.create to be called once."