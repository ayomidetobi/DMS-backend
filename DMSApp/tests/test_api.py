import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from DMSApp.models import Document, Entity
from DMSApp.serializers import DocumentSerializer

@pytest.fixture
def api_client():
    """Fixture to provide an APIClient instance."""
    return APIClient()

@pytest.fixture
def create_documents(db):
    """Fixture to create sample documents with entities."""
    document1 = Document.objects.create(
        process_number="12345",
        tribunal="Supreme Court",
        summary="Summary 1",
        decision="Decision 1",
        date="2023-11-20",
        descriptors="Descriptor 1",
        main_text="Main text 1",
    )
    document2 = Document.objects.create(
        process_number="67890",
        tribunal="High Court",
        summary="Summary 2",
        decision="Decision 2",
        date="2023-11-21",
        descriptors="Descriptor 2",
        main_text="Main text 2",
    )
    Entity.objects.create(document=document1, name="Entity1", label="Label1", url="http://example.com/entity1")
    Entity.objects.create(document=document2, name="Entity2", label="Label2", url="http://example.com/entity2")
    return [document1, document2]

@pytest.mark.django_db
class TestDocumentViewSet:
    """Test suite for DocumentViewSet."""

    def test_list_documents(self, api_client, create_documents):
        """Test listing all documents."""
        url = reverse("document-list")  # Update with your app's namespace if needed
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_retrieve_document(self, api_client, create_documents):
        """Test retrieving a single document."""
        document = create_documents[0]
        url = reverse("document-detail", args=[document.id])
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["process_number"] == document.process_number

    def test_create_document(self, api_client):
        """Test creating a new document."""
        url = reverse("document-list")
        payload = {
            "process_number": "11223",
            "tribunal": "Court of Appeals",
            "summary": "Summary 3",
            "decision": "Decision 3",
            "date": "2023-11-22",
            "descriptors": "Descriptor 3",
            "main_text": "Main text 3",
        }
        response = api_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["process_number"] == payload["process_number"]

    def test_update_document(self, api_client, create_documents):
        """Test updating an existing document."""
        document = create_documents[0]
        url = reverse("document-detail", args=[document.id])
        payload = {
            "process_number": "12345",
            "tribunal": "Updated Tribunal",
            "summary": "Updated Summary",
            "decision": "Updated Decision",
            "date": "2023-11-23",
            "descriptors": "Updated Descriptor",
            "main_text": "Updated Main Text",
        }
        response = api_client.put(url, payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["tribunal"] == payload["tribunal"]

    def test_delete_document(self, api_client, create_documents):
        """Test deleting a document."""
        document = create_documents[0]
        url = reverse("document-detail", args=[document.id])
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Document.objects.filter(id=document.id).exists()

    def test_entities_action(self, api_client, create_documents):
        """Test retrieving entities for a document."""
        document = create_documents[0]
        url = reverse("document-entities", args=[document.id])
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["name"] == "Entity1"

    def test_delete_nonexistent_document(self, api_client):
        """Test deleting a non-existent document."""
        url = reverse("document-detail", args=[9999])  # ID 9999 does not exist
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data["error"] == "Document with the given ID does not exist."

    def test_entities_nonexistent_document(self, api_client):
        """Test retrieving entities for a non-existent document."""
        url = reverse("document-entities", args=[9999])  # ID 9999 does not exist
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data["error"] == "Document with the given ID does not exist."


