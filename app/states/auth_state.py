import reflex as rx
import hashlib
from sqlalchemy import text


class AuthState(rx.State):
    full_name: str = ""
    username: str = ""
    email: str = ""
    password: str = ""
    confirm_password: str = ""
    is_logged_in: bool = False
    current_user: str = ""

    def _hash_password(self, pwd: str) -> str:
        return hashlib.sha256(pwd.encode()).hexdigest()

    @rx.event(background=True)
    async def handle_signup(self):
        if not all([self.full_name, self.username, self.email, self.password]):
            yield rx.toast.error("All fields are required.")
            return
        if self.password != self.confirm_password:
            yield rx.toast.error("Passwords do not match.")
            return
        hashed_password = self._hash_password(self.password)
        async with rx.asession() as session:
            async with session.begin():
                check_query = text(
                    "SELECT id FROM users WHERE username = :username OR email = :email"
                )
                result = await session.execute(
                    check_query, {"username": self.username, "email": self.email}
                )
                if result.first():
                    yield rx.toast.error("Username or email already exists.")
                    return
                insert_query = text("""
                    INSERT INTO users (full_name, username, email, password_hash) 
                    VALUES (:full_name, :username, :email, :password_hash)
                """)
                await session.execute(
                    insert_query,
                    {
                        "full_name": self.full_name,
                        "username": self.username,
                        "email": self.email,
                        "password_hash": hashed_password,
                    },
                )
        async with self:
            self.is_logged_in = True
            self.current_user = self.username
            self.password = ""
            self.confirm_password = ""
            self.email = ""
        yield rx.toast.success("Account created successfully!")
        yield rx.redirect("/dashboard")

    @rx.event(background=True)
    async def handle_login(self):
        if not self.username or not self.password:
            yield rx.toast.error("Username and password are required.")
            return
        hashed_password = self._hash_password(self.password)
        async with rx.asession() as session:
            query = text("SELECT password_hash FROM users WHERE username = :username")
            result = await session.execute(query, {"username": self.username})
            user_data = result.first()
            if user_data and user_data.password_hash == hashed_password:
                async with self:
                    self.is_logged_in = True
                    self.current_user = self.username
                    self.password = ""
                yield rx.toast.success("Login successful!")
                yield rx.redirect("/dashboard")
            else:
                yield rx.toast.error("Invalid username or password.")