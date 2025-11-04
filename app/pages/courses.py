import reflex as rx
from app.states.dashboard_state import DashboardState
from app.components.sidebar import sidebar
from app.pages.teachers import data_management_header, auth_input, auth_button


def courses_page() -> rx.Component:
    return rx.el.div(
        sidebar(),
        rx.el.div(
            data_management_header("Manage Courses", "Add, view, and remove courses."),
            rx.el.main(
                rx.el.div(
                    rx.el.div(
                        rx.el.h3(
                            "Add New Course", class_name="text-xl font-semibold mb-4"
                        ),
                        rx.el.form(
                            rx.el.div(
                                auth_input("Course ID", "course_id"),
                                auth_input("Course Name", "course_name"),
                                rx.el.select(
                                    rx.el.option(
                                        "Select Teacher", value="", disabled=True
                                    ),
                                    rx.foreach(
                                        DashboardState.teachers,
                                        lambda t: rx.el.option(
                                            t["full_name"], value=t["id"]
                                        ),
                                    ),
                                    name="teacher_id",
                                    class_name="w-full px-4 py-3 rounded-lg border border-gray-600 bg-[#0d1117] text-white",
                                ),
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
                                rx.el.select(
                                    rx.el.option(
                                        "Select Section", value="", disabled=True
                                    ),
                                    rx.foreach(
                                        DashboardState.sections,
                                        lambda s: rx.el.option(
                                            f"{s['year']} - {s['section_id']}",
                                            value=s["id"],
                                        ),
                                    ),
                                    name="section_id",
                                    class_name="w-full px-4 py-3 rounded-lg border border-gray-600 bg-[#0d1117] text-white",
                                ),
                                rx.el.select(
                                    rx.el.option(
                                        "Course Type", value="", disabled=True
                                    ),
                                    rx.el.option("Theory", value="Theory"),
                                    rx.el.option("Laboratory", value="Laboratory"),
                                    rx.el.option("Special", value="Special"),
                                    name="course_type",
                                    class_name="w-full px-4 py-3 rounded-lg border border-gray-600 bg-[#0d1117] text-white",
                                ),
                                rx.el.div(
                                    rx.el.input(
                                        type="checkbox", name="is_daily", id="is_daily"
                                    ),
                                    rx.el.label(
                                        "Daily Course?",
                                        html_for="is_daily",
                                        class_name="ml-2",
                                    ),
                                    class_name="flex items-center text-white",
                                ),
                                auth_input(
                                    "Continuous Periods",
                                    "continuous_periods",
                                    input_type="number",
                                ),
                                auth_button("Add Course"),
                                class_name="space-y-4",
                            ),
                            on_submit=DashboardState.add_course,
                            reset_on_submit=True,
                        ),
                        class_name="p-6 bg-[#1c2128] rounded-xl border border-gray-700",
                    ),
                    rx.el.div(
                        rx.el.h3(
                            "Existing Courses", class_name="text-xl font-semibold mb-4"
                        ),
                        rx.el.div(
                            rx.el.table(
                                rx.el.thead(
                                    rx.el.tr(
                                        rx.el.th(
                                            "ID",
                                            class_name="p-4 text-left font-semibold",
                                        ),
                                        rx.el.th(
                                            "Name",
                                            class_name="p-4 text-left font-semibold",
                                        ),
                                        rx.el.th(
                                            "Teacher",
                                            class_name="p-4 text-left font-semibold",
                                        ),
                                        rx.el.th(
                                            "Section",
                                            class_name="p-4 text-left font-semibold",
                                        ),
                                        rx.el.th(
                                            "Type",
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
                                        DashboardState.courses,
                                        lambda course: rx.el.tr(
                                            rx.el.td(
                                                course["course_id"], class_name="p-4"
                                            ),
                                            rx.el.td(
                                                course["course_name"], class_name="p-4"
                                            ),
                                            rx.el.td(
                                                course["teacher_name"], class_name="p-4"
                                            ),
                                            rx.el.td(
                                                course["section_name"], class_name="p-4"
                                            ),
                                            rx.el.td(
                                                course["course_type"], class_name="p-4"
                                            ),
                                            rx.el.td(
                                                rx.el.button(
                                                    rx.icon(
                                                        "trash-2", class_name="h-4 w-4"
                                                    ),
                                                    on_click=lambda: DashboardState.delete_course(
                                                        course["id"]
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
        on_mount=[
            DashboardState.load_courses,
            DashboardState.load_teachers,
            DashboardState.load_departments,
            DashboardState.load_sections,
        ],
    )