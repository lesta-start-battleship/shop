import pytest
from rest_framework.test import APIClient
from django.urls import reverse
from apps.product.models import Product
from apps.chest.models import Chest
from apps.promotion.models import Promotion
from apps.purchase.models import Purchase
from django.utils import timezone
from datetime import timedelta


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(django_user_model):
    user = django_user_model.objects.create_user(username='testuser', password='testpass')
    return user


@pytest.fixture
def auth_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def product():
    return Product.objects.create(name="Test Product", cost=100)


@pytest.fixture
def chest():
    return Chest.objects.create(name="Test Chest", cost=200)


@pytest.fixture
def promotion():
    return Promotion.objects.create(
        name="Promo 1",
        description="Desc",
        start_date=timezone.now(),
        duration=timedelta(days=7),
        manually_disabled=False
    )


@pytest.mark.django_db
def test_create_purchase_item(auth_client, product, user):
    url = reverse("purchase-list-create")
    response = auth_client.post(url, {
        "item": product.id,
        "quantity": 2
    })

    assert response.status_code == 201
    data = response.json()
    assert data["item"] == product.id
    assert data["owner"] == user.id
    assert data["quantity"] == 2
    assert Purchase.objects.count() == 1


@pytest.mark.django_db
def test_create_purchase_chest(auth_client, chest, user):
    url = reverse("purchase-list-create")
    response = auth_client.post(url, {
        "chest": chest.id,
        "quantity": 1
    })

    assert response.status_code == 201
    data = response.json()
    assert data["chest"] == chest.id
    assert data["owner"] == user.id
    assert Purchase.objects.count() == 1


@pytest.mark.django_db
def test_create_purchase_with_promotion(auth_client, product, promotion):
    url = reverse("purchase-list-create")
    response = auth_client.post(url, {
        "item": product.id,
        "promotion": promotion.id,
        "quantity": 1
    })

    assert response.status_code == 201
    data = response.json()
    assert data["promotion"] == promotion.id
    assert data["item"] == product.id


@pytest.mark.django_db
def test_create_purchase_invalid_quantity(auth_client, product):
    url = reverse("purchase-list-create")
    response = auth_client.post(url, {
        "item": product.id,
        "quantity": 0
    })
    assert response.status_code == 400
    assert "Количество должно быть положительным" in str(response.data)


@pytest.mark.django_db
def test_create_purchase_both_item_and_chest(auth_client, product, chest):
    url = reverse("purchase-list-create")
    response = auth_client.post(url, {
        "item": product.id,
        "chest": chest.id,
        "quantity": 1
    })
    assert response.status_code == 400
    assert "Ровно одно из полей item или chest должно быть заполнено" in str(response.data)


@pytest.mark.django_db
def test_create_purchase_none_item_and_chest(auth_client):
    url = reverse("purchase-list-create")
    response = auth_client.post(url, {
        "quantity": 1
    })
    assert response.status_code == 400
    assert "Должен быть указан либо item_id, либо chest_id" in str(response.data)
