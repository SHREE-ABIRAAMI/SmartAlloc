import reflex as rx
from app.states.page_state import PageState
from app.states.dashboard_state import DashboardState


def nav_item(item: dict) -> rx.Component:
    is_active = item["label"] == PageState.active_page
    return rx.el.a(
        rx.el.div(
            rx.icon(item["icon"], class_name="h-5 w-5"),
            rx.el.span(item["label"], class_name="font-medium"),
            class_name=rx.cond(
                is_active,
                "flex items-center gap-3 rounded-lg bg-gray-700 px-3 py-2 text-white transition-all hover:text-white",
                "flex items-center gap-3 rounded-lg px-3 py-2 text-gray-400 transition-all hover:text-white",
            ),
        ),
        href=item["page"],
        on_click=lambda: PageState.set_active_page(item["label"]),
    )


def sidebar() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.a(
                rx.icon("bot", class_name="h-8 w-8 text-white"),
                rx.el.span("SmartAlloc", class_name="text-xl font-bold"),
                href="/",
                class_name="flex items-center gap-2 font-semibold text-white",
            ),
            rx.el.nav(
                rx.foreach(PageState.nav_items, nav_item),
                class_name="grid items-start px-2 text-sm font-medium",
            ),
            class_name="flex flex-col gap-6",
        ),
        class_name="hidden border-r border-gray-700 bg-[#1c2128] lg:flex flex-col h-full",
    )