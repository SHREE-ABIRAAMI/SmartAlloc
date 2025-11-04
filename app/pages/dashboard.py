import reflex as rx
from app.components.sidebar import sidebar
from app.states.dashboard_state import DashboardState
from app.states.chatbot_state import ChatbotState


def info_card(icon: str, title: str, description: str, href: str) -> rx.Component:
    return rx.el.a(
        rx.el.div(
            rx.icon(icon, class_name="h-8 w-8 text-blue-400 mb-4"),
            rx.el.h3(title, class_name="text-lg font-semibold text-white mb-2"),
            rx.el.p(description, class_name="text-sm text-gray-400"),
            class_name="p-6 bg-[#1c2128] rounded-xl border border-gray-700 hover:border-blue-500 transition-all duration-300 h-full flex flex-col",
        ),
        href=href,
        width="100%",
    )


def dashboard_header() -> rx.Component:
    return rx.el.header(
        rx.el.div(
            rx.el.h1(
                "Welcome to Your SmartAlloc Dashboard",
                class_name="text-3xl font-bold tracking-tight text-white",
            ),
            rx.el.p(
                f"Your AI-powered command center for academic scheduling.",
                class_name="text-gray-400 mt-1",
            ),
            class_name="flex-1",
        ),
        class_name="flex items-center justify-between p-6 border-b border-gray-700",
    )


def dashboard_content() -> rx.Component:
    return rx.el.main(
        rx.el.div(
            rx.el.div(
                info_card(
                    "database",
                    "1. Manage Data",
                    "Use the sidebar to add and manage teachers, rooms, courses, and other essential academic data.",
                    "/dashboard/data",
                ),
                info_card(
                    "calendar-cog",
                    "2. Generate Timetable",
                    "Once your data is ready, our genetic algorithm will craft the optimal schedule for you.",
                    "/dashboard/generate",
                ),
                rx.el.div(
                    info_card(
                        "bot",
                        "3. Ask the Assistant",
                        "Query your generated timetable with our HOD Assistant for quick insights and answers.",
                        "#",
                    ),
                    on_click=ChatbotState.toggle_chat,
                ),
                class_name="grid md:grid-cols-3 gap-6",
            ),
            class_name="p-6",
        ),
        class_name="flex-1 overflow-auto",
    )


from app.components.chatbot import chatbot


def dashboard() -> rx.Component:
    return rx.el.div(
        sidebar(),
        rx.el.div(
            dashboard_header(),
            dashboard_content(),
            chatbot(),
            rx.el.div(
                rx.el.span(
                    f"SHREE {DashboardState.current_user}", class_name="font-semibold"
                ),
                rx.el.button(
                    rx.icon("log-out", class_name="h-5 w-5"),
                    on_click=DashboardState.handle_logout,
                    class_name="p-2 rounded-full text-gray-400 hover:bg-gray-700 hover:text-white transition-all",
                ),
                class_name="absolute top-6 right-6 flex items-center gap-4 text-white",
            ),
            class_name="flex flex-col flex-1 relative",
        ),
        class_name="grid min-h-screen w-full lg:grid-cols-[280px_1fr] bg-[#0d1117] font-['Poppins'] text-white",
        on_mount=DashboardState.check_login,
    )