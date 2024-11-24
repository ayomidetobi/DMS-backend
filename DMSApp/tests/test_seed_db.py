import pytest
import os
import json
from datetime import date
from unittest.mock import mock_open, patch, MagicMock
from bs4 import BeautifulSoup
from django.db import IntegrityError

from DMSApp.models import Document, Entity
from DMSApp.utils.seeding_scripts import (
    convert_date_to_standard_format,
    extract_metadata_and_text_from_html,
    load_json_file,
    process_html_and_json_files,
    populate_database_with_files
)

@pytest.fixture
def sample_html_content():
    return """
    <table>
        <tr><td>Processo:</td><td>123/2024</td></tr>
        <tr><td>Relator:</td><td>Supreme Court</td></tr>
        <tr><td>Descritores:</td><td>Criminal Law</td></tr>
        <tr><td>Data do Acordão:</td><td>15-03-2024</td></tr>
        <tr><td>Decisão:</td><td>Approved</td></tr>
        <tr><td>Sumário:</td><td>Case Summary</td></tr>
        <tr><td>Decisão Texto Integral:</td><td>This is the main text of the decision.</td></tr>
    </table>
    """

@pytest.fixture
def sample_json_content():
    return {
        "entities": [
            {
                "name": "John Doe",
                "label": "PERSON",
                "url": "http://example.com/john"
            }
        ]
    }

class TestDateConverter:
    @pytest.mark.parametrize("input_date,expected", [
        ("15-03-2024", date(2024, 3, 15)),
        ("invalid-date", None),
        ("", None),
        (None, None),
    ])
    def test_convert_date_to_standard_format(self, input_date, expected):
        result = convert_date_to_standard_format(input_date)
        assert result == expected

class TestMetadataExtraction:
    def test_successful_extraction(self, sample_html_content):
        with patch("builtins.open", mock_open(read_data=sample_html_content)):
            with patch("os.path.exists") as mock_exists:
                mock_exists.return_value = True
                metadata, main_text = extract_metadata_and_text_from_html("dummy.html")

        assert metadata["process_number"] == "123/2024"
        assert metadata["tribunal"] == "Supreme Court"
        assert metadata["descriptors"] == "Criminal Law"
        assert metadata["date"] == "15-03-2024"
        assert metadata["decision"] == "Approved"
        assert metadata["summary"] == "Case Summary"
        assert main_text == "This is the main text of the decision."

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            extract_metadata_and_text_from_html("nonexistent.html")

    def test_missing_metadata_fields(self):
        incomplete_html = "<table><tr><td>Processo:</td><td>123/2024</td></tr></table>"
        with patch("builtins.open", mock_open(read_data=incomplete_html)):
            with patch("os.path.exists") as mock_exists:
                mock_exists.return_value = True
                metadata, main_text = extract_metadata_and_text_from_html("dummy.html")

        assert metadata["process_number"] == "123/2024"
        assert metadata["tribunal"] == ""
        assert main_text == ""

class TestJsonLoading:
    def test_successful_json_load(self, sample_json_content):
        with patch("builtins.open", mock_open(read_data=json.dumps(sample_json_content))):
            with patch("os.path.exists") as mock_exists:
                mock_exists.return_value = True
                result = load_json_file("dummy.json")

        assert result == sample_json_content

    def test_file_not_found(self):
        result = load_json_file("nonexistent.json")
        assert result == {}

    def test_invalid_json(self):
        with patch("builtins.open", mock_open(read_data="invalid json")):
            with patch("os.path.exists") as mock_exists:
                mock_exists.return_value = True
                result = load_json_file("dummy.json")

        assert result == {}

class TestFileProcessing:
    @pytest.fixture
    def mock_document_model(self):
        return MagicMock()

    def test_successful_processing(self, sample_html_content, sample_json_content, mock_document_model):
        mock_file = mock_open(read_data=sample_html_content)
        mock_json = mock_open(read_data=json.dumps(sample_json_content))
        
        def side_effect(filename, *args, **kwargs):
            if filename.endswith('.html'):
                return mock_file.return_value
            return mock_json.return_value

        with patch("builtins.open", side_effect=side_effect):
            with patch("os.path.exists") as mock_exists:
                mock_exists.return_value = True
                with patch('bs4.BeautifulSoup', return_value=BeautifulSoup(sample_html_content, 'html.parser')):
                    document, entities = process_html_and_json_files("test.html", "data/")

        assert document is not None
        assert document.process_number == "123/2024"
        assert len(entities) == 1
        assert entities[0].name == "John Doe"


@pytest.mark.django_db
class TestDatabasePopulation:
    @pytest.fixture
    def mock_document_objects(self):
        mock = MagicMock()
        mock.get.return_value = MagicMock(spec=Document)
        return mock

    @pytest.fixture
    def mock_entity_objects(self):
        return MagicMock()

    def test_successful_population(self, sample_html_content, sample_json_content, 
                                 mock_document_objects, mock_entity_objects):
        mock_file = mock_open(read_data=sample_html_content)
        mock_json = mock_open(read_data=json.dumps(sample_json_content))

        def side_effect(filename, *args, **kwargs):
            if filename.endswith('.html'):
                return mock_file.return_value
            return mock_json.return_value

        with patch("os.listdir") as mock_listdir:
            with patch("builtins.open", side_effect=side_effect):
                with patch("os.path.exists") as mock_exists:
                    with patch('bs4.BeautifulSoup', return_value=BeautifulSoup(sample_html_content, 'html.parser')):
                        with patch.object(Document.objects, 'create', return_value=MagicMock(spec=Document)) as mock_create:
                            mock_listdir.return_value = ["test.html"]
                            mock_exists.return_value = True

                            populate_database_with_files("data/", max_workers=1)

                            # Check if the document was created successfully
                            mock_create.assert_called_once()


    @pytest.mark.parametrize("error_type", [
        FileNotFoundError,
        Exception,
    ])
    def test_error_handling(self, error_type, mock_document_objects):
        with patch("os.listdir") as mock_listdir:
            with patch("builtins.open") as mock_open:
                mock_listdir.return_value = ["test.html"]
                if error_type == json.JSONDecodeError:
                    mock_open.side_effect = json.JSONDecodeError("Invalid JSON", "doc", 0)
                else:
                    mock_open.side_effect = error_type()

                with patch.object(Document.objects, 'create') as mock_create:
                    populate_database_with_files("data/", max_workers=1)
                    mock_create.assert_not_called()

    def test_json_decode_error_handling(self, mock_document_objects):
        with patch("os.listdir") as mock_listdir:
            with patch("builtins.open") as mock_open:
                mock_listdir.return_value = ["test.html"]
                mock_open.side_effect = json.JSONDecodeError("Invalid JSON", "doc", 0)

                with patch.object(Document.objects, 'create') as mock_create:
                    populate_database_with_files("data/", max_workers=1)
                    mock_create.assert_not_called()