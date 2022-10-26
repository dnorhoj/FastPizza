import sqlite3
from os import path
from flows.account import account_flow
from flows.order import order_flow
from flows.orders import orders_flow
from flows.login import login_flow
from helpers import create_tables, populate_db, prompt_from_list, LOGOUT

conn: sqlite3.Connection = None  # Will be set


def main_menu_flow(user: dict) -> None:
    """Main menu flow.

    Args:
        user (dict): User data.
    """

    print(user['isAdmin'])

    match prompt_from_list([
        'Account',
        'Order',
        'View past orders',
        *(['Admin', 'Logout'] if user['isAdmin'] else ['Logout']),
        'Exit'
    ], f'Hello {user["firstName"]}, what would you like to do?'):
        case 0:
            account_flow(user, conn)
        case 1:
            order_flow(user, conn)
        case 2:
            orders_flow(user, conn)
        case 3:
            raise LOGOUT
        case 4:
            print("\nGoodbye!")
            exit(0)


def main():
    global conn

    # Database setup
    if not path.exists('database.db'):
        # Database does not exist
        conn = create_tables()
        # Populate the database with test data (Products, Ingredients, etc.)
        populate_db(conn)

    if not conn:
        conn = sqlite3.connect('database.db')

    conn.row_factory = sqlite3.Row

    while True:
        user = login_flow(conn)
        try:
            while True:
                main_menu_flow(user)
        except LOGOUT:
            # Only happens when the user logs out, this makes the user login again
            pass


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
        exit(0)
