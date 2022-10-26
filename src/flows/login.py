
from datetime import datetime
import re
import sqlite3

import bcrypt
from helpers import get_user_by_email, prompt_for_bool, prompt_for_string, prompt_from_list


def login_flow(conn: sqlite3.Connection) -> dict:
    """Login flow for the user.

    Returns:
        dict: User data.
    """
    print('Welcome to the Pizza Ordering System!')

    if prompt_from_list(['Yes', 'No'], 'Do you already have an account?') == 0:
        # Login
        email = ""
        while True:
            email = prompt_for_string("Please enter your email:")
            if re.match(r"[^@]+@[^@]+\.[^@]+", email):
                break

            print("Invalid email. Please try again.")

        password = ""
        while True:
            password = prompt_for_string("Please enter your password:")
            if len(password) >= 8:
                break

            print("Password must be at least 8 characters long.")

        # Check if the user exists
        user = get_user_by_email(conn, email)

        if not user:
            print("User does not exist. Try again!")
            return login_flow(conn)

        # Check if the password is correct
        if not bcrypt.checkpw(password.encode('utf-8'), user["password"].encode('utf-8')):
            print("Incorrect password. Try again!")
            return login_flow(conn)

        print("Login successful!")
        return user

    else:
        # Register
        first_name = prompt_for_string("Please enter your first name:")
        last_name = prompt_for_string("Please enter your last name:")

        email = ""
        while True:
            email = prompt_for_string("Email:")
            if re.match(r"[^@]+@[^@]+\.[^@]+", email):
                break

            print("Invalid email. Please try again.")

        # Check if the user already exists
        if get_user_by_email(conn, email):
            print("A user with this email already exists! Try again.")
            return login_flow(conn)

        password = ""
        while True:
            password = prompt_for_string("Password:")
            if len(password) >= 8:
                break

            print("Password must be at least 8 characters long.")

        repeat_password = ""
        while True:
            repeat_password = prompt_for_string("Repeat password:")
            if len(repeat_password) < 8:
                print("Password must be at least 8 characters long.")
                continue
            if repeat_password != password:
                print("Passwords do not match. Try again.")
                return login_flow(conn)

            break

        is_admin = prompt_for_bool('!TEST! Create user as admin?')

        # Create the user
        hashed_password = bcrypt.hashpw(
            password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        c = conn.cursor()
        c.execute("INSERT INTO User (email, password, firstName, lastName, isAdmin, updatedAt) VALUES (?, ?, ?, ?, ?, ?)",
                  (email, hashed_password, first_name, last_name, is_admin, datetime.now()))
        conn.commit()

        print("Registration successful!")
        return get_user_by_email(conn, email)
