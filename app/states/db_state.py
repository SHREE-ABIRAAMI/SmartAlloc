import reflex as rx
from app.states.dashboard_state import DashboardState


class DBState(rx.State):
    @rx.event
    async def initialize_app_data(self):
        """Initializes data required for the app, like dashboard stats."""
        dashboard_state = await self.get_state(DashboardState)
        yield dashboard_state.init_database