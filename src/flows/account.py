import sqlite3

import bcrypt
from helpers import LOGOUT, prompt_for_bool, prompt_for_string, prompt_from_list


def change_password_flow(user: dict, conn: sqlite3.Connection) -> None:
    """Change password flow.

    Args:
        user (dict): User data.
    """

    password = ""
    while True:
        password = prompt_for_string("Please enter your new password:")
        if len(password) >= 8:
            break
        print("Password must be at least 8 characters long.")

    repeat_password = ""
    while True:
        repeat_password = prompt_for_string("Repeat Password:")
        if len(repeat_password) < 8:
            print("Password must be at least 8 characters long.")
            continue
        if repeat_password != password:
            print("Passwords do not match. Password has not been changed.")
            return change_password_flow(user, conn)

        break

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    cur = conn.cursor()
    cur.execute("UPDATE User SET password = ? WHERE id = ?",
                (hashed_password, user["id"]))
    conn.commit()

    print("Password changed successfully!")

def change_name_flow(user: dict, conn: sqlite3.Connection) -> None:
    """Change name flow.

    Args:
        user (dict): User data.
    """

    first_name = prompt_for_string("New first name:")
    last_name = prompt_for_string("New last name:")

    cur = conn.cursor()
    cur.execute("UPDATE User SET firstName = ?, lastName = ? WHERE id = ?",
                (first_name, last_name, user["id"]))
    conn.commit()

    print("Name changed successfully! Please log in again to see the changes.")

def account_flow(user: dict, conn: sqlite3.Connection) -> None:
    """Account flow.

    Args:
        user (dict): User data.
    """

    while True:
        match prompt_from_list([
            'Change my password',
            'Change my name',
            'Delete my account',
            'Go back',
        ], f"{user['firstName']} {user['lastName']}'s account"):
            case 0:
                change_password_flow(user, conn)
            case 1:
                change_name_flow(user, conn)
            case 2:
                # Delete account
                if prompt_for_bool("Are you sure you want to delete your account?", False):
                    c = conn.cursor()
                    c.execute("DELETE FROM User WHERE id = ?", (user["id"],))
                    conn.commit()
                    raise LOGOUT
            case 3:
                return
