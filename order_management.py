from dataclasses import dataclass
from enum import Enum
from queue import Queue
import threading
import time
from datetime import datetime, time as dtime

# Define enums
class RequestType(Enum):
    Unknown = 0
    New = 1
    Modify = 2
    Cancel = 3

class ResponseType(Enum):
    Unknown = 0
    Accept = 1
    Reject = 2

# Define data classes
@dataclass
class OrderRequest:
    m_symbolId: int
    m_price: float
    m_qty: int
    m_side: str
    m_orderId: int
    m_requestType: RequestType

@dataclass
class OrderResponse:
    m_orderId: int
    m_responseType: ResponseType

# Order management class
class OrderManagement:
    def __init__(self, max_orders_per_sec=100, start_time=dtime(0, 0), end_time=dtime(23, 59)):
        self.max_orders_per_sec = max_orders_per_sec
        self.order_queue = Queue()
        self.lock = threading.Lock()
        self.start_time = start_time
        self.end_time = end_time
        self.order_send_count = 0
        self.last_reset = time.time()
        self.sent_orders = {}  # order_id -> timestamp

        # Start background thread for sending orders
        threading.Thread(target=self._send_orders, daemon=True).start()
        self._check_and_logon_logout()
  # order_id -> timestamp

        # # Start background thread for sending orders
        # threading.Thread(target=self._send_orders, daemon=True).start()
        # self._check_and_logon_logout()

    def _current_time_allowed(self):
        now = datetime.now().time()
        return self.start_time <= now <= self.end_time

    def _check_and_logon_logout(self):
        def check_time():
            logged_in = False
            while True:
                now = datetime.now().time()
                if self.start_time <= now <= self.end_time:
                    if not logged_in:
                        self.sendLogon()
                        logged_in = True
                else:
                    if logged_in:
                        self.sendLogout()
                        logged_in = False
                time.sleep(1)
        threading.Thread(target=check_time, daemon=True).start()

    def onData(self, request: OrderRequest):
        if not self._current_time_allowed():
            print(f"Order {request.m_orderId} rejected: Outside allowed time")
            return

        with self.lock:
            # Handle Modify and Cancel
            if request.m_requestType in [RequestType.Modify, RequestType.Cancel]:
                found = False
                new_queue = Queue()
                while not self.order_queue.empty():
                    existing_order = self.order_queue.get()
                    if existing_order.m_orderId == request.m_orderId:
                        found = True
                        if request.m_requestType == RequestType.Modify:
                            existing_order.m_price = request.m_price
                            existing_order.m_qty = request.m_qty
                            new_queue.put(existing_order)
                        # Cancel: just skip adding back
                    else:
                        new_queue.put(existing_order)
                self.order_queue = new_queue
                if found:
                    print(f"{request.m_requestType.name} processed for Order ID: {request.m_orderId}")
                return
            # Normal new order
            self.order_queue.put(request)

    def _send_orders(self):
        while True:
            now = time.time()
            if now - self.last_reset >= 1:
                self.order_send_count = 0
                self.last_reset = now
            with self.lock:
                while self.order_send_count < self.max_orders_per_sec and not self.order_queue.empty():
                    order = self.order_queue.get()
                    self.send(order)
                    self.sent_orders[order.m_orderId] = time.time()
                    self.order_send_count += 1
            time.sleep(0.01)

    def onDataResponse(self, response: OrderResponse):
        sent_time = self.sent_orders.pop(response.m_orderId, None)
        if sent_time:
            latency = time.time() - sent_time
            self.log_response(response, latency)

    def log_response(self, response: OrderResponse, latency: float):
        with open("order_responses.log", "a") as f:
            f.write(f"{response.m_orderId},{response.m_responseType.name},{latency:.6f}s\n")

    def send(self, request: OrderRequest):
        print(f"Sent Order: {request.m_orderId}")

    def sendLogon(self):
        print("Logon sent")

    def sendLogout(self):
        print("Logout sent")
