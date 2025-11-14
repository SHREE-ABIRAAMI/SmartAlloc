import reflex as rx
from app.states.auth_state import AuthState


def animated_background() -> rx.Component:
    return rx.el.div(
        rx.el.div(class_name="light x1"),
        rx.el.div(class_name="light x2"),
        rx.el.div(class_name="light x3"),
        rx.el.div(class_name="light x4"),
        rx.el.div(class_name="light x5"),
        rx.el.div(class_name="light x6"),
        rx.el.div(class_name="light x7"),
        rx.el.div(class_name="light x8"),
        rx.el.div(class_name="light x9"),
        class_name="absolute top-0 left-0 w-full h-full z-[-1] overflow-hidden",
    )


def glass_card(*children, **props) -> rx.Component:
    return rx.el.div(
        *children,
        bg="rgba(255, 255, 255, 0.05)",
        backdrop_filter="blur(10px)",
        class_name="border border-gray-700 rounded-2xl shadow-lg p-8",
        **props,
    )


def auth_input(placeholder: str, type: str, field) -> rx.Component:
    return rx.el.input(
        placeholder=placeholder,
        type=type,
        on_change=field,
        class_name="w-full p-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-all duration-300",
    )


def auth_button(text: str, on_click: rx.event.EventType) -> rx.Component:
    return rx.el.button(
        text,
        on_click=on_click,
        class_name="w-full p-3 rounded-lg bg-gradient-to-r from-blue-600 to-purple-600 text-white font-bold hover:from-blue-700 hover:to-purple-700 transition-all duration-300 shadow-lg",
    )


def base_layout(child: rx.Component) -> rx.Component:
    return rx.el.main(
        animated_background(),
        rx.el.div(
            child,
            class_name="relative z-10 flex flex-col items-center justify-center min-h-screen p-4",
        ),
        class_name="font-['Poppins'] bg-[#0d1117] text-white",
    )


def index() -> rx.Component:
    return base_layout(
        rx.el.div(
            rx.el.h1(
                "SmartAlloc",
                class_name="text-7xl font-bold tracking-tighter bg-clip-text text-transparent bg-gradient-to-r from-blue-500 to-purple-500 font-['Montserrat_Alternates']",
            ),
            rx.el.p(
                "Intelligent Timetable Automation",
                class_name="mt-4 text-2xl text-gray-400 font-['Quicksand']",
            ),
            rx.el.div(
                rx.el.a(
                    rx.el.button(
                        "Get Started",
                        class_name="px-8 py-3 rounded-lg bg-gradient-to-r from-blue-600 to-purple-600 text-white font-bold hover:from-blue-700 hover:to-purple-700 transition-all duration-300 shadow-lg",
                    ),
                    href="/login",
                ),
                class_name="mt-8",
            ),
            class_name="text-center",
        )
    )


def login() -> rx.Component:
    return base_layout(
        glass_card(
            rx.el.h2(
                "Welcome Back",
                class_name="text-3xl font-bold text-center text-white mb-6 font-['Quicksand']",
            ),
            rx.el.div(
                auth_input("Username", "text", AuthState.set_username),
                auth_input("Password", "password", AuthState.set_password),
                auth_button("Log In", AuthState.handle_login),
                class_name="flex flex-col gap-4",
            ),
            rx.el.p(
                "Don't have an account? ",
                rx.el.a(
                    "Sign Up",
                    href="/signup",
                    class_name="text-purple-400 hover:underline",
                ),
                class_name="text-center mt-6 text-gray-400",
            ),
            width="400px",
        )
    )


def signup() -> rx.Component:
    return base_layout(
        glass_card(
            rx.el.h2(
                "Create Account",
                class_name="text-3xl font-bold text-center text-white mb-6 font-['Quicksand']",
            ),
            rx.el.div(
                auth_input("Full Name", "text", AuthState.set_full_name),
                auth_input("Username", "text", AuthState.set_username),
                auth_input("Email", "email", AuthState.set_email),
                auth_input("Password", "password", AuthState.set_password),
                auth_input(
                    "Confirm Password", "password", AuthState.set_confirm_password
                ),
                auth_button("Sign Up", AuthState.handle_signup),
                class_name="flex flex-col gap-4",
            ),
            rx.el.p(
                "Already have an account? ",
                rx.el.a(
                    "Log In",
                    href="/login",
                    class_name="text-purple-400 hover:underline",
                ),
                class_name="text-center mt-6 text-gray-400",
            ),
            width="400px",
        )
    )


def placeholder_page(title: str) -> rx.Component:
    return base_layout(rx.el.h1(f"{title} Page - Coming Soon"))


def page_404() -> rx.Component:
    return base_layout(
        rx.el.div(
            rx.el.h1("404", class_name="text-9xl font-bold text-purple-500"),
            rx.el.p("Page Not Found", class_name="text-2xl mt-4"),
            rx.el.a(
                "Go Home", href="/", class_name="mt-8 text-blue-400 hover:underline"
            ),
            class_name="text-center",
        )
    )


app = rx.App(
    theme=rx.theme(appearance="light"),
    stylesheets=["/animations.css"],
    head_components=[
        rx.el.link(rel="preconnect", href="https://fonts.googleapis.com"),
        rx.el.link(rel="preconnect", href="https://fonts.gstatic.com", cross_origin=""),
        rx.el.link(
            href="https://fonts.googleapis.com/css2?family=Montserrat+Alternates:wght@700&family=Poppins:wght@400;600&family=Quicksand:wght@500;700&display=swap",
            rel="stylesheet",
        ),
    ],
)
app.add_page(index, route="/")
app.add_page(login, route="/login")
app.add_page(signup, route="/signup")
app.add_page(lambda: placeholder_page("Dashboard"), route="/dashboard")
app.add_page(lambda: placeholder_page("Attendance"), route="/attendance")
app.add_page(lambda: placeholder_page("Data Management"), route="/data-management")
app.add_page(lambda: placeholder_page("Teachers"), route="/teachers")
app.add_page(lambda: placeholder_page("Rooms"), route="/rooms")
app.add_page(lambda: placeholder_page("Timings"), route="/timings")
app.add_page(lambda: placeholder_page("Courses"), route="/courses")
app.add_page(lambda: placeholder_page("Departments"), route="/departments")
app.add_page(lambda: placeholder_page("Sections"), route="/sections")
app.add_page(lambda: placeholder_page("Generate Timetable"), route="/generate")
app.add_page(page_404, route="/404")