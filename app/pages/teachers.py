import reflex as rx
from app.states.dashboard_state import DashboardState
from app.components.sidebar import sidebar


def data_management_header(title: str, subtitle: str) -> rx.Component:
    return rx.el.header(
        rx.el.div(
            rx.el.h1(title, class_name="text-3xl font-bold tracking-tight text-white"),
            rx.el.p(subtitle, class_name="text-gray-400 mt-1"),
            class_name="flex-1",
        ),
        class_name="flex items-center justify-between p-6 border-b border-gray-700",
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


def teachers_page() -> rx.Component:
    return rx.el.div(
        sidebar(),
        rx.el.div(
            data_management_header(
                "Manage Teachers", "Add, view, and remove teachers."
            ),
            rx.el.main(
                rx.el.div(
                    rx.el.div(
                        rx.el.h3(
                            "Add New Teacher", class_name="text-xl font-semibold mb-4"
                        ),
                        rx.el.form(
                            rx.el.div(
                                auth_input("Teacher Unique ID (TUID)", "tuid"),
                                auth_input("Full Name", "full_name"),
                                auth_button("Add Teacher"),
                                class_name="space-y-4",
                            ),
                            on_submit=DashboardState.add_teacher,
                            reset_on_submit=True,
                        ),
                        class_name="p-6 bg-[#1c2128] rounded-xl border border-gray-700",
                    ),
                    rx.el.div(
                        rx.el.h3(
                            "Existing Teachers", class_name="text-xl font-semibold mb-4"
                        ),
                        rx.el.div(
                            rx.el.table(
                                rx.el.thead(
                                    rx.el.tr(
                                        rx.el.th(
                                            "TUID",
                                            class_name="p-4 text-left font-semibold",
                                        ),
                                        rx.el.th(
                                            "Full Name",
                                            class_name="p-4 text-left font-semibold",
                                        ),
                                        rx.el.th(
                                            "Actions",
                                            class_name="p-4 text-left font-semibold",
                                        ),
                                        class_name="border-b-2 border-gray-600 bg-[#22272e]",
                                    )
                                ),
                                rx.el.tbody(
                                    rx.foreach(
                                        DashboardState.teachers,
                                        lambda teacher: rx.el.tr(
                                            rx.el.td(teacher["tuid"], class_name="p-4"),
                                            rx.el.td(
                                                teacher["full_name"], class_name="p-4"
                                            ),
                                            rx.el.td(
                                                rx.el.button(
                                                    rx.icon(
                                                        "trash-2", class_name="h-4 w-4"
                                                    ),
                                                    on_click=lambda: DashboardState.delete_teacher(
                                                        teacher["id"]
                                                    ),
                                                    class_name="p-2 rounded-md text-red-400 hover:bg-red-900/50 transition-colors",
                                                ),
                                                class_name="p-4",
                                            ),
                                            class_name="border-b border-gray-700 hover:bg-[#2a3038] transition-colors",
                                        ),
                                    )
                                ),
                                class_name="w-full text-left table-auto",
                            ),
                            class_name="overflow-hidden rounded-b-xl border border-gray-700 border-t-0 bg-[#1c2128]",
                        ),
                        class_name="mt-8",
                    ),
                    class_name="p-6 grid md:grid-cols-1 gap-8",
                ),
                class_name="flex-1 overflow-auto",
            ),
            class_name="flex flex-col flex-1 relative",
        ),
        class_name="grid min-h-screen w-full lg:grid-cols-[280px_1fr] bg-[#0d1117] font-['Poppins'] text-white",
        on_mount=DashboardState.load_teachers,
    )