from prometheus_client import Counter, Gauge

# Сколько золота всего потрачено (по всем транзакциям)
gold_spent_total = Counter(
    'shop_gold_spent_total',
    'Total amount of gold spent in purchases'
)

# Кол-во успешно завершённых покупок (успешных транзакций)
successful_purchases_total = Counter(
    'shop_successful_purchases_total',
    'Total count of successful purchases'
)

# Кол-во неуспешных покупок (FAILED, DECLINED)
failed_purchases_total = Counter(
    'shop_failed_purchases_total',
    'Total count of failed purchases'
)

# Кол-во успешно купленных товаров или сундуков по акции
successful_promo_purchases_total = Counter(
    'shop_successful_promo_purchases_total',
    'Total count of successful promo purchases (products or chests)'
)
