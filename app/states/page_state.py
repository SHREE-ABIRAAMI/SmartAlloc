import reflex as rx
from typing import TypedDict


class NavItem(TypedDict):
    label: str
    icon: str
    href: str


class PageState(rx.State):
    nav_items: list[NavItem] = [
        {"label": "Dashboard", "icon": "layout-dashboard", "href": "/dashboard"},
        {"label": "Attendance", "icon": "check-square", "href": "/attendance"},
        {"label": "Data Management", "icon": "database", "href": "/data-management"},
        {"label": "Generate Timetable", "icon": "calendar-days", "href": "/generate"},
    ]

    @rx.var
    def active_page(self) -> str:
        return self.router.page.path.replace("/", "").replace("-", " ").title()