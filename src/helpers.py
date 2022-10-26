import sqlite3
import json
from datetime import datetime


class LOGOUT(Exception):
    """Exception to be raised when the user logs out."""
    pass

############
# DB STUFF #
############


def populate_db(conn: sqlite3.Connection):
    """Populate the database with data from the JSON test_data file.

    Args:
        conn (sqlite3.Connection): Connection to the database.
    """
    with open('assets/test_data.json', 'r') as f:
        data = json.load(f)

    cur = conn.cursor()

    # Create ingredients
    for ingredient in data['ingredients']:
        cur.execute('INSERT INTO Ingredient (id, name, inStock, isTopping, updatedAt) VALUES (?, ?, ?, ?, ?)',
                    (ingredient['id'], ingredient['name'], ingredient['in_stock'], ingredient['is_topping'], datetime.now()))

    # Create products
    for product in data['products']:
        cur.execute('INSERT INTO Product (id, name, price, description, updatedAt) VALUES (?, ?, ?, ?, ?)',
                    (product['id'], product['name'], product['price'], product['description'], datetime.now()))
        for ingredient in product['ingredients']:
            cur.execute('INSERT INTO ProductIngredient (productId, ingredientId, amount, updatedAt) VALUES (?, ?, ?, ?)',
                        (product['id'], ingredient['id'], ingredient['amount'], datetime.now()))

    conn.commit()


def create_tables():
    """Create the database and all tables."""

    conn = sqlite3.connect('database.db')

    c = conn.cursor()

    # Run contents of schema.sql
    with open('assets/schema.sql') as f:
        c.executescript(f.read())

    # Save (commit) the changes
    conn.commit()
    return conn


def get_user_by_email(conn: sqlite3.Connection, email: str) -> dict:
    """Get a user by their email.

    Args:
        email (str): Email of the user.

    Returns:
        dict: User data.
    """

    c = conn.cursor()
    c.execute("SELECT * FROM User WHERE email = ?", (email,))
    return c.fetchone()

########
# MISC #
########


def prompt_from_list(choices: list, prompt: str = 'Please choose an option: ') -> int:
    """Prompt the user with a list of choices.

    Args:
        choices (list): List of choices.
        prompt (str, optional): Prompt to display. Defaults to 'Please choose an option: '.

    Returns:
        int: Index of the selected choice.
    """

    while True:
        print(f"\n{prompt}")
        # Print the choices
        for i, choice in enumerate(choices):
            print(f'[{i+1}] {choice}')

        # Prompt the user
        try:
            choice = int(input("> ").strip())
            if choice >= 1 and choice < len(choices)+1:
                return choice-1
        except ValueError:
            print('Invalid choice. Please try again.')


def prompt_for_string(prompt: str, default: str = "") -> str:
    """Prompt the user for a string.

    Args:
        prompt (str): Prompt to display.

    Returns:
        str: User input.
    """
    p = f"\n{prompt}"
    if default != "":
        p += f" [{default}]"
    print(p)
    c = input("> ")
    if len(c) == 0:
        return default
    return c


def prompt_for_bool(prompt: str, default: bool = True) -> bool:
    """Prompt the user for a boolean.

    Args:
        prompt (str): Prompt to display.

    Returns:
        bool: User input.
    """
    p = input(
        f"\n{prompt} [Y/n] " if default else f"\n{prompt} [y/N] ").strip().lower()

    if default:
        return p != 'n'
    else:
        return p == 'y'
