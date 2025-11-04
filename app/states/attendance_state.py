import reflex as rx
from typing import TypedDict
from sqlalchemy import text
import datetime
import logging


class TeacherAttendance(TypedDict):
    id: int
    tuid: str
    full_name: str
    status: str | None
    date: str | None


class AttendanceState(rx.State):
    teachers_for_attendance: list[TeacherAttendance] = []
    attendance_date: str = datetime.date.today().isoformat()

    @rx.var
    def attendance_date_display(self) -> str:
        if not self.attendance_date:
            return ""
        try:
            date_obj = datetime.date.fromisoformat(self.attendance_date)
            return date_obj.strftime("%A, %Y-%m-%d")
        except (ValueError, TypeError) as e:
            logging.exception(f"Error parsing attendance date: {e}")
            return self.attendance_date

    @rx.event
    def set_attendance_date(self, new_date: str):
        self.attendance_date = new_date
        return AttendanceState.load_teachers_for_attendance

    @rx.event
    def on_mount(self):
        return AttendanceState.load_teachers_for_attendance

    @rx.event
    async def load_teachers_for_attendance(self):
        async with rx.asession() as session:
            result = await session.execute(
                text("""SELECT t.id, t.tuid, t.full_name, ta.status, ta.date
                    FROM teachers t
                    LEFT JOIN teacher_attendance ta ON t.id = ta.teacher_id AND ta.date = :date
                    ORDER BY t.tuid"""),
                {"date": self.attendance_date},
            )
            self.teachers_for_attendance = [
                dict(row) for row in result.mappings().all()
            ]

    @rx.event
    async def mark_attendance(self, teacher_id: int, status: str):
        async with rx.asession() as session:
            async with session.begin():
                res = await session.execute(
                    text(
                        "SELECT id FROM teacher_attendance WHERE teacher_id = :tid AND date = :date"
                    ),
                    {"tid": teacher_id, "date": self.attendance_date},
                )
                existing_id = res.scalar_one_or_none()
                if existing_id:
                    await session.execute(
                        text(
                            "UPDATE teacher_attendance SET status = :status WHERE id = :id"
                        ),
                        {"status": status, "id": existing_id},
                    )
                else:
                    await session.execute(
                        text(
                            "INSERT INTO teacher_attendance (teacher_id, date, status) VALUES (:tid, :date, :status)"
                        ),
                        {
                            "tid": teacher_id,
                            "date": self.attendance_date,
                            "status": status,
                        },
                    )
        await self.load_teachers_for_attendance()