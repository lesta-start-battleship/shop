import logging
import jwt
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status, filters
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.core.cache import cache
from rest_framework.reverse import reverse
from .models import Chest, ChestSettings
from .serializers import ChestSerializer, ChestOpenSerializer, ChestSettingsSerializer
from apps.saga.saga_orchestrator import start_purchase
from apps.chest.tasks import open_chest_task

logger = logging.getLogger(__name__)


class ChestListView(generics.ListAPIView):
    serializer_class = ChestSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_queryset(self):
        return Chest.objects.all().prefetch_related('product')


class ChestDetailView(generics.RetrieveAPIView):
    queryset = Chest.objects.all()
    serializer_class = ChestSerializer
    lookup_field = 'item_id'

    def retrieve(self, request, *args, **kwargs):
        item_id = kwargs.get("item_id")
        cache_key = f"chest:detail:{item_id}"

        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

        response = super().retrieve(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=30)

        return response


class ChestBuyView(APIView):
    def post(self, request, item_id):
        user = request.user

        if not user.id:
            return Response(
                {"error": "ID пользователя отсутствует или неверный"},
                status=status.HTTP_400_BAD_REQUEST
            )
        chest = get_object_or_404(Chest, item_id=item_id)

        if not chest.check_daily_purchase_limit(user.id):
            return Response(
                {"error": "Превышен дневной лимит для этого сундука"},
                status=status.HTTP_400_BAD_REQUEST
            )

        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return Response(
                {"error": "Токен отсутствует или неверный"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        token = auth_header.split(' ')[1]

        try:
            transaction = start_purchase(
                user_id=user.id,
                item_id=chest.item_id,
                cost=chest.cost,
                currency_type=chest.currency_type,
                promotion_id=chest.promotion.id if chest.promotion else None,
                token=token
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        status_url = reverse(
            'transaction-status',
            kwargs={'transaction_id': str(transaction.id)},
            request=request
        )

        return Response({
            "status": "purchase_started",
            "transaction_id": str(transaction.id),
            "status_url": request.build_absolute_uri(status_url)
        }, status=status.HTTP_202_ACCEPTED)


class OpenChestView(APIView):

    @swagger_auto_schema(
        operation_summary="Open chests",
        operation_description="Open chests in inventory",
        request_body=ChestOpenSerializer(),
        responses={202: ChestOpenSerializer(many=True)}
    )
    def post(self, request):

        auth_header = request.META.get('HTTP_AUTHORIZATION', '')

        if not auth_header.startswith('Bearer '):
            return Response(
                {"error": "Invalid authorization header"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        else:
            token = auth_header.strip()

        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            user_id = payload['sub']
        except (jwt.DecodeError, KeyError):
            return Response(
                {"error": "Invalid token format"},
                status=status.HTTP_400_BAD_REQUEST
            )
        logger.info(f"{request.data}")

        serializer_in = ChestOpenSerializer(data=request.data)
        serializer_in.is_valid(raise_exception=True)
        data = serializer_in.validated_data

        chest_id = data.get('item_id')
        amount = data.get('amount')
        callback_url = data.get('callback_url')

        chest = get_object_or_404(Chest, item_id=chest_id)

        logger.info("Send task to open_chest_task")

        task = open_chest_task.delay(
            chest_id=chest_id,
            token=token,
            user_id=user_id,
            callback_url=callback_url,
            amount=amount
        )

        return Response(
            {"task_id": task.id},
            status=status.HTTP_202_ACCEPTED
        )


class ChestSettingsView(APIView):

    @swagger_auto_schema(
        operation_summary="Chest settings",
        operation_description="Create chest settings",
        request_body=ChestSettingsSerializer(),
        responses={201: ChestSettingsSerializer()}
    )
    def post(self, request):
        ChestSettings.objects.all().delete()

        serializer = ChestSettingsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(id=1)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get(self, request):
        settings = ChestSettings.get_solo()
        serializer = ChestSettingsSerializer(settings)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Chest settings",
        operation_description="Update chest settings",
        request_body=ChestSettingsSerializer(),
        responses={200: ChestSettingsSerializer()}
    )
    def put(self, request):
        settings = ChestSettings.get_solo()

        serializer = ChestSettingsSerializer(
            instance=settings,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)
