import reflex as rx
from app.states.auth_state import AuthState


def animated_background() -> rx.Component:
    return rx.el.div(
        class_name="fixed top-0 left-0 w-full h-screen z-[-1] bg-[#0d1117]"
    )


def container(*children, **props):
    class_name = props.pop("class_name", "")
    return rx.el.div(
        animated_background(),
        *children,
        class_name=f"relative flex flex-col items-center justify-center min-h-screen font-['Poppins'] p-4 text-white w-full {class_name}",
        **props,
    )


def glass_card(*children, **props):
    class_name = props.pop("class_name", "")
    return rx.el.div(
        *children,
        class_name=f"bg-[#1c2128] p-8 rounded-2xl border border-gray-700 shadow-lg {class_name}",
        **props,
    )


def auth_input(placeholder: str, name: str, input_type: str = "text") -> rx.Component:
    return rx.el.input(
        placeholder=placeholder,
        name=name,
        type=input_type,
        class_name="w-full px-4 py-3 rounded-lg border border-gray-600 bg-[#0d1117] focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all duration-300 text-white",
        style={"font_family": "'Quicksand', sans-serif"},
    )


def auth_button(text: str, on_click: rx.event.EventType | None = None) -> rx.Component:
    return rx.el.button(
        rx.icon("sparkles", class_name="mr-2"),
        text,
        on_click=on_click,
        type="submit",
        class_name="w-full flex items-center justify-center mt-4 px-8 py-3 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 text-white font-bold text-lg hover:from-blue-700 hover:to-purple-700 transition-all duration-300 ease-in-out shadow-lg hover:shadow-xl transform hover:-translate-y-1",
        style={"font_family": "'Poppins', sans-serif"},
    )


def index() -> rx.Component:
    return container(
        rx.el.div(
            rx.el.h1(
                "SmartAlloc",
                class_name="text-7xl font-bold text-white tracking-wide",
                style={"font_family": "'Montserrat Alternates', sans-serif"},
            ),
            rx.el.p(
                "An AI-Powered Timetable Generator and Academic Chatbot Assistant",
                class_name="text-lg text-gray-400 mt-4 max-w-2xl text-center font-['Quicksand']",
            ),
            rx.el.a(
                rx.el.button(
                    "Get Started",
                    class_name="mt-8 px-8 py-3 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 text-white font-bold text-lg hover:from-blue-700 hover:to-purple-700 transition-all duration-300 ease-in-out shadow-lg hover:shadow-xl transform hover:-translate-y-1",
                    style={"font_family": "'Poppins', sans-serif"},
                ),
                href="/login",
            ),
            class_name="flex flex-col items-center justify-center text-center p-8 z-10 min-h-screen",
        )
    )


def login() -> rx.Component:
    return container(
        glass_card(
            rx.el.h2(
                "Login",
                class_name="text-3xl font-bold text-white text-center mb-6",
                style={"font_family": "'Poppins', sans-serif"},
            ),
            rx.el.form(
                rx.el.div(
                    auth_input("Username", "username"),
                    auth_input("Password", "password", input_type="password"),
                    auth_button("Login"),
                    class_name="space-y-4",
                ),
                on_submit=AuthState.handle_login,
                reset_on_submit=True,
            ),
            rx.el.div(
                rx.el.a(
                    "Forgot password?",
                    href="#",
                    class_name="text-sm text-gray-400 hover:text-blue-500",
                ),
                rx.el.a(
                    "Sign Up",
                    href="/signup",
                    class_name="text-sm text-blue-500 font-bold hover:underline",
                ),
                class_name="flex justify-between items-center mt-6",
            ),
            width="100%",
            max_width="28rem",
        ),
        class_name="w-full justify-center",
    )


def signup() -> rx.Component:
    return container(
        glass_card(
            rx.el.h2(
                "Sign Up",
                class_name="text-3xl font-bold text-white text-center mb-6",
                style={"font_family": "'Poppins', sans-serif"},
            ),
            rx.el.form(
                rx.el.div(
                    auth_input("First Name", "first_name"),
                    auth_input("Username", "username"),
                    auth_input("Email", "email", input_type="email"),
                    auth_input("Password", "password", input_type="password"),
                    auth_input(
                        "Confirm Password", "repeat_password", input_type="password"
                    ),
                    auth_button("Sign Up"),
                    class_name="space-y-4",
                ),
                on_submit=AuthState.handle_signup,
                reset_on_submit=True,
            ),
            rx.el.div(
                rx.el.a(
                    "Already have an account? Login",
                    href="/login",
                    class_name="text-sm text-blue-500 font-bold hover:underline",
                ),
                class_name="text-center mt-6",
            ),
            width="100%",
            max_width="28rem",
        ),
        class_name="w-full justify-center",
    )


app = rx.App(
    stylesheets=["/animations.css"],
    head_components=[
        rx.el.link(rel="preconnect", href="https://fonts.googleapis.com"),
        rx.el.link(rel="preconnect", href="https://fonts.gstatic.com", cross_origin=""),
        rx.el.link(
            href="https://fonts.googleapis.com/css2?family=Montserrat+Alternates:wght@400;700&family=Poppins:wght@400;600;700&family=Quicksand:wght@400;500;600;700&display=swap",
            rel="stylesheet",
        ),
    ],
    theme=rx.theme(appearance="light"),
)
from app.states.db_state import DbState

app.add_page(index, route="/", on_load=DbState.init_db)
app.add_page(login, route="/login")
app.add_page(signup, route="/signup")
from app.pages.dashboard import dashboard

app.add_page(dashboard, route="/dashboard")
from app.pages.attendance import attendance
from app.states.attendance_state import AttendanceState

app.add_page(
    attendance, route="/dashboard/attendance", on_load=AttendanceState.on_mount
)
from app.pages.data_management import data_management_page

app.add_page(data_management_page, route="/dashboard/data")
from app.pages.teachers import teachers_page

app.add_page(teachers_page, route="/dashboard/teachers")
from app.pages.rooms import rooms_page

app.add_page(rooms_page, route="/dashboard/rooms")
from app.pages.timings import timings_page

app.add_page(timings_page, route="/dashboard/timings")
from app.pages.courses import courses_page

app.add_page(courses_page, route="/dashboard/courses")
from app.pages.departments import departments_page

app.add_page(departments_page, route="/dashboard/departments")
from app.pages.sections import sections_page

app.add_page(sections_page, route="/dashboard/sections")
from app.pages.generate import generate_page

app.add_page(generate_page, route="/dashboard/generate")
from app.pages.not_found import not_found_page

app.add_page(not_found_page, route="/404")