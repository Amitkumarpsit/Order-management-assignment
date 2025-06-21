import time
import threading
from order_management import (
    OrderManagement,
    OrderRequest,
    RequestType,
    OrderResponse,
    ResponseType
)

def simulate_orders(om: OrderManagement):
    orders = [
        OrderRequest(m_symbolId=1, m_price=100.5, m_qty=10, m_side='B', m_orderId=1, m_requestType=RequestType.New),
        OrderRequest(m_symbolId=1, m_price=101.0, m_qty=20, m_side='S', m_orderId=2, m_requestType=RequestType.New),
        OrderRequest(m_symbolId=1, m_price=99.5, m_qty=15, m_side='B', m_orderId=1, m_requestType=RequestType.Modify),
        OrderRequest(m_symbolId=1, m_price=0, m_qty=0, m_side='S', m_orderId=2, m_requestType=RequestType.Cancel),
        OrderRequest(m_symbolId=1, m_price=105.0, m_qty=5, m_side='B', m_orderId=3, m_requestType=RequestType.New),
    ]

    for req in orders:
        om.onData(req)
        time.sleep(0.2)  # simulate delay between requests

    time.sleep(2)  # simulate delay for responses
    responses = [
        OrderResponse(m_orderId=1, m_responseType=ResponseType.Accept),
        OrderResponse(m_orderId=3, m_responseType=ResponseType.Reject)
    ]
    for resp in responses:
        om.onDataResponse(resp)

if __name__ == "__main__":
    # Allow 24x7 for testing instead of fixed 10:00-13:00
    from datetime import time as dtime
    om = OrderManagement(max_orders_per_sec=2, start_time=dtime(0, 0), end_time=dtime(23, 59))
    
    threading.Thread(target=simulate_orders, args=(om,), daemon=False).start()
