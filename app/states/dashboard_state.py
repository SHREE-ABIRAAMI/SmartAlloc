import reflex as rx


class DashboardState(rx.State):
    initialized: bool = False

    @rx.event(background=True)
    async def init_database(self):
        print("Initializing database... (placeholder)")
        async with self:
            self.initialized = True
        yield