import reflex as rx


def index() -> rx.Component:
    return rx.el.main(
        rx.el.div(
            rx.el.div(
                rx.el.h1(
                    "SmartAlloc",
                    class_name="text-7xl font-bold text-white tracking-tighter",
                ),
                rx.el.p(
                    "A genetic algorithm-based timetable optimization system",
                    class_name="text-lg text-white/80 mt-4 max-w-xl text-center",
                ),
                rx.el.a(
                    rx.el.button(
                        "Get Started",
                        class_name="mt-8 bg-white text-blue-600 font-semibold px-8 py-3 rounded-full shadow-lg hover:bg-gray-100 hover:scale-105 transition-all duration-300",
                    ),
                    href="/login",
                ),
                class_name="flex flex-col items-center justify-center p-12 rounded-3xl bg-white/10 backdrop-blur-lg border border-white/20 shadow-2xl",
            ),
            class_name="min-h-screen flex items-center justify-center",
        ),
        class_name="font-['Poppins'] bg-gradient-to-br from-[#0066FF] to-[#00CCFF]",
    )


def login() -> rx.Component:
    return rx.el.div("Login Page - Coming Soon!", class_name="p-8")


app = rx.App(
    theme=rx.theme(appearance="light"),
    head_components=[
        rx.el.link(rel="preconnect", href="https://fonts.googleapis.com"),
        rx.el.link(rel="preconnect", href="https://fonts.gstatic.com", cross_origin=""),
        rx.el.link(
            href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap",
            rel="stylesheet",
        ),
    ],
)
app.add_page(index, route="/")
app.add_page(login, route="/login")