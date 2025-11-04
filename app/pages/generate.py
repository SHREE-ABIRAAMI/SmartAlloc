import reflex as rx
from app.states.timetable_state import TimetableGenerationState
from app.components.sidebar import sidebar
from app.components.chatbot import chatbot


def generation_controls() -> rx.Component:
    return rx.el.div(
        rx.el.button(
            "Start Timetable Generation",
            on_click=TimetableGenerationState.run_genetic_algorithm,
            is_loading=TimetableGenerationState.is_generating,
            class_name="px-6 py-3 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 text-white font-bold text-lg hover:from-blue-700 hover:to-purple-700 transition-all duration-300 ease-in-out shadow-lg hover:shadow-xl transform hover:-translate-y-1",
        ),
        rx.el.div(
            rx.el.p(f"Generation: {TimetableGenerationState.current_generation}"),
            rx.el.p(
                f"Best Fitness: {TimetableGenerationState.best_fitness.to_string()}"
            ),
            class_name="text-white font-mono",
        ),
        class_name="flex justify-between items-center p-6 bg-[#1c2128] rounded-t-xl border-b border-gray-700",
    )


def progress_view() -> rx.Component:
    return rx.el.div(
        rx.el.progress(
            value=TimetableGenerationState.progress, max=100, class_name="w-full"
        ),
        rx.el.p(f"{TimetableGenerationState.progress}%"),
        class_name="flex items-center gap-4 text-white p-6",
    )


def fitness_chart() -> rx.Component:
    return rx.recharts.line_chart(
        rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
        rx.recharts.line(data_key="fitness", type="monotone", stroke="#8884d8"),
        rx.recharts.x_axis(data_key="generation"),
        rx.recharts.y_axis(domain=[0.0, 1.0]),
        rx.recharts.tooltip(),
        data=TimetableGenerationState.generation_history,
        height=300,
        width="100%",
    )


def timetable_display() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.select(
                rx.foreach(
                    TimetableGenerationState.section_options,
                    lambda option: rx.el.option(option["label"], value=option["value"]),
                ),
                on_change=TimetableGenerationState.on_section_change,
                value=TimetableGenerationState.selected_section_id,
                class_name="px-4 py-2 rounded-lg border border-gray-600 bg-[#0d1117] text-white",
            ),
            rx.el.div(
                rx.el.button(
                    "Download PDF",
                    on_click=TimetableGenerationState.download_current_section_pdf,
                    class_name="px-4 py-2 bg-blue-600 text-white rounded-lg",
                ),
                rx.el.button(
                    "Download All (ZIP)",
                    on_click=TimetableGenerationState.download_all_sections_zip,
                    class_name="px-4 py-2 bg-purple-600 text-white rounded-lg",
                ),
                class_name="flex gap-4",
            ),
            class_name="flex justify-between items-center p-4",
        ),
        rx.el.div(
            rx.el.table(
                rx.el.thead(
                    rx.el.tr(
                        rx.el.th("Day", class_name="p-2 text-left"),
                        rx.foreach(
                            TimetableGenerationState.sorted_timings,
                            lambda t: rx.el.th(t, class_name="p-2 text-left text-xs"),
                        ),
                    )
                ),
                rx.el.tbody(
                    rx.foreach(
                        TimetableGenerationState.timetable_grid_data,
                        lambda day_data: rx.el.tr(
                            rx.el.td(day_data[0], class_name="font-bold p-2"),
                            rx.foreach(
                                day_data[1],
                                lambda slot: rx.el.td(
                                    rx.el.div(
                                        rx.el.p(
                                            slot["course_name"],
                                            class_name="font-semibold text-sm",
                                        ),
                                        rx.el.p(
                                            slot["teacher_name"],
                                            class_name="text-xs text-gray-400",
                                        ),
                                        rx.el.p(
                                            slot["room_number"],
                                            class_name="text-xs text-gray-500",
                                        ),
                                        class_name=rx.cond(
                                            slot["course_type"] == "Laboratory",
                                            "p-2 border border-yellow-500 bg-yellow-900/30 rounded-md",
                                            "p-2 border border-gray-700 bg-gray-800/30 rounded-md",
                                        ),
                                    )
                                ),
                            ),
                        ),
                    )
                ),
                class_name="w-full text-white table-auto",
            ),
            class_name="overflow-x-auto p-4",
        ),
        class_name="bg-[#1c2128] rounded-xl border border-gray-700 mt-6",
    )


def generate_page() -> rx.Component:
    return rx.el.div(
        sidebar(),
        rx.el.div(
            rx.el.header(
                rx.el.h1(
                    "Generate Timetable",
                    class_name="text-3xl font-bold tracking-tight text-white",
                ),
                class_name="p-6 border-b border-gray-700",
            ),
            rx.el.main(
                rx.el.div(
                    generation_controls(),
                    rx.cond(
                        TimetableGenerationState.is_generating,
                        rx.el.div(progress_view(), fitness_chart()),
                        rx.cond(
                            TimetableGenerationState.timetable_generated,
                            timetable_display(),
                            rx.el.div(
                                "Click button to start generation.",
                                class_name="p-6 text-center text-gray-400",
                            ),
                        ),
                    ),
                    class_name="p-6",
                ),
                class_name="flex-1 overflow-auto",
            ),
            chatbot(),
            class_name="flex flex-col flex-1 relative",
        ),
        class_name="grid min-h-screen w-full lg:grid-cols-[280px_1fr] bg-[#0d1117] font-['Poppins'] text-white",
        on_mount=TimetableGenerationState.load_all_data,
    )