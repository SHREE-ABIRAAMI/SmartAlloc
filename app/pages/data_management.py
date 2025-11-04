import reflex as rx
from app.states.dashboard_state import DashboardState
from app.components.sidebar import sidebar


def management_card(icon: str, title: str, href: str) -> rx.Component:
    return rx.el.a(
        rx.el.div(
            rx.icon(icon, class_name="h-8 w-8 text-blue-400 mb-4"),
            rx.el.h3(title, class_name="text-lg font-semibold text-white mb-2"),
            class_name="p-6 bg-[#1c2128] rounded-xl border border-gray-700 hover:border-blue-500 transition-all duration-300 h-full flex flex-col justify-center items-center",
        ),
        href=href,
        width="100%",
    )


def data_management_page() -> rx.Component:
    return rx.el.div(
        sidebar(),
        rx.el.div(
            rx.el.header(
                rx.el.h1(
                    "Data Management",
                    class_name="text-3xl font-bold tracking-tight text-white",
                ),
                rx.el.p(
                    "Manage all academic data from one place.",
                    class_name="text-gray-400 mt-1",
                ),
                class_name="p-6 border-b border-gray-700",
            ),
            rx.el.main(
                rx.el.div(
                    management_card("users", "Teachers", "/dashboard/teachers"),
                    management_card("door-open", "Rooms", "/dashboard/rooms"),
                    management_card("clock", "Timings", "/dashboard/timings"),
                    management_card("book-open", "Courses", "/dashboard/courses"),
                    management_card(
                        "building", "Departments", "/dashboard/departments"
                    ),
                    management_card("users-round", "Sections", "/dashboard/sections"),
                    class_name="grid md:grid-cols-2 lg:grid-cols-3 gap-6 p-6",
                ),
                class_name="flex-1 overflow-auto",
            ),
            class_name="flex flex-col flex-1 relative",
        ),
        class_name="grid min-h-screen w-full lg:grid-cols-[280px_1fr] bg-[#0d1117] font-['Poppins'] text-white",
    )