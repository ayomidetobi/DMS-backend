from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.filters import SearchFilter,OrderingFilter
from django.utils.translation import gettext as _

from .models import Document
from .serializers import DocumentSerializer
import hashlib

class DocumentPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = "page_size"  
    max_page_size = 100


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.prefetch_related("entities").all()
    serializer_class = DocumentSerializer
    pagination_class = DocumentPagination
    filter_backends = [SearchFilter,OrderingFilter]
    search_fields = ['main_text', 'summary'] 
    ordering_fields = ['date', 'process_number']
    ordering = ['date'] 
    lookup_field = 'uid'

    @action(detail=True, methods=["get"])
    def entities(self, request, uid=None):
        try:
            document = get_object_or_404(self.queryset, uid=uid)
        except NotFound:
            return Response({"error": "Document with the given ID does not exist."}, status=404)

        serializer = self.get_serializer(document)
        return Response(serializer.data["entities"])

    def destroy(self, request, *args, **kwargs):
        try:
            instance = get_object_or_404(Document, uid=kwargs.get(self.lookup_field))
            self.perform_destroy(instance)
            return Response(
                {"message": "Document deleted successfully."}, status=status.HTTP_204_NO_CONTENT
            )
        except Document.DoesNotExist:
            return Response(
                {"error": "Document with the given ID does not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response(
                {"error": "An unexpected error occurred.", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def perform_destroy(self, instance):
        instance.delete()

    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        document_data = serializer.data

        # Calculate ETag based on the serialized data
        etag = hashlib.md5(str(document_data).encode('utf-8')).hexdigest()

        # Check for the If-None-Match header in the request
        if_none_match = request.headers.get('If-None-Match')

        # If ETag matches, return 304 Not Modified
        if if_none_match == etag:
            return Response(status=status.HTTP_304_NOT_MODIFIED)

        # Otherwise, return the serialized data with ETag header
        response = Response(document_data)
        response['ETag'] = etag

        return response