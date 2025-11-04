import reflex as rx
from app.states.dashboard_state import DashboardState
from app.components.sidebar import sidebar
from app.pages.teachers import data_management_header, auth_input, auth_button


def timings_page() -> rx.Component:
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    return rx.el.div(
        sidebar(),
        rx.el.div(
            data_management_header("Manage Timings", "Add, view, and remove timings."),
            rx.el.main(
                rx.el.div(
                    rx.el.div(
                        rx.el.h3(
                            "Add New Timing Slot",
                            class_name="text-xl font-semibold mb-4",
                        ),
                        rx.el.form(
                            rx.el.div(
                                auth_input("Time (e.g., 08:30-09:15)", "time"),
                                auth_input(
                                    "Timing Group (e.g., year_1)", "timing_group"
                                ),
                                rx.el.div(
                                    rx.el.label(
                                        "Days of the Week",
                                        class_name="font-medium mb-2",
                                    ),
                                    rx.el.div(
                                        rx.foreach(
                                            days,
                                            lambda day: rx.el.div(
                                                rx.el.input(
                                                    type="checkbox",
                                                    name="days_of_week",
                                                    id=day.lower(),
                                                    class_name="mr-2",
                                                    default_value=day,
                                                    key=day,
                                                ),
                                                rx.el.label(day, html_for=day.lower()),
                                                class_name="flex items-center",
                                            ),
                                        ),
                                        class_name="grid grid-cols-2 md:grid-cols-3 gap-2 mt-2",
                                    ),
                                    class_name="text-white",
                                ),
                                auth_button("Add Timing(s)"),
                                class_name="space-y-4",
                            ),
                            on_submit=DashboardState.add_timing,
                            reset_on_submit=True,
                        ),
                        class_name="p-6 bg-[#1c2128] rounded-xl border border-gray-700",
                    ),
                    rx.el.div(
                        rx.el.h3(
                            "Existing Timings", class_name="text-xl font-semibold mb-4"
                        ),
                        rx.el.div(
                            rx.el.table(
                                rx.el.thead(
                                    rx.el.tr(
                                        rx.el.th(
                                            "Time",
                                            class_name="p-4 text-left font-semibold",
                                        ),
                                        rx.el.th(
                                            "Day of Week",
                                            class_name="p-4 text-left font-semibold",
                                        ),
                                        rx.el.th(
                                            "Timing Group",
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
                                        DashboardState.timings,
                                        lambda timing: rx.el.tr(
                                            rx.el.td(timing["time"], class_name="p-4"),
                                            rx.el.td(
                                                timing["day_of_week"], class_name="p-4"
                                            ),
                                            rx.el.td(
                                                timing["timing_group"], class_name="p-4"
                                            ),
                                            rx.el.td(
                                                rx.el.button(
                                                    rx.icon(
                                                        "trash-2", class_name="h-4 w-4"
                                                    ),
                                                    on_click=lambda: DashboardState.delete_timing(
                                                        timing["id"]
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
        on_mount=DashboardState.load_timings,
    )