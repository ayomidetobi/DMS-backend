from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django.utils.translation import gettext as _

from .models import Document
from .serializers import DocumentSerializer


class DocumentPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = "page_size"  
    max_page_size = 100


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.prefetch_related("entities").all()
    serializer_class = DocumentSerializer
    pagination_class = DocumentPagination

    @action(detail=True, methods=["get"])
    def entities(self, request, pk=None):
        try:
            document = get_object_or_404(self.queryset, pk=pk)
        except NotFound:
            return Response({"error": "Document with the given ID does not exist."}, status=404)

        serializer = self.get_serializer(document)
        return Response(serializer.data["entities"])

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
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
