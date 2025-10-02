"""
API views for client management.
"""

import logging
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from apps.authentication.permissions import CanManageClients
from .models import Client, ClientContact, ClientNote
from .serializers import (
    ClientListSerializer,
    ClientDetailSerializer,
    ClientCreateUpdateSerializer,
    ClientContactSerializer,
    ClientNoteSerializer,
    ClientStatisticsSerializer,
)
from .services import ClientService, ClientContactService, ClientNoteService

logger = logging.getLogger(__name__)


class ClientViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Client model providing CRUD operations.

    Endpoints:
    - GET    /api/v1/clients/          - List all clients
    - POST   /api/v1/clients/          - Create a new client
    - GET    /api/v1/clients/{id}/     - Retrieve a specific client
    - PUT    /api/v1/clients/{id}/     - Update a client
    - PATCH  /api/v1/clients/{id}/     - Partial update a client
    - DELETE /api/v1/clients/{id}/     - Delete (deactivate) a client
    """

    queryset = Client.objects.all()
    permission_classes = [CanManageClients]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'industry', 'account_manager']
    search_fields = ['company_name', 'contact_email', 'contact_person']
    ordering_fields = ['created_at', 'company_name', 'updated_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """
        Return appropriate serializer based on action.
        """
        if self.action == 'list':
            return ClientListSerializer
        elif self.action == 'retrieve':
            return ClientDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ClientCreateUpdateSerializer
        return ClientDetailSerializer

    def perform_create(self, serializer):
        """
        Create client with created_by field.
        """
        client = serializer.save(created_by=self.request.user)
        logger.info(
            f"Client '{client.company_name}' created by {self.request.user.email}"
        )

    def perform_update(self, serializer):
        """
        Update client with logging.
        """
        client = serializer.save()
        logger.info(
            f"Client '{client.company_name}' updated by {self.request.user.email}"
        )

    def perform_destroy(self, instance):
        """
        Soft delete client by setting status to inactive.
        """
        success = ClientService.deactivate_client(instance, self.request.user)
        if not success:
            logger.error(
                f"Failed to deactivate client '{instance.company_name}'"
            )

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Activate a client.

        POST /api/v1/clients/{id}/activate/
        """
        client = self.get_object()
        success = ClientService.activate_client(client, request.user)

        if success:
            return Response(
                {'status': 'Client activated successfully'},
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {'error': 'Failed to activate client'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """
        Deactivate a client.

        POST /api/v1/clients/{id}/deactivate/
        """
        client = self.get_object()
        success = ClientService.deactivate_client(client, request.user)

        if success:
            return Response(
                {'status': 'Client deactivated successfully'},
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {'error': 'Failed to deactivate client'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def add_subscription(self, request, pk=None):
        """
        Add an Azure subscription to client.

        POST /api/v1/clients/{id}/add_subscription/
        Body: {"subscription_id": "azure-subscription-id"}
        """
        client = self.get_object()
        subscription_id = request.data.get('subscription_id')

        if not subscription_id:
            return Response(
                {'error': 'subscription_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        success = ClientService.add_subscription(
            client,
            subscription_id,
            request.user
        )

        if success:
            return Response(
                {
                    'status': 'Subscription added successfully',
                    'subscription_count': client.subscription_count
                },
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {'error': 'Failed to add subscription'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def remove_subscription(self, request, pk=None):
        """
        Remove an Azure subscription from client.

        POST /api/v1/clients/{id}/remove_subscription/
        Body: {"subscription_id": "azure-subscription-id"}
        """
        client = self.get_object()
        subscription_id = request.data.get('subscription_id')

        if not subscription_id:
            return Response(
                {'error': 'subscription_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        success = ClientService.remove_subscription(
            client,
            subscription_id,
            request.user
        )

        if success:
            return Response(
                {
                    'status': 'Subscription removed successfully',
                    'subscription_count': client.subscription_count
                },
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {'error': 'Failed to remove subscription'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get client statistics.

        GET /api/v1/clients/statistics/
        """
        stats = ClientService.get_client_statistics()
        serializer = ClientStatisticsSerializer(stats)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get', 'post'])
    def contacts(self, request, pk=None):
        """
        Manage client contacts.

        GET  /api/v1/clients/{id}/contacts/ - List contacts
        POST /api/v1/clients/{id}/contacts/ - Add a contact
        """
        client = self.get_object()

        if request.method == 'GET':
            contacts = client.contacts.all()
            serializer = ClientContactSerializer(contacts, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        elif request.method == 'POST':
            serializer = ClientContactSerializer(data=request.data)
            if serializer.is_valid():
                contact = ClientContactService.create_contact(
                    client,
                    serializer.validated_data,
                    request.user
                )
                if contact:
                    return Response(
                        ClientContactSerializer(contact).data,
                        status=status.HTTP_201_CREATED
                    )
                else:
                    return Response(
                        {'error': 'Failed to create contact'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get', 'post'])
    def notes(self, request, pk=None):
        """
        Manage client notes.

        GET  /api/v1/clients/{id}/notes/ - List notes
        POST /api/v1/clients/{id}/notes/ - Add a note
        """
        client = self.get_object()

        if request.method == 'GET':
            notes = client.client_notes.all()
            serializer = ClientNoteSerializer(notes, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        elif request.method == 'POST':
            serializer = ClientNoteSerializer(data=request.data)
            if serializer.is_valid():
                note = ClientNoteService.create_note(
                    client=client,
                    author=request.user,
                    note_type=serializer.validated_data.get('note_type', 'general'),
                    subject=serializer.validated_data['subject'],
                    content=serializer.validated_data['content'],
                    related_report=serializer.validated_data.get('related_report')
                )
                if note:
                    return Response(
                        ClientNoteSerializer(note).data,
                        status=status.HTTP_201_CREATED
                    )
                else:
                    return Response(
                        {'error': 'Failed to create note'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )


class ClientContactViewSet(viewsets.ModelViewSet):
    """
    ViewSet for ClientContact model.
    """
    queryset = ClientContact.objects.all()
    serializer_class = ClientContactSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['client', 'role', 'is_primary']
    search_fields = ['name', 'email']

    def perform_create(self, serializer):
        """
        Create contact with logging.
        """
        contact = serializer.save()
        logger.info(
            f"Contact '{contact.name}' created by {self.request.user.email}"
        )


class ClientNoteViewSet(viewsets.ModelViewSet):
    """
    ViewSet for ClientNote model.
    """
    queryset = ClientNote.objects.all()
    serializer_class = ClientNoteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['client', 'author', 'note_type', 'related_report']
    search_fields = ['subject', 'content']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

    def perform_create(self, serializer):
        """
        Create note with author set to current user.
        """
        note = serializer.save(author=self.request.user)
        logger.info(
            f"Note '{note.subject}' created by {self.request.user.email}"
        )
