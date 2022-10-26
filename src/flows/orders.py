import sqlite3

from helpers import prompt_from_list


def orders_flow(user: dict, conn: sqlite3.Connection) -> None:
    """Orders flow.
    Args:
        user (dict): User data.
    """

    print("Past orders:")

    cur = conn.cursor()
    cur.execute("""
        SELECT
            o.id, COUNT(oi.id) AS itemsCount, o.createdAt
        FROM `Order` o JOIN `OrderItem` oi ON o.id = oi.orderId
        WHERE
            userId = ?
            AND status = 1
        GROUP BY o.id
        ORDER BY
            o.createdAt DESC
        LIMIT 10
    """, (user["id"],))

    orders = cur.fetchall()

    if len(orders) == 0:
        print("No orders yet.")
        return

    p = prompt_from_list([
        *list(map(lambda order: f"{order['createdAt']} ({order['itemsCount']} items)", orders)),
        "Go back"
    ], "Choose an order to view:")

    if p == len(orders):
        return

    order = orders[p]

    print("Receipt:\n")
    print("--------")
    print(f"Order #{order['id']}")
    print(f"Created at {order['createdAt']}")
    print("Items:")
    cur.execute("""
        SELECT
            p.name, oi.amount, p.price
        FROM `OrderItem` oi JOIN Product p ON oi.productId = p.id
        WHERE
            orderId = ?
    """, (order["id"],))

    items = cur.fetchall()

    for item in items:
        print(f"{item['amount']}x {item['name']} - {item['price']} kr")
    print(
        f"Total: {sum(map(lambda item: item['amount'] * item['price'], items))}")
    print("--------")

    input("\nPress enter to go back.")
