import reflex as rx
from app.states.dashboard_state import DashboardState
from app.components.sidebar import sidebar
from app.pages.teachers import data_management_header, auth_input, auth_button


def sections_page() -> rx.Component:
    return rx.el.div(
        sidebar(),
        rx.el.div(
            data_management_header(
                "Manage Sections", "Add, view, and remove sections."
            ),
            rx.el.main(
                rx.el.div(
                    rx.el.div(
                        rx.el.h3(
                            "Add New Section", class_name="text-xl font-semibold mb-4"
                        ),
                        rx.el.form(
                            rx.el.div(
                                auth_input("Section ID (e.g., A)", "section_id"),
                                auth_input("Year", "year", input_type="number"),
                                rx.el.select(
                                    rx.el.option(
                                        "Select Department", value="", disabled=True
                                    ),
                                    rx.foreach(
                                        DashboardState.departments,
                                        lambda d: rx.el.option(
                                            d["name"], value=d["id"]
                                        ),
                                    ),
                                    name="department_id",
                                    class_name="w-full px-4 py-3 rounded-lg border border-gray-600 bg-[#0d1117] text-white",
                                ),
                                auth_input(
                                    "Periods Monday",
                                    "periods_monday",
                                    input_type="number",
                                ),
                                auth_input(
                                    "Periods Tuesday",
                                    "periods_tuesday",
                                    input_type="number",
                                ),
                                auth_input(
                                    "Periods Wednesday",
                                    "periods_wednesday",
                                    input_type="number",
                                ),
                                auth_input(
                                    "Periods Thursday",
                                    "periods_thursday",
                                    input_type="number",
                                ),
                                auth_input(
                                    "Periods Friday",
                                    "periods_friday",
                                    input_type="number",
                                ),
                                auth_input(
                                    "Periods Saturday",
                                    "periods_saturday",
                                    input_type="number",
                                ),
                                auth_button("Add Section"),
                                class_name="space-y-4",
                            ),
                            on_submit=DashboardState.add_section,
                            reset_on_submit=True,
                        ),
                        class_name="p-6 bg-[#1c2128] rounded-xl border border-gray-700",
                    ),
                    rx.el.div(
                        rx.el.h3(
                            "Existing Sections", class_name="text-xl font-semibold mb-4"
                        ),
                        rx.el.div(
                            rx.el.table(
                                rx.el.thead(
                                    rx.el.tr(
                                        rx.el.th(
                                            "Year",
                                            class_name="p-4 text-left font-semibold",
                                        ),
                                        rx.el.th(
                                            "Section",
                                            class_name="p-4 text-left font-semibold",
                                        ),
                                        rx.el.th(
                                            "Department",
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
                                        DashboardState.sections,
                                        lambda section: rx.el.tr(
                                            rx.el.td(section["year"], class_name="p-4"),
                                            rx.el.td(
                                                section["section_id"], class_name="p-4"
                                            ),
                                            rx.el.td(
                                                section["department_name"],
                                                class_name="p-4",
                                            ),
                                            rx.el.td(
                                                rx.el.button(
                                                    rx.icon(
                                                        "trash-2", class_name="h-4 w-4"
                                                    ),
                                                    on_click=lambda: DashboardState.delete_section(
                                                        section["id"]
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
                    class_name="p-6",
                ),
                class_name="flex-1 overflow-auto",
            ),
            class_name="flex flex-col flex-1 relative",
        ),
        class_name="grid min-h-screen w-full lg:grid-cols-[280px_1fr] bg-[#0d1117] font-['Poppins'] text-white",
        on_mount=[DashboardState.load_sections, DashboardState.load_departments],
    )