import reflex as rx
from app.states.dashboard_state import DashboardState


class DbState(rx.State):
    @rx.event
    async def init_db(self):
        dashboard_state = await self.get_state(DashboardState)
        await dashboard_state.init_database()