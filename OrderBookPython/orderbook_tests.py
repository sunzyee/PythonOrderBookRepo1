from unittest import TestCase
from orderbook import *

class OrderBook_Tests(TestCase):

    def test_adding_updating_removing_orders(self):
        # Assert that adding orders works
        order1 = "1568390243|abbb11|a|AAPL|B|100.00000|5"
        order2 = "1568390243|abbb12|a|AAPL|S|200.00000|5"
        order3 = "1568390243|abbb13|a|AAPL|B|150.00000|5"
        order4 = "1568390243|abbb14|a|AAPL|B|150.00000|10"
        order_books = OrderBooks()
        order_books.processOrder(order1)
        order_books.processOrder(order2)
        order_books.processOrder(order3)
        order_books.processOrder(order4)

        order_books.showOrderBooks()  # show orderbooks data

        self.assertEqual(order_books.orderbooks['AAPL'].best_ask.price, 200.00000)
        self.assertEqual(order_books.orderbooks['AAPL'].best_bid.price, 150.00000)
        self.assertEqual(order_books.orderbooks['AAPL'].best_bid.size, 15)

        # Assert that updating an order works
        updated_order4 = "1568390243|abbb14|u|6"
        order_books.processOrder(updated_order4)
        self.assertEqual(order_books.orderbooks['AAPL'].best_bid.price, 150.00000)
        self.assertEqual(order_books.orderbooks['AAPL'].best_bid.size, 11)

        updated_order2 = "1568390243|abbb12|u|9"
        order_books.processOrder(updated_order2)
        self.assertEqual(order_books.orderbooks['AAPL'].best_ask.price, 200.00000)
        self.assertEqual(order_books.orderbooks['AAPL'].best_ask.size, 9)

        # Assert that removing orders works
        removed_order3 = "1568390243|abbb13|c"
        order_books.processOrder(removed_order3)
        self.assertEqual(order_books.orderbooks['AAPL'].best_bid.price, 150.00000)
        self.assertEqual(order_books.orderbooks['AAPL'].best_bid.size, 6)

        removed_order4 = "1568390243|abbb14|c"
        order_books.processOrder(removed_order4)
        self.assertEqual(order_books.orderbooks['AAPL'].best_bid.price, 100.00000)
        self.assertEqual(order_books.orderbooks['AAPL'].best_bid.size, 5)