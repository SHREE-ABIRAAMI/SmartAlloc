import reflex as rx
from sqlalchemy import text
import hashlib


class AuthState(rx.State):
    is_logged_in: bool = False
    current_user: str = ""

    @rx.event
    async def handle_signup(self, form_data: dict):
        username = form_data.get("username")
        first_name = form_data.get("first_name")
        email = form_data.get("email")
        password = form_data.get("password")
        repeat_password = form_data.get("repeat_password")
        if not all([username, first_name, email, password, repeat_password]):
            yield rx.toast("All fields are required.")
            return
        if password != repeat_password:
            yield rx.toast("Passwords do not match.")
            return
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        async with rx.asession() as session:
            async with session.begin():
                res_username = await session.execute(
                    text("SELECT id FROM users WHERE username = :u"), {"u": username}
                )
                if res_username.first():
                    yield rx.toast("Username already exists.")
                    return
                res_email = await session.execute(
                    text("SELECT id FROM users WHERE email = :e"), {"e": email}
                )
                if res_email.first():
                    yield rx.toast("Email already registered.")
                    return
                await session.execute(
                    text(
                        "INSERT INTO users (username, first_name, email, password) VALUES (:u, :fn, :e, :p)"
                    ),
                    {"u": username, "fn": first_name, "e": email, "p": hashed_password},
                )
                await session.commit()
        self.is_logged_in = True
        self.current_user = username
        yield rx.toast(f"Welcome, {first_name}!")
        yield rx.redirect("/dashboard")

    @rx.event
    async def handle_login(self, form_data: dict):
        username = form_data.get("username")
        password = form_data.get("password")
        if not username or not password:
            yield rx.toast("Username and password are required.")
            return
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        async with rx.asession() as session:
            result = await session.execute(
                text(
                    "SELECT username, first_name FROM users WHERE username = :u AND password = :p"
                ),
                {"u": username, "p": hashed_password},
            )
            user = result.first()
        if user:
            self.is_logged_in = True
            self.current_user = user.username
            yield rx.toast(f"Welcome back, {user.first_name}!")
            yield rx.redirect("/dashboard")
        else:
            yield rx.toast("Invalid username or password.")