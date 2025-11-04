import reflex as rx
from typing import TypedDict


class NavItem(TypedDict):
    label: str
    icon: str
    page: str


class PageState(rx.State):
    nav_items: list[NavItem] = [
        {"label": "Dashboard", "icon": "layout-dashboard", "page": "/dashboard"},
        {"label": "Data Management", "icon": "database", "page": "/dashboard/data"},
        {
            "label": "Attendance",
            "icon": "check-circle",
            "page": "/dashboard/attendance",
        },
        {
            "label": "Generate Timetable",
            "icon": "calendar-cog",
            "page": "/dashboard/generate",
        },
    ]
    active_page: str = "Dashboard"

    @rx.event
    def set_active_page(self, page_label: str):
        self.active_page = page_label