import reflex as rx
from app.states.subject_state import SubjectState


def subject_management_page() -> rx.Component:
    return rx.el.div(
        rx.el.h1("Manage Subjects", class_name="text-2xl font-bold mb-4"),
        rx.el.div(
            rx.el.input(
                placeholder="Subject Name",
                on_change=SubjectState.set_new_subject_name,
                class_name="p-2 border rounded-md",
                default_value=SubjectState.new_subject_name,
            ),
            rx.el.select(
                rx.foreach(
                    SubjectState.departments,
                    lambda dept: rx.el.option(dept, value=dept),
                ),
                value=SubjectState.new_subject_department,
                on_change=SubjectState.set_new_subject_department,
                class_name="p-2 border rounded-md",
            ),
            rx.el.select(
                rx.foreach(
                    SubjectState.years,
                    lambda year: rx.el.option(year.to_string(), value=year.to_string()),
                ),
                value=SubjectState.new_subject_year.to_string(),
                on_change=SubjectState.set_new_subject_year,
                class_name="p-2 border rounded-md",
            ),
            rx.el.button(
                "Add Subject",
                on_click=SubjectState.add_subject,
                class_name="bg-blue-500 text-white p-2 rounded-md",
            ),
            class_name="flex gap-4 mb-4 items-center",
        ),
        rx.el.table(
            rx.el.thead(
                rx.el.tr(
                    rx.el.th("ID", class_name="px-4 py-2"),
                    rx.el.th("Name", class_name="px-4 py-2"),
                    rx.el.th("Department", class_name="px-4 py-2"),
                    rx.el.th("Year", class_name="px-4 py-2"),
                    rx.el.th("Actions", class_name="px-4 py-2"),
                )
            ),
            rx.el.tbody(
                rx.foreach(
                    SubjectState.subjects,
                    lambda subject: rx.el.tr(
                        rx.el.td(subject["id"], class_name="border px-4 py-2"),
                        rx.el.td(subject["name"], class_name="border px-4 py-2"),
                        rx.el.td(subject["department"], class_name="border px-4 py-2"),
                        rx.el.td(subject["year"], class_name="border px-4 py-2"),
                        rx.el.td(
                            rx.el.button(
                                rx.icon(tag="trash-2", class_name="h-4 w-4"),
                                on_click=lambda: SubjectState.delete_subject(
                                    subject["id"]
                                ),
                                class_name="text-red-500 hover:text-red-700",
                            ),
                            class_name="border px-4 py-2 text-center",
                        ),
                    ),
                )
            ),
            class_name="w-full text-left table-auto",
        ),
        class_name="p-8",
    )


def index() -> rx.Component:
    return rx.el.main(
        rx.el.div(
            rx.el.h1(
                "Environment is ready...",
                class_name="text-3xl font-semibold text-gray-800 mb-4",
            ),
            rx.el.p(
                "Keep prompting to build your app!", class_name="text-gray-600 mb-12"
            ),
            rx.el.a(
                rx.el.button(
                    "View Documentation",
                    rx.icon("arrow-right", class_name="ml-2", size=16),
                    class_name="bg-violet-500 text-white px-6 py-3 rounded-lg hover:bg-violet-600 transition-colors flex items-center font-medium",
                ),
                href="https://reflex.dev/docs/ai-builder/overview/best-practices/",
                target="_blank",
            ),
            rx.el.a(
                rx.el.button(
                    "Manage Subjects",
                    class_name="bg-green-500 text-white px-6 py-3 rounded-lg hover:bg-green-600 transition-colors flex items-center font-medium mt-4",
                ),
                href="/subjects",
            ),
            class_name="flex flex-col items-center justify-center text-center min-h-screen",
        ),
        class_name="font-['Inter'] bg-white",
    )


app = rx.App(
    theme=rx.theme(appearance="light"),
    head_components=[
        rx.el.link(rel="preconnect", href="https://fonts.googleapis.com"),
        rx.el.link(rel="preconnect", href="https://fonts.gstatic.com", cross_origin=""),
        rx.el.link(
            href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap",
            rel="stylesheet",
        ),
    ],
)
app.add_page(index)
app.add_page(subject_management_page, route="/subjects")