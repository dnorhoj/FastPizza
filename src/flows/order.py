from datetime import datetime
import sqlite3

from helpers import prompt_for_bool, prompt_for_string, prompt_from_list


def order_flow(user: dict, conn: sqlite3.Connection) -> None:
    """Order flow.
    Args:
        user (dict): User data.
    """

    while True:
        match prompt_from_list([
            'Order a pizza',
            'Place order',
            'Modify order',
            'Clear order items',
            'Go back'
        ], f"{user['firstName']} {user['lastName']}'s orders"):
            case 0:
                order_pizza_flow(user, conn)
            case 1:
                if place_order_flow(user, conn):
                    return
            case 2:
                modify_order_flow(user, conn)
            case 3:
                clear_order_flow(user, conn)
            case 4:
                return


def get_open_order_items(conn: sqlite3.Connection, user_id: int) -> list:
    """Get open order

    Args:
        conn (sqlite3.Connection): Database connection.
        user_id (int): User id.

    Returns:
        list: Orders.
    """

    cur = conn.cursor()
    # Get order item info with product info for open order
    cur.execute("""
        SELECT
            oi.amount, oi.comment, p.name, p.price, o.id as orderId, oi.id as orderItemId
        FROM `Order` o
        JOIN OrderItem oi ON
            o.id = oi.orderId
        JOIN Product p ON
            oi.productId = p.id
        WHERE o.userId = ?
              AND o.status = 0
    """, (user_id,))

    return cur.fetchall()


def get_order_item_toppings(conn: sqlite3.Connection, order_item_id: int) -> list:
    """Get an order item's toppings.

    Args:
        conn (sqlite3.Connection): Database connection.
        order_item_id (int): Order item id.

    Returns:
        list: Order item ingredients.
    """

    cur = conn.cursor()
    cur.execute("""
        SELECT
            i.name,
            t.amount
        FROM IngredientOrderItemTopping t
        JOIN Ingredient i ON
            t.ingredientId = i.id
        WHERE t.orderItemId = ?
    """, (order_item_id,))

    return cur.fetchall()


def order_pizza_flow(user: dict, conn: sqlite3.Connection) -> None:
    """Order pizza flow."""

    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM `Order`
        WHERE userId = ? 
              AND status = 0
    """, (user["id"],))

    # Get open order
    if not (order := cur.fetchone()):
        # If no order exists, create one
        cur.execute("""
            INSERT INTO `Order`
                (userId, status, updatedAt)
            VALUES
                (?, 0, ?)
        """, (user["id"], datetime.now()))
        conn.commit()
        cur.execute("""
            SELECT * FROM `Order`
            WHERE userId = ?
                  AND status = 0
        """, (user["id"],))
        order = cur.fetchone()

    # Get products
    cur.execute("SELECT * FROM Product")
    products = cur.fetchall()

    # Product selection
    while True:
        choice = prompt_from_list(
            [*list(
                map(lambda p: f"{p['price']} kr - {p['name']}\n - {p['description']}", products)
            ), "Cancel"],
            "Select a pizza:"
        )

        # Check if user wants to cancel
        if choice == len(products):
            return

        # Get product amount
        product_amount = prompt_for_string(
            f"How many '{products[choice]['name']}' do you want?", "1")
        try:
            product_amount = int(product_amount)
        except ValueError:
            print("Invalid amount!")
            continue

        # Add toppings
        selected_toppings = []
        if prompt_for_bool("Do you want to add any toppings?", False):
            cur.execute("SELECT * FROM Ingredient WHERE isTopping = 1")
            available_toppings = cur.fetchall()

            while True:
                topping = prompt_from_list(
                    [*list(
                        map(lambda i: f"{i['name']}", available_toppings)
                    ), "Done"],
                    "Select a topping:"
                )

                if topping == len(available_toppings):
                    break

                topping_amount = prompt_for_string(
                    f"How many '{available_toppings[topping]['name']}' do you want?", "1")
                try:
                    topping_amount = int(topping_amount)
                except ValueError:
                    print("Invalid amount!")
                    continue

                if topping_amount * product_amount > available_toppings[topping]["inStock"]:
                    print(
                        f"Not enough {available_toppings[topping]['name']} in stock! ({available_toppings[topping]['inStock']} left)")
                    continue
                elif topping_amount > 10:
                    print("You can't have more than 10 of each topping!")
                    continue

                selected_toppings.append({
                    "ingredientId": available_toppings[topping]["id"],
                    "amount": topping_amount
                })

                print(
                    f"Added {topping_amount}x {available_toppings[topping]['name']} to your {products[choice]['name']}")

        cur.execute("""
            SELECT
                i.id, i.name, i.inStock, pi.amount
            FROM Ingredient i INNER JOIN ProductIngredient pi ON
                i.id = pi.ingredientId
            WHERE i.id IN (
                SELECT
                    pi.ingredientId
                FROM Product p JOIN ProductIngredient pi ON
                    pi.productId = p.id
                WHERE p.id = ?
            )
        """, (products[choice]["id"],))
        ingredients = cur.fetchall()

        # Check if there are enough ingredients in stock, and update stock
        for ingredient in ingredients:
            used_amount = product_amount * ingredient["amount"]
            for extra_topping in selected_toppings:
                if extra_topping["ingredientId"] == ingredient["id"]:
                    used_amount += extra_topping["amount"]

            if ingredient["inStock"] < used_amount:
                print(f"Not enough {ingredient['name']} in stock!")
                return

            cur.execute("""
                UPDATE Ingredient
                SET inStock = inStock - ?
                WHERE id = ?
            """, (used_amount, ingredient["id"]))

        # Order Item comment
        comment = prompt_for_string(
            "Do you want to add a comment? (Leave blank for no comment)", None)

        # Update order
        cur.execute("UPDATE `Order` SET updatedAt = ? WHERE id = ?",
                    (datetime.now(), order["id"]))
        # Add order item to database
        cur.execute("""
            INSERT INTO OrderItem
                (orderId, productId, amount, comment, updatedAt)
            VALUES
                (?, ?, ?, ?, ?)
        """, (order["id"], products[choice]["id"], product_amount, comment, datetime.now()))
        # Add toppings to dabase if any
        if len(selected_toppings) > 0:
            # Get order item id
            cur.execute("SELECT last_insert_rowid() as id")
            order_item_id = cur.fetchone()["id"]
            # Add all toppings to the database
            for topping in selected_toppings:
                cur.execute("""
                    INSERT INTO IngredientOrderItemTopping
                        (orderItemId, ingredientId, amount)
                    VALUES
                        (?, ?, ?)
                """, (order_item_id, topping["ingredientId"], topping["amount"]))

        # Commit transaction
        conn.commit()

        print("Your order has been updated!")

        if not prompt_for_bool("Do you want to add another pizza?", False):
            return


def place_order_flow(user: dict, conn: sqlite3.Connection) -> None:
    """Check order flow."""

    items = get_open_order_items(conn, user['id'])

    # Get open order
    if not items or len(items) == 0:
        print("You haven't added anything to your order yet!")
        return

    print("\nYour order:")
    print("-----------")
    for i in items:
        print(f"{i['amount']}x {i['name']} - {i['price']*i['amount']} kr")
        toppings = get_order_item_toppings(conn, i['orderItemId'])
        for t in toppings:
            print(f"   + {t['amount']}x {t['name']}")
        if i['comment']:
            print(f"   >>: {i['comment']}")

    total_price = sum([i['amount'] * i['price'] for i in items])
    print(f"Total: {total_price} kr")

    if prompt_for_bool("Do you want to place your order?", False):
        cur = conn.cursor()
        cur.execute("UPDATE `Order` SET status = 1 WHERE userId = ? AND status = 0",
                    (user["id"],))
        conn.commit()
        print("Order placed successfully!")
        return True


def modify_order_flow(user: dict, conn: sqlite3.Connection) -> None:
    """Modify open order"""

    items = get_open_order_items(conn, user['id'])

    # Get open order
    if not items or len(items) == 0:
        print("You haven't added anything to your order yet!")
        return

    print("\nWhich item do you want to modify:")
    print("---------------------------------")
    toppings = {}
    for i, it in enumerate(items):
        print(f"[{i+1}] {it['amount']}x {it['name']} - {it['price']*it['amount']} kr")
        toppings[it['orderItemId']] = get_order_item_toppings(
            conn, it['orderItemId'])
        for t in toppings[it['orderItemId']]:
            print(" "*(len(str(i)) + 3) + f"   + {t['amount']}x {t['name']}")
        if it['comment']:
            print((" "*(len(str(i)) + 3)) + f"   >>: {it['comment']}")
    print(f"[{i+2}] Go back")

    try:
        p = int(input("> ").strip())-1
    except ValueError:
        print("Invalid input!")
        return

    if p == len(items):
        return
    elif p > len(items) or p < 0:
        print("Invalid input!")
        return
    item = dict(items[p])

    item_toppings = toppings[item['orderItemId']]
    while True:
        display = f"Modifying:"
        display += f"\n{item['amount']}x {item['name']} - {item['price']*item['amount']} kr"
        for t in item_toppings:
            display += f"\n   + {t['amount']}x {t['name']}"
        if item['comment']:
            display += f"\n   >>: {item['comment']}"

        match prompt_from_list([
            "Remove item",
            "Change amount",
            "Change comment",
            "Go back"
        ], display):
            case 0:  # Remove item
                if not prompt_for_bool("Are you sure you want to remove this item?", False):
                    continue

                cur = conn.cursor()
                cur.execute("DELETE FROM OrderItem WHERE id = ?",
                            (item["orderItemId"],))
                conn.commit()
                print("Item removed from order!")
                break
            case 1:  # Change amount
                amount = None
                while amount is None:
                    amount = prompt_for_string(
                        f"Enter new amount for {item['name']}", item['amount'])

                    try:
                        amount = int(amount)
                    except ValueError:
                        print("Invalid input!")
                        amount = None

                cur = conn.cursor()
                cur.execute("UPDATE OrderItem SET amount = ? WHERE id = ?",
                            (amount, item["orderItemId"]))
                conn.commit()
                item['amount'] = amount
                print("Amount updated!")
            case 2:  # Change comment
                comment = prompt_for_string(
                    "New comment: (leave blank for no comment)", None)
                cur = conn.cursor()
                cur.execute("UPDATE OrderItem SET comment = ? WHERE id = ?",
                            (comment, item["orderItemId"]))
                conn.commit()
                item['comment'] = comment
                print("Comment updated!")
            case 3:  # Go back
                return


def clear_order_flow(user: dict, conn: sqlite3.Connection) -> None:
    """Clear order flow.

    Args:
        user (dict): User data.
    """

    items = get_open_order_items(conn, user["id"])

    if len(items) == 0:
        print("You haven't added anything to your order yet!")
        return

    if prompt_for_bool(f"Are you sure you want to clear {len(items)} items from your order?", False):
        cur = conn.cursor()
        # Delete all OrderItems of current order user has open
        cur.execute("""
            DELETE FROM OrderItem
            WHERE orderId = (
                SELECT id FROM `Order`
                WHERE status = 0
                      AND userId = ?
            )
        """, (user["id"],))
        conn.commit()
        print("Your order has been cleared!")
