import logging

import jwt
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.core.cache import cache
from rest_framework.reverse import reverse
from .models import Chest
from .serializers import ChestSerializer, ChestOpenSerializer
from apps.saga.saga_orchestrator import start_purchase
from apps.chest.tasks import open_chest_task

logger = logging.getLogger(__name__)


class ChestListView(generics.ListAPIView):
    serializer_class = ChestSerializer

    def get_queryset(self):
        return Chest.objects.all().prefetch_related('product')

    def list(self, request, *args, **kwargs):
        cache_key = "chest:public:active"
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data)

        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        cache.set(cache_key, serializer.data, timeout=60 * 5)  # Cache for 5 minutes

        return Response(serializer.data)


class ChestDetailView(generics.RetrieveAPIView):
    queryset = Chest.objects.all()
    serializer_class = ChestSerializer

    def retrieve(self, request, *args, **kwargs):
        item_id = kwargs.get("pk")
        cache_key = f"chest:detail:{item_id}"

        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

        response = super().retrieve(request, *args, **kwargs)

        cache.set(cache_key, response.data, timeout=60 * 10)

        return response


class ChestBuyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, chest_id):
        user = request.user

        if not user.id:
            return Response(
                {"error": "ID пользователя отсутствует или неверный"},
                status=status.HTTP_400_BAD_REQUEST
            )

        chest = get_object_or_404(Chest, id=chest_id)
        if not chest.check_daily_purchase_limit(user.id):
            return Response(
                {"error": "Превышен дневной лимит для этого сундука"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            transaction = start_purchase(
                user_id=user.id,
                chest_id=chest.id,
                cost=chest.cost,
                currency_type=chest.currency_type,
                promotion_id=chest.promotion.id if chest.promotion else None
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
            "status_url": status_url
        }, status=status.HTTP_202_ACCEPTED)


class OpenChestView(APIView):

    @swagger_auto_schema(
        operation_summary="Open chests",
        operation_description="Open chests in inventory",
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
