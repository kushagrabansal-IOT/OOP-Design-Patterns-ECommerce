"""
OOP-Design-Patterns-ECommerce
Design Patterns: Factory, Singleton, Strategy, Observer, Decorator, Command, Builder
Author  : Kushagra Bansal — Project Lab India
Run     : python main.py
"""
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import List, Callable
import threading

# ════════════════════════════════════════════════════════════
# 1. SINGLETON PATTERN — Database Connection
# "Ensure only ONE instance exists"
# ════════════════════════════════════════════════════════════
class DatabaseConnection:
    """Thread-safe Singleton using double-checked locking"""
    _instance = None
    _lock     = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.url        = "mongodb://localhost:27017/ecommerce"
            self.connected  = True
            self.queries    = 0
            self._initialized = True

    def execute(self, query):
        self.queries += 1
        return f"Query #{self.queries}: {query}"

    @classmethod
    def reset(cls):
        cls._instance = None

    def __repr__(self):
        return f"DB(url={self.url!r}, queries={self.queries})"


# ════════════════════════════════════════════════════════════
# 2. FACTORY PATTERN — Product Creation
# "Create objects without specifying exact class"
# ════════════════════════════════════════════════════════════
class Product(ABC):
    def __init__(self, name, price):
        self.name  = name
        self.price = price
        self.id    = f"P{id(self)%10000:04d}"

    @abstractmethod
    def get_category(self): pass
    @abstractmethod
    def calculate_shipping(self): pass

    def __str__(self):
        return f"[{self.get_category()}] {self.name} — ₹{self.price:,.2f}"

class Electronics(Product):
    def __init__(self, name, price, warranty_yr):
        super().__init__(name, price)
        self.warranty = warranty_yr
    def get_category(self): return "Electronics"
    def calculate_shipping(self): return 99 if self.price < 5000 else 0

class Clothing(Product):
    def __init__(self, name, price, size):
        super().__init__(name, price)
        self.size = size
    def get_category(self): return "Clothing"
    def calculate_shipping(self): return 49

class Books(Product):
    def __init__(self, name, price, author):
        super().__init__(name, price)
        self.author = author
    def get_category(self): return "Books"
    def calculate_shipping(self): return 29

class ProductFactory:
    """Factory — client code doesn't know which class is instantiated"""
    _creators = {
        "electronics": lambda d: Electronics(d["name"], d["price"], d.get("warranty",1)),
        "clothing":    lambda d: Clothing(d["name"], d["price"], d.get("size","M")),
        "books":       lambda d: Books(d["name"], d["price"], d.get("author","Unknown")),
    }

    @classmethod
    def create(cls, product_type: str, **kwargs) -> Product:
        creator = cls._creators.get(product_type.lower())
        if not creator:
            raise ValueError(f"Unknown product type: {product_type}")
        return creator(kwargs)

    @classmethod
    def register(cls, type_name: str, creator: Callable):
        """Open/Closed: register new types without modifying factory"""
        cls._creators[type_name] = creator


# ════════════════════════════════════════════════════════════
# 3. STRATEGY PATTERN — Payment Processing
# "Define a family of algorithms, encapsulate each one"
# ════════════════════════════════════════════════════════════
class PaymentStrategy(ABC):
    @abstractmethod
    def pay(self, amount: float, metadata: dict) -> dict:
        pass

    @abstractmethod
    def get_name(self) -> str:
        pass

class UPIPayment(PaymentStrategy):
    def pay(self, amount, metadata):
        upi_id = metadata.get("upi_id","user@upi")
        txn    = f"UPI{datetime.now().microsecond:08d}"
        print(f"  💳 UPI: ₹{amount:,.2f} via {upi_id} | TXN: {txn}")
        return {"status":"SUCCESS","txn":txn,"method":"UPI"}

    def get_name(self): return "UPI"

class CreditCardPayment(PaymentStrategy):
    def pay(self, amount, metadata):
        last4  = str(metadata.get("card_number",""))[-4:].rjust(4,'X')
        txn    = f"CC{datetime.now().microsecond:08d}"
        print(f"  💳 Credit Card: ₹{amount:,.2f} | Card: XXXX-XXXX-XXXX-{last4} | TXN: {txn}")
        return {"status":"SUCCESS","txn":txn,"method":"CreditCard"}

    def get_name(self): return "Credit Card"

class WalletPayment(PaymentStrategy):
    def __init__(self, balance=5000):
        self._balance = balance

    def pay(self, amount, metadata):
        if amount > self._balance:
            return {"status":"FAILED","error":"Insufficient wallet balance"}
        self._balance -= amount
        txn = f"WL{datetime.now().microsecond:08d}"
        print(f"  👜 Wallet: ₹{amount:,.2f} | Remaining: ₹{self._balance:,.2f} | TXN: {txn}")
        return {"status":"SUCCESS","txn":txn,"method":"Wallet"}

    def get_name(self): return "Wallet"

class CODPayment(PaymentStrategy):
    def pay(self, amount, metadata):
        print(f"  🏠 COD: ₹{amount:,.2f} to be collected on delivery")
        return {"status":"PENDING","method":"COD"}

    def get_name(self): return "Cash on Delivery"


# ════════════════════════════════════════════════════════════
# 4. OBSERVER PATTERN — Order Events
# "Define one-to-many dependency between objects"
# ════════════════════════════════════════════════════════════
class OrderEventType(Enum):
    PLACED     = "ORDER_PLACED"
    CONFIRMED  = "ORDER_CONFIRMED"
    SHIPPED    = "ORDER_SHIPPED"
    DELIVERED  = "ORDER_DELIVERED"
    CANCELLED  = "ORDER_CANCELLED"

class OrderObserver(ABC):
    @abstractmethod
    def update(self, event_type: OrderEventType, order_data: dict):
        pass

class EmailObserver(OrderObserver):
    def update(self, event_type, order_data):
        print(f"  📧 EMAIL: {event_type.value} for Order#{order_data['id']} → {order_data['email']}")

class SMSObserver(OrderObserver):
    def update(self, event_type, order_data):
        print(f"  📱 SMS: {event_type.value} notification → {order_data['phone']}")

class InventoryObserver(OrderObserver):
    def update(self, event_type, order_data):
        if event_type == OrderEventType.CONFIRMED:
            print(f"  📦 INVENTORY: Reducing stock for Order#{order_data['id']}")
        elif event_type == OrderEventType.CANCELLED:
            print(f"  📦 INVENTORY: Restoring stock for Order#{order_data['id']}")

class AnalyticsObserver(OrderObserver):
    def __init__(self): self.events = []
    def update(self, event_type, order_data):
        self.events.append({"type":event_type.value,"time":datetime.now().isoformat()})
        print(f"  📊 ANALYTICS: Logged {event_type.value}")

class Order:
    """Observable — notifies all registered observers on state change"""

    def __init__(self, customer_name, email, phone, items):
        self.id            = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.customer      = customer_name
        self.email         = email
        self.phone         = phone
        self.items         = items
        self.status        = OrderEventType.PLACED
        self._observers: List[OrderObserver] = []
        self._payment_result = None

    def subscribe(self, observer: OrderObserver):
        self._observers.append(observer)

    def unsubscribe(self, observer: OrderObserver):
        self._observers.remove(observer)

    def _notify(self, event_type: OrderEventType):
        """Notify ALL observers"""
        data = {"id":self.id, "customer":self.customer,
                "email":self.email, "phone":self.phone,
                "amount":self.get_total()}
        for obs in self._observers:
            obs.update(event_type, data)

    def get_total(self):
        return sum(p.price for p in self.items)

    def place(self):
        self.status = OrderEventType.PLACED
        self._notify(OrderEventType.PLACED)

    def confirm(self, payment_result):
        self._payment_result = payment_result
        self.status = OrderEventType.CONFIRMED
        self._notify(OrderEventType.CONFIRMED)

    def ship(self):
        self.status = OrderEventType.SHIPPED
        self._notify(OrderEventType.SHIPPED)

    def deliver(self):
        self.status = OrderEventType.DELIVERED
        self._notify(OrderEventType.DELIVERED)

    def cancel(self):
        self.status = OrderEventType.CANCELLED
        self._notify(OrderEventType.CANCELLED)


# ════════════════════════════════════════════════════════════
# 5. BUILDER PATTERN — Order Construction
# "Construct complex objects step by step"
# ════════════════════════════════════════════════════════════
class OrderBuilder:
    """Build complex Order object step by step"""

    def __init__(self):
        self._reset()

    def _reset(self):
        self._customer = None; self._email = None; self._phone = None
        self._items = []; self._observers = []
        self._payment = None

    def set_customer(self, name, email, phone):
        self._customer = name; self._email = email; self._phone = phone
        return self

    def add_item(self, product: Product):
        self._items.append(product)
        return self

    def add_observer(self, observer: OrderObserver):
        self._observers.append(observer)
        return self

    def set_payment(self, strategy: PaymentStrategy):
        self._payment = strategy
        return self

    def build(self) -> Order:
        if not all([self._customer, self._email, self._items]):
            raise ValueError("Customer, email, and at least one item required")
        order = Order(self._customer, self._email, self._phone or "", self._items)
        for obs in self._observers:
            order.subscribe(obs)
        self._reset()
        return order


if __name__ == "__main__":
    print("═"*65)
    print("  OOP Design Patterns — E-Commerce Backend")
    print("  Project Lab India")
    print("═"*65)

    # 1. SINGLETON
    print("\n── 1. Singleton Pattern ──")
    db1 = DatabaseConnection()
    db2 = DatabaseConnection()
    print(f"  Same instance: {db1 is db2}")
    db1.execute("SELECT * FROM products")
    db2.execute("SELECT * FROM orders")
    print(f"  Total queries via db2: {db2.queries}")

    # 2. FACTORY
    print("\n── 2. Factory Pattern ──")
    products = [
        ProductFactory.create("electronics", name="iPhone 15",   price=79999, warranty=1),
        ProductFactory.create("clothing",    name="Levis Jeans",  price=2500,  size="M"),
        ProductFactory.create("books",       name="Clean Code",   price=2800,  author="Martin"),
    ]
    for p in products:
        print(f"  {p} | Shipping: ₹{p.calculate_shipping()}")

    # 3. STRATEGY
    print("\n── 3. Strategy Pattern ──")
    payment_strategies = [UPIPayment(), CreditCardPayment(), WalletPayment(10000), CODPayment()]
    for strategy in payment_strategies:
        result = strategy.pay(5000, {"upi_id":"kushagra@upi","card_number":"4111111111111234"})
        print(f"     Result: {result['status']}")

    # 4. OBSERVER + BUILDER
    print("\n── 4. Observer + Builder Pattern ──")
    analytics = AnalyticsObserver()
    order = (OrderBuilder()
             .set_customer("Kushagra Bansal","kushagra@pli.in","9876543210")
             .add_item(products[0])
             .add_item(products[2])
             .add_observer(EmailObserver())
             .add_observer(SMSObserver())
             .add_observer(InventoryObserver())
             .add_observer(analytics)
             .build())

    print(f"\n  Order ID: {order.id} | Total: ₹{order.get_total():,.2f}")
    order.place()
    payment = UPIPayment().pay(order.get_total(), {"upi_id":"kushagra@upi"})
    order.confirm(payment)
    order.ship()
    order.deliver()

    print(f"\n  Analytics captured {len(analytics.events)} events")
    print("  All design patterns demonstrated successfully! ✅")
