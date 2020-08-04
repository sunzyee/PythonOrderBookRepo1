import decimal
import logging
import time
from itertools import islice
import functools

log = logging.getLogger(__name__)


class OrderBooks:

    def __init__(self):
        self.orderbooks = {}  # ticker to orderbook mapping
        self.order_orderbook = {}  # order to orderbook mapping

    def showOrderBooks(self):
        """returns the OrderBooks as list of dictionary, which will be used for html display"""
        """All tickers' OrderBooks are combined together in flat structure, which are distinguished by ticker"""
        order_book_data = []
        for k1, v1 in self.orderbooks.items():
            order_book_data.extend(self.orderbooks[k1].showLevels())
        return order_book_data

    def processOrder(self, order):
        """This Function add / update / cancel an order in the order book"""
        """incoming order string format - timestamp|order id|action|ticker|side|price|size """
        orderDetails = order.split('|')

        order_id = orderDetails[1]
        action = orderDetails[2]
        is_bid = True
        size = 0
        price = 0.00000
        ticker = ''
        if action == 'a':
            ticker = orderDetails[3]
            is_bid = True if orderDetails[4] == 'B' else False
            size = (int)(orderDetails[6])
            price = decimal.Decimal(orderDetails[5])
        elif action == 'u':
            size = (int)(orderDetails[3])

        order = Order(order_id, is_bid, size, price)  # init Order object

        # handle action and maintain orderbooks and order_orderbook dictionaries
        if action == 'a':
            if ticker in self.orderbooks:
                order_book = self.orderbooks[ticker]
            else:
                order_book = OrderBook(ticker=ticker)
            order_book.add(order)
            self.orderbooks.update({ticker : order_book})
            self.order_orderbook.update({order_id : order_book})
        elif action == 'u':
            order_book = self.order_orderbook[order_id]
            order_book.update(order)
        elif action == 'c':
            order_book = self.order_orderbook[order_id]
            order_book.remove(order)
            self.order_orderbook.pop(order_id)
            if order_book.best_bid is None and order_book.best_ask is None:
                self.orderbooks.pop(ticker)


class OrderBook:
    """Order Book contains list of Limit/Price Levels"""

    def __init__(self, ticker=None):
        self.ticker = ticker
        self.bids = LimitLevelTree()
        self.asks = LimitLevelTree()
        self.best_bid = None
        self.best_ask = None
        self._price_levels = {}
        self._orders = {}

    @property
    def getBestBidAndAsk(self):
        """Returns the top bid and ask"""
        return self.best_bid, self.best_ask

    def update(self, order):
        """Updates an existing order in the book, also update limit level
        """
        size_diff = self._orders[order.order_id].size - order.size
        self._orders[order.order_id].size = order.size
        self._orders[order.order_id].parent_limit.size -= size_diff

    def remove(self, order):
        """Removes an order from the book, also update limit level
        """
        # Remove Order from self._orders
        try:
            popped_item = self._orders.pop(order.order_id)
        except KeyError:
            return False

        # Remove order from its doubly linked list
        popped_item.pop_from_list()

        # Remove Limit Level from self._price_levels and tree, if no orders are
        # left within that limit level
        try:
            if len(self._price_levels[popped_item.price]) == 0:
                popped_limit_level = self._price_levels.pop(popped_item.price)
                # Remove Limit Level from LimitLevelTree
                if popped_item.is_bid:
                    if popped_limit_level == self.best_bid:
                        if not isinstance(popped_limit_level.parent, LimitLevelTree):
                            self.best_bid = popped_limit_level.parent
                        else:
                            self.best_bid = None

                    popped_limit_level.remove()
                else:
                    if popped_limit_level == self.best_ask:
                        if not isinstance(popped_limit_level.parent, LimitLevelTree):
                            self.best_ask = popped_limit_level.parent
                        else:
                            self.best_ask = None
                    popped_limit_level.remove()
        except KeyError:
            pass

        return popped_item

    def add(self, order):
        """Adds a new LimitLevel to the book and appends the given order to it.
        """
        if order.price not in self._price_levels:
            limit_level = LimitLevel(order)
            self._orders[order.order_id] = order
            self._price_levels[limit_level.price] = limit_level

            if order.is_bid:
                self.bids.insert(limit_level)
                if self.best_bid is None or limit_level.price > self.best_bid.price:
                    self.best_bid = limit_level

            else:
                self.asks.insert(limit_level)
                if self.best_ask is None or limit_level.price < self.best_ask.price:
                    self.best_ask = limit_level
        else:
            # The price level already exists, hence we need to append the order
            # to that price level
            self._orders[order.order_id] = order
            self._price_levels[order.price].append(order)

    def showLevels(self, depth=None):
        """Returns the price levels as a list of dictionaries [ {Ticker=Ticker1, BidQty=BidQty1, BidPrice=BidPrice1, AskPrice=AskPrice1, AskQty=AskQty1},... ]
        """
        levels_data = []
        levels_sorted = sorted(self._price_levels.keys())
        bids_all = reversed([price_level for price_level in levels_sorted if self.best_ask is None or price_level < self.best_ask.price] )
        bids = list(islice(bids_all, depth)) if depth else list(bids_all)
        asks_all = (price_level for price_level in levels_sorted if self.best_bid is None or price_level > self.best_bid.price )
        asks = list(islice(asks_all, depth)) if depth else list(asks_all)

        i = 0
        j = 0
        while i < len(asks) or j < len(bids):
            bid_qty = ""
            bid_price = ""
            ask_qty = ""
            ask_price = ""
            ticker = self.ticker if i == 0 else ""  # only show ticker on top level
            if i < len(asks):
                ask_price = asks[i]
                ask_qty = self._price_levels[ask_price].size
                i = i+1

            if j < len(bids):
                bid_price = bids[j]
                bid_qty = self._price_levels[bid_price].size
                j = j+1

            levels_data.append({'AskQty':ask_qty, 'AskPrice':str(ask_price), 'BidPrice':str(bid_price), 'BidQty':bid_qty, 'Ticker':ticker })
        return levels_data

    def levels(self, depth=None):
        """Returns the price levels as a dict {'bids': [bid1, ...], 'asks': [ask1, ...]}
        """
        levels_sorted = sorted(self._price_levels.keys())
        bids_all = reversed([price_level for price_level in levels_sorted if self.best_ask is None or price_level < self.best_ask.price])
        bids = list(islice(bids_all, depth)) if depth else list(bids_all)
        asks_all = (price_level for price_level in levels_sorted if self.best_bid is None or price_level > self.best_bid.price)
        asks = list(islice(asks_all, depth)) if depth else list(asks_all)
        levels_dict = {
            'bids': [self._price_levels[price] for price in bids],
            'asks': [self._price_levels[price] for price in asks],
        }
        return levels_dict


class LimitLevel:
    """Binary Search Tree node.
    """
    __slots__ = ['price', 'size', 'parent', 'left_child',
                 'right_child', 'head', 'tail', 'count', 'orders']

    def __init__(self, order):
        """Initialize a Node() instance.
        """
        # Data Values
        self.price = order.price
        self.size = order.size

        # BST Attributes
        self.parent = None
        self.left_child = None
        self.right_child = None

        # Doubly-Linked-list attributes
        self.orders = OrderList(self)
        self.append(order)

    @property
    def is_root(self):
        return isinstance(self.parent, LimitLevelTree)

    @property
    def volume(self):
        return self.price * self.size

    @property
    def balance_factor(self):
        """factor to check if tree is balanced
        """
        right_height = self.right_child.height if self.right_child else 0
        left_height = self.left_child.height if self.left_child else 0

        return right_height - left_height

    @property
    def grandparent(self):
        try:
            if self.parent:
                return self.parent.parent
            else:
                return None
        except AttributeError:
            return None

    @property
    def height(self):
        """Calculates the height of the tree up to this Node.
        """
        left_height = self.left_child.height if self.left_child else 0
        right_height = self.right_child.height if self.right_child else 0
        if left_height > right_height:
            return left_height + 1
        else:
            return right_height + 1

    @property
    def min(self):
        """Returns the smallest node under this node.
        """
        minimum = self
        while minimum.left_child:
            minimum = minimum.left_child
        return minimum

    def append(self, order):
        """Append to double linked list.
        """
        return self.orders.append(order)

    def _replace_node_in_parent(self, new_value=None):
        """Replaces Node in parent on a delete() call.
        """
        if not self.is_root:
            if self == self.parent.left_child:
                self.parent.left_child = new_value
            else:
                self.parent.right_child = new_value
        if new_value:
            new_value.parent = self.parent

    def remove(self):
        """Deletes this limit level.
        """

        if self.left_child and self.right_child:
            # We have two kids
            succ = self.right_child.min

            # Swap Successor and current node
            self.left_child, succ.left_child = succ.left_child, self.left_child
            self.right_child, succ.right_child = succ.right_child, self.right_child
            self.parent, succ.parent = succ.parent, self.parent
            self.remove()
            self.balance_grandparent()
        elif self.left_child:
            # Only left child
            self._replace_node_in_parent(self.left_child)
        elif self.right_child:
            # Only right child
            self._replace_node_in_parent(self.right_child)
        else:
            # No children
            self._replace_node_in_parent(None)

    def balance_grandparent(self):
        """Checks if our grandparent needs rebalancing.
        """
        if self.grandparent and self.grandparent.is_root:
            # If our grandpa is root, we do nothing.
            pass
        elif self.grandparent and not self.grandparent.is_root:
            # Tell the grandpa to check his balance.
            self.grandparent.balance()
        elif self.grandparent is None:
            # We don't have a grandpa!
            pass
        else:
            # Unforeseen things have happened. D:
            raise NotImplementedError

        return

    def balance(self):
        """rotate nodes to balance the tree
        """
        if self.balance_factor > 1:
            # right is heavier
            if self.right_child.balance_factor < 0:
                # right_child.left is heavier, RL case
                self._rl_case()
            elif self.right_child.balance_factor > 0:
                # right_child.right is heavier, RR case
                self._rr_case()
        elif self.balance_factor < -1:
            # left is heavier
            if self.left_child.balance_factor < 0:
                # left_child.left is heavier, LL case
                self._ll_case()
            elif self.left_child.balance_factor > 0:
                # left_child.right is heavier, LR case
                self._lr_case()
        else:
            pass

        # Now check upwards
        if not self.is_root and not self.parent.is_root:
            self.parent.balance()

    def _ll_case(self):
        """Rotate Nodes for LL Case.
        """
        child = self.left_child

        if self.parent.is_root or self.price > self.parent.price:
            self.parent.right_child = child
        else:
            self.parent.left_child = child

        child.parent, self.parent = self.parent, child
        child.right_child, self.left_child = self, child.right_child

    def _rr_case(self):
        """Rotate Nodes for RR Case.
        """
        child = self.right_child

        if self.parent.is_root or self.price > self.parent.price:
            self.parent.right_child = child
        else:
            self.parent.left_child = child

        child.parent, self.parent = self.parent, child
        child.left_child, self.right_child = self, child.left_child

    def _lr_case(self):
        """Rotate Nodes for LR Case.
        """
        child, grand_child = self.left_child, self.left_child.right_child
        child.parent, grand_child.parent = grand_child, self
        child.right_child = grand_child.left_child
        self.left_child, grand_child.left_child = grand_child, child
        self._ll_case()

    def _rl_case(self):
        """Rotate Nodes for RL case.
        """
        child, grand_child = self.right_child, self.right_child.left_child
        child.parent, grand_child.parent = grand_child, self
        child.left_child = grand_child.right_child
        self.right_child, grand_child.right_child = grand_child, child
        self._rr_case()

    def __str__(self):
        if not self.is_root:
            s = 'Node Value: %s\n' % self.price
            s += 'Node left_child value: %s\n' % (self.left_child.price if self.left_child else 'None')
            s += 'Node right_child value: %s\n\n' % (self.right_child.price if self.right_child else 'None')
        else:
            s = ''

        left_side_print = self.left_child.__str__() if self.left_child else ''
        right_side_print = self.right_child.__str__() if self.right_child else ''
        return s + left_side_print + right_side_print

    def __len__(self):
        return len(self.orders)


class LimitLevelTree:
    """Binary Search Tree Root Node.
    """
    __slots__ = ['right_child', 'is_root']

    def __init__(self):
        # BST Attributes
        self.right_child = None
        self.is_root = True

    def insert(self, limit_level):
        """Insert to the tree
        """
        current_node = self
        while True:
            if current_node.is_root or limit_level.price > current_node.price:
                if current_node.right_child is None:
                    current_node.right_child = limit_level
                    current_node.right_child.parent = current_node
                    current_node.right_child.balance_grandparent()
                    break
                else:
                    current_node = current_node.right_child
                    continue
            elif limit_level.price < current_node.price:
                if current_node.left_child is None:
                    current_node.left_child = limit_level
                    current_node.left_child.parent = current_node
                    current_node.left_child.balance_grandparent()
                    break
                else:
                    current_node = current_node.left_child
                    continue
            else:
                # The level already exists
                break


class OrderList:
    """Double Linked List Container Class.
    """
    __slots__ = ['head', 'tail', 'parent_limit', 'count']

    def __init__(self, parent_limit):
        self.head = None
        self.tail = None
        self.count = 0
        self.parent_limit = parent_limit

    def __len__(self):
        return self.count

    def append(self, order):
        """Appends an order to this List.
        Automatically update head and tail if it's the first order in this list.
        """
        if not self.tail:
            order.root = self
            self.tail = order
            self.head = order
            self.count += 1
        else:
            self.tail.append(order)


class Order:
    """Double-Linked List Order item.
    """
    __slots__ = ['order_id', 'is_bid', 'size', 'price', 'timestamp',
                 'next_item', 'previous_item', 'root']

    def __init__(self, order_id, is_bid, size, price, root=None,
                 timestamp=None, next_item=None, previous_item=None):
        # Data Values
        self.order_id = order_id
        self.is_bid = is_bid
        self.price = price
        self.size = size
        self.timestamp = timestamp if timestamp else time.time()

        # DLL Attributes
        self.next_item = next_item
        self.previous_item = previous_item
        self.root = root

    @property
    def parent_limit(self):
        return self.root.parent_limit

    def append(self, order):
        """Append an order.
        """
        if self.next_item is None:
            self.next_item = order
            self.next_item.previous_item = self
            self.next_item.root = self.root

            # Update Root Statistics in OrderList root obj
            self.root.count += 1
            self.root.tail = order

            self.parent_limit.size += order.size

        else:
            self.next_item.append(order)

    def pop_from_list(self):
        """Pops this item from the DoublyLinkedList it belongs to.
        """
        if self.previous_item is None:
            # We're head
            self.root.head = self.next_item
            if self.next_item:
                self.next_item.previous_item = None

        if self.next_item is None:
            # We're tail
            self.root.tail = self.previous_item
            if self.previous_item:
                self.previous_item.next_item = None

        # Update the Limit Level and root
        self.root.count -= 1
        self.parent_limit.size -= self.size

        return self.__repr__()

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return str((self.order_id, self.is_bid, self.price, self.size, self.timestamp))

