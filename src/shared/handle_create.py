from common.models import Stock

def add_common_stock(exchange, symbol, start_date):
    try:
        stock = Stock.objects.get(exchange=exchange, symbol=symbol)
        if stock.purchase_date > start_date:
            stock.purchase_date = start_date
            stock.save()
    except Stock.DoesNotExist:
        new_stock = Stock()
        new_stock.exchange = exchange
        new_stock.symbol = symbol
        new_stock.collection_start_date = start_date
        new_stock.save()

