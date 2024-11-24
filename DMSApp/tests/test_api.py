import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from DMSApp.models import Document, Entity
from DMSApp.serializers import DocumentSerializer
import uuid

@pytest.mark.django_db
class TestDocumentViewSet:

    @pytest.fixture(autouse=True)
    def setup(self, db):
        self.client = APIClient()
        

        self.document1 = Document.objects.create(
            uid="996dd81b-6324-4e6a-b6c4-2bc3d6c4863f",
            process_number="12345",
            tribunal="Supreme Court",
            summary="Summary 1",
            decision="Decision 1",
            date="2023-11-20",
            descriptors="Descriptor 1",
            main_text="Main text 1",
        )
        
        self.document2 = Document.objects.create(
            uid="6f328a61-8381-4f0a-9328-7e9f92b1e627",
            process_number="67890",
            tribunal="High Court",
            summary="Summary 2",
            decision="Decision 2",
            date="2023-11-21",
            descriptors="Descriptor 2",
            main_text="Main text 2",
        )


        self.entity1 = Entity.objects.create(
            document=self.document1,
            name="Entity1",
            label="Label1",
            url="http://example.com/entity1"
        )
        
        self.entity2 = Entity.objects.create(
            document=self.document2,
            name="Entity2",
            label="Label2",
            url="http://example.com/entity2"
        )


        self.test_payload = {
            "process_number": "11223",
            "tribunal": "Court of Appeals",
            "summary": "Summary 3",
            "decision": "Decision 3",
            "date": "2023-11-22",
            "descriptors": "Descriptor 3",
            "main_text": "Main text 3",
        }


        self.list_url = reverse("document-list")
        self.detail_url = lambda uid: reverse("document-detail", args=[uid])
        self.entities_url = lambda uid: reverse("document-entities", args=[uid])

    def test_list_documents(self):
        response = self.client.get(self.list_url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_retrieve_document(self):
        response = self.client.get(self.detail_url(self.document1.uid))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["process_number"] == self.document1.process_number

    def test_create_document(self):
        response = self.client.post(self.list_url, self.test_payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["process_number"] == self.test_payload["process_number"]

    def test_update_document(self):
        update_payload = {
            "process_number": "12345",
            "tribunal": "Updated Tribunal",
            "summary": "Updated Summary",
            "decision": "Updated Decision",
            "date": "2023-11-23",
            "descriptors": "Updated Descriptor",
            "main_text": "Updated Main Text",
        }
        response = self.client.put(
            self.detail_url(self.document1.uid),
            update_payload,
            format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["tribunal"] == update_payload["tribunal"]

    def test_delete_document(self):

        response = self.client.delete(self.detail_url(self.document1.uid))
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.data["message"] == "Document deleted successfully."
        assert not Document.objects.filter(uid=self.document1.uid).exists()

    def test_entities_action(self):
        response = self.client.get(self.entities_url(self.document1.uid))
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["name"] == "Entity1"

    def test_delete_nonexistent_document(self):
        non_existent_uid = str(uuid.uuid4())
        response = self.client.delete(self.detail_url(non_existent_uid))
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_entities_nonexistent_document(self):
        non_existent_uid = str(uuid.uuid4())
        response = self.client.get(self.entities_url(non_existent_uid))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_list_documents_ordering(self):

        response = self.client.get(f"{self.list_url}?ordering=date")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0]["date"] == "2023-11-20"


        response = self.client.get(f"{self.list_url}?ordering=-process_number")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0]["process_number"] == "67890"

    def test_retrieve_document_with_etag(self):
        """Test retrieving a document with ETag logic."""

        response = self.client.get(self.detail_url(self.document1.uid))
        assert response.status_code == status.HTTP_200_OK
        etag = response["ETag"]

        response = self.client.get(
            self.detail_url(self.document1.uid),
            HTTP_IF_NONE_MATCH=etag
        )
        assert response.status_code == status.HTTP_304_NOT_MODIFIED