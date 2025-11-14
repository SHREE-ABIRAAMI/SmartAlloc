import reflex as rx
import datetime
from typing import TypedDict
from sqlalchemy import text


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
            return "Select a date"
        return datetime.date.fromisoformat(self.attendance_date).strftime("%B %d, %Y")

    @rx.event
    def set_attendance_date(self, new_date: str):
        self.attendance_date = new_date
        return AttendanceState.load_teachers_for_attendance

    @rx.event
    def on_mount(self):
        return AttendanceState.load_teachers_for_attendance

    @rx.event(background=True)
    async def load_teachers_for_attendance(self):
        async with self:
            date_to_check = self.attendance_date
        if not date_to_check:
            return
        async with rx.asession() as session:
            query = text("""
                SELECT 
                    t.id, 
                    t.tuid, 
                    t.full_name,
                    ta.status,
                    ta.date
                FROM teachers t
                LEFT JOIN teacher_attendance ta 
                ON t.id = ta.teacher_id AND ta.date = :date
            """)
            result = await session.execute(query, {"date": date_to_check})
            teachers = result.fetchall()
            async with self:
                self.teachers_for_attendance = [
                    {
                        "id": row.id,
                        "tuid": row.tuid,
                        "full_name": row.full_name,
                        "status": row.status,
                        "date": str(row.date) if row.date else None,
                    }
                    for row in teachers
                ]

    @rx.event(background=True)
    async def mark_attendance(self, teacher_id: int, status: str):
        async with self:
            current_date = self.attendance_date
        async with rx.asession() as session:
            async with session.begin():
                check_query = text("""
                    SELECT id FROM teacher_attendance 
                    WHERE teacher_id = :teacher_id AND date = :date
                """)
                result = await session.execute(
                    check_query, {"teacher_id": teacher_id, "date": current_date}
                )
                existing_record = result.scalar_one_or_none()
                if existing_record:
                    update_query = text("""
                        UPDATE teacher_attendance 
                        SET status = :status
                        WHERE id = :id
                    """)
                    await session.execute(
                        update_query, {"status": status, "id": existing_record}
                    )
                else:
                    insert_query = text("""
                        INSERT INTO teacher_attendance (teacher_id, date, status) 
                        VALUES (:teacher_id, :date, :status)
                    """)
                    await session.execute(
                        insert_query,
                        {
                            "teacher_id": teacher_id,
                            "date": current_date,
                            "status": status,
                        },
                    )
        yield AttendanceState.load_teachers_for_attendance