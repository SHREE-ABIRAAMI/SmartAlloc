import reflex as rx


class AuthState(rx.State):
    full_name: str = ""
    username: str = ""
    email: str = ""
    password: str = ""

    @rx.event
    def signup(self):
        print(f"Signing up user: {self.full_name}, {self.username}, {self.email}")
        return rx.redirect("/login")

    @rx.event
    def login(self):
        print(f"Logging in user: {self.username}")
        return rx.redirect("/dashboard")