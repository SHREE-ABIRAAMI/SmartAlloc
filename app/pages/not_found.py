import reflex as rx


def not_found_page() -> rx.Component:
    return rx.el.div(
        rx.el.h1("404 - Page Not Found", class_name="text-5xl font-bold text-white"),
        rx.el.p(
            "The page you are looking for does not exist.",
            class_name="text-lg text-gray-400 mt-4",
        ),
        rx.el.a(
            "Go back to Home",
            href="/",
            class_name="mt-8 px-6 py-3 rounded-xl bg-blue-600 text-white font-semibold hover:bg-blue-700 transition-colors",
        ),
        class_name="flex flex-col items-center justify-center min-h-screen bg-[#0d1117] text-center p-4",
    )