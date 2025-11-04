import reflex as rx
from app.states.attendance_state import AttendanceState
from app.states.page_state import PageState
from app.components.sidebar import sidebar


def attendance_header() -> rx.Component:
    return rx.el.header(
        rx.el.div(
            rx.el.h1(
                "Teacher Attendance",
                class_name="text-3xl font-bold tracking-tight text-white",
            ),
            rx.el.p(
                "Mark teacher presence for the selected date.",
                class_name="text-gray-400",
            ),
            class_name="flex-1",
        ),
        class_name="flex items-center justify-between p-6 border-b border-gray-700",
    )


def attendance_controls() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.label(
                "Select Date:",
                class_name="font-medium text-white mr-2",
                html_for="attendance-date",
            ),
            rx.el.input(
                id="attendance-date",
                type="date",
                default_value=AttendanceState.attendance_date,
                on_change=AttendanceState.set_attendance_date,
                class_name="px-3 py-2 rounded-lg border border-gray-600 bg-[#0d1117] text-white focus:outline-none focus:ring-2 focus:ring-blue-500",
            ),
            class_name="flex items-center",
        ),
        rx.el.p(
            f"Displaying for: {AttendanceState.attendance_date_display}",
            class_name="text-lg font-semibold text-gray-300",
        ),
        class_name="flex justify-between items-center p-6 bg-[#1c2128] rounded-t-xl border-b border-gray-700",
    )


def attendance_row(teacher: dict) -> rx.Component:
    return rx.el.tr(
        rx.el.td(teacher["tuid"], class_name="p-4"),
        rx.el.td(teacher["full_name"], class_name="p-4"),
        rx.el.td(
            rx.el.span(
                rx.cond(teacher["status"], teacher["status"], "Not Marked"),
                class_name=rx.cond(
                    teacher["status"] == "Present",
                    "px-3 py-1 rounded-full text-xs font-medium bg-green-900 text-green-200",
                    rx.cond(
                        teacher["status"] == "Absent",
                        "px-3 py-1 rounded-full text-xs font-medium bg-red-900 text-red-200",
                        "px-3 py-1 rounded-full text-xs font-medium bg-gray-700 text-gray-300",
                    ),
                ),
            ),
            class_name="p-4",
        ),
        rx.el.td(
            rx.el.div(
                rx.el.button(
                    "Mark Present",
                    on_click=lambda: AttendanceState.mark_attendance(
                        teacher["id"], "Present"
                    ),
                    class_name="px-3 py-1 rounded-md text-sm font-semibold bg-green-600 text-white hover:bg-green-700 transition-colors disabled:opacity-50",
                    disabled=teacher["status"] == "Present",
                ),
                rx.el.button(
                    "Mark Absent",
                    on_click=lambda: AttendanceState.mark_attendance(
                        teacher["id"], "Absent"
                    ),
                    class_name="px-3 py-1 rounded-md text-sm font-semibold bg-red-600 text-white hover:bg-red-700 transition-colors disabled:opacity-50",
                    disabled=teacher["status"] == "Absent",
                ),
                class_name="flex items-center gap-2",
            ),
            class_name="p-4",
        ),
        class_name="border-b border-gray-700 hover:bg-[#2a3038] transition-colors",
    )


def attendance_table() -> rx.Component:
    return rx.el.div(
        rx.el.table(
            rx.el.thead(
                rx.el.tr(
                    rx.el.th("TUID", class_name="p-4 text-left font-semibold"),
                    rx.el.th("Full Name", class_name="p-4 text-left font-semibold"),
                    rx.el.th("Status", class_name="p-4 text-left font-semibold"),
                    rx.el.th("Actions", class_name="p-4 text-left font-semibold"),
                    class_name="border-b-2 border-gray-600 bg-[#22272e]",
                )
            ),
            rx.el.tbody(
                rx.foreach(AttendanceState.teachers_for_attendance, attendance_row)
            ),
            class_name="w-full text-left table-auto",
        ),
        class_name="overflow-hidden rounded-b-xl border border-gray-700 border-t-0 bg-[#1c2128]",
    )


def attendance_content() -> rx.Component:
    return rx.el.main(
        rx.el.div(attendance_controls(), attendance_table(), class_name="p-6"),
        class_name="flex-1 overflow-auto",
    )


def attendance() -> rx.Component:
    return rx.el.div(
        sidebar(),
        rx.el.div(
            attendance_header(), attendance_content(), class_name="flex flex-col flex-1"
        ),
        class_name="grid min-h-screen w-full lg:grid-cols-[280px_1fr] bg-[#0d1117] font-['Poppins'] text-white",
        on_mount=AttendanceState.on_mount,
    )