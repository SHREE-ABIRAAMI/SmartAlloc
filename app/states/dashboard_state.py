import reflex as rx
from typing import TypedDict
from sqlalchemy import text
import logging


class Teacher(TypedDict):
    id: int
    tuid: str
    full_name: str


class Room(TypedDict):
    id: int
    year: int
    section_id: str
    lh_number: str
    capacity: int


class Timing(TypedDict):
    id: int
    time: str
    day_of_week: str
    timing_group: str | None


class Course(TypedDict):
    id: int
    course_id: str
    course_name: str
    teacher_id: int
    teacher_name: str | None
    year: int | None
    department_id: int | None
    department_name: str | None
    course_type: str | None
    section_id: int | None
    section_name: str | None
    is_daily: bool
    continuous_periods: int
    is_combined_class: bool
    combined_class_group: str | None
    is_fixed_teacher: bool


class Department(TypedDict):
    id: int
    name: str


class Section(TypedDict):
    id: int
    section_id: str
    department_id: int
    year: int
    department_name: str | None
    periods_monday: int
    periods_tuesday: int
    periods_wednesday: int
    periods_thursday: int
    periods_friday: int
    periods_saturday: int


class DashboardState(rx.State):
    is_logged_in: bool = False
    current_user: str = ""
    teachers: list[Teacher] = []
    rooms: list[Room] = []
    timings: list[Timing] = []
    courses: list[Course] = []
    departments: list[Department] = []
    sections: list[Section] = []
    upload_status: str = "No file selected."

    async def _add_column_if_not_exists(
        self, session, table_name: str, column_name: str, column_type: str
    ):
        try:
            res = await session.execute(text(f"PRAGMA table_info({table_name})"))
            columns = [row[1] for row in res.fetchall()]
            if column_name not in columns:
                await session.execute(
                    text(
                        f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
                    )
                )
        except Exception as e:
            logging.exception(f"Error adding column {column_name} to {table_name}: {e}")

    @rx.event
    async def init_database(self):
        async with rx.asession() as session:
            async with session.begin():
                await session.execute(
                    text("""
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        first_name TEXT NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL
                    );
                """)
                )
                await session.execute(
                    text("""
                    CREATE TABLE IF NOT EXISTS teachers (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tuid TEXT UNIQUE NOT NULL,
                        full_name TEXT NOT NULL
                    );
                """)
                )
                await session.execute(
                    text("""
                    CREATE TABLE IF NOT EXISTS rooms (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        year INTEGER,
                        section_id TEXT,
                        lh_number TEXT NOT NULL,
                        capacity INTEGER NOT NULL,
                        UNIQUE(lh_number, year, section_id)
                    );
                """)
                )
                await session.execute(
                    text("""
                    CREATE TABLE IF NOT EXISTS timings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        time TEXT NOT NULL,
                        day_of_week TEXT NOT NULL,
                        timing_group TEXT,
                        UNIQUE(time, day_of_week, timing_group)
                    );
                    """)
                )
                await session.execute(
                    text("""
                    CREATE TABLE IF NOT EXISTS departments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL
                    );
                    """)
                )
                await session.execute(
                    text("""
                    CREATE TABLE IF NOT EXISTS sections (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        section_id TEXT NOT NULL,
                        department_id INTEGER NOT NULL,
                        year INTEGER,
                        periods_monday INTEGER DEFAULT 0,
                        periods_tuesday INTEGER DEFAULT 0,
                        periods_wednesday INTEGER DEFAULT 0,
                        periods_thursday INTEGER DEFAULT 0,
                        periods_friday INTEGER DEFAULT 0,
                        periods_saturday INTEGER DEFAULT 0,
                        FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE CASCADE,
                        UNIQUE(section_id, department_id, year)
                    );
                    """)
                )
                await session.execute(
                    text("""
                    CREATE TABLE IF NOT EXISTS courses (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        course_id TEXT NOT NULL,
                        course_name TEXT NOT NULL,
                        teacher_id INTEGER NOT NULL,
                        year INTEGER,
                        department_id INTEGER,
                        course_type TEXT,
                        section_id INTEGER,
                        FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE,
                        FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE CASCADE,
                        FOREIGN KEY (section_id) REFERENCES sections(id) ON DELETE CASCADE
                    );
                    """)
                )
                await self._add_column_if_not_exists(
                    session, "courses", "is_daily", "INTEGER DEFAULT 0"
                )
                await self._add_column_if_not_exists(
                    session, "courses", "continuous_periods", "INTEGER DEFAULT 1"
                )
                await self._add_column_if_not_exists(
                    session, "courses", "is_combined_class", "INTEGER DEFAULT 0"
                )
                await self._add_column_if_not_exists(
                    session, "courses", "combined_class_group", "TEXT"
                )
                await self._add_column_if_not_exists(
                    session, "courses", "is_fixed_teacher", "INTEGER DEFAULT 0"
                )
                await session.execute(
                    text("""
                    CREATE TABLE IF NOT EXISTS course_teachers (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        course_id INTEGER NOT NULL,
                        teacher_id INTEGER NOT NULL,
                        FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
                        FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE
                    );
                """)
                )
                await session.execute(
                    text("""
                    CREATE TABLE IF NOT EXISTS timetable (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        course_id INTEGER,
                        teacher_id INTEGER,
                        room_id INTEGER,
                        timing_id INTEGER,
                        section_id INTEGER,
                        FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
                        FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE,
                        FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
                        FOREIGN KEY (timing_id) REFERENCES timings(id) ON DELETE CASCADE,
                        FOREIGN KEY (section_id) REFERENCES sections(id) ON DELETE CASCADE
                    );
                    """)
                )
                await session.execute(
                    text("""
                    CREATE TABLE IF NOT EXISTS teacher_attendance (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        teacher_id INTEGER NOT NULL,
                        date TEXT NOT NULL,
                        status TEXT NOT NULL CHECK(status IN ('Present', 'Absent')),
                        FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE,
                        UNIQUE(teacher_id, date)
                    );
                    """)
                )
                result = await session.execute(text("SELECT COUNT(*) FROM users"))
                user_count = result.scalar_one()
                if user_count == 0:
                    logging.info("Users table is empty. Populating with sample data.")
                    await self._add_sample_data(session)
                else:
                    logging.info(
                        "Database already contains data. Skipping sample data population."
                    )

    async def _add_sample_data(self, session):
        dept_res = await session.execute(
            text(
                "INSERT INTO departments (name) VALUES ('Computer Science') RETURNING id"
            )
        )
        cs_dept_id = dept_res.scalar_one()
        section_ids = {}
        for year in [1, 2, 3]:
            for sec in ["A", "B"]:
                res = await session.execute(
                    text("""INSERT INTO sections (section_id, department_id, year, 
                                             periods_monday, periods_tuesday, periods_wednesday, 
                                             periods_thursday, periods_friday, periods_saturday) 
                           VALUES (:sec, :dept_id, :year, 9, 9, 9, 9, 9, 6) RETURNING id"""),
                    {"sec": sec, "dept_id": cs_dept_id, "year": year},
                )
                section_ids[f"{year}{sec}"] = res.scalar_one()
        teachers = {
            "Lakshmi Iyer": "T001",
            "Meera Reddy": "T002",
            "Ramesh Gupta": "T003",
            "Suresh Naik": "T004",
            "Rajesh Kumar": "T005",
            "Anitha Sharma": "T006",
            "Vijay Patel": "T007",
            "Priya Singh": "T008",
            "Arun Verma": "T009",
            "Kavitha Nair": "T010",
            "Deepak Shah": "T011",
            "Nisha Mehta": "T012",
            "Karthik Bose": "T013",
            "Divya Rao": "T014",
            "Praveen Das": "T015",
            "Sneha Joshi": "T016",
            "Arjun Pillai": "T017",
            "Ritu Malhotra": "T018",
        }
        teacher_ids = {}
        for name, tuid in teachers.items():
            res = await session.execute(
                text(
                    "INSERT INTO teachers (tuid, full_name) VALUES (:tuid, :name) RETURNING id"
                ),
                {"tuid": tuid, "name": name},
            )
            teacher_ids[name] = res.scalar_one()
        teacher_id_list = list(teacher_ids.values())
        rooms_to_add = []
        for building in ["LH", "LAB"]:
            for floor in range(1, 5):
                for room_num in range(1, 4):
                    for sec_suffix in ["A", "B"]:
                        rooms_to_add.append(f"{building}{floor}0{room_num}{sec_suffix}")
        for room_lh in rooms_to_add[:30]:
            await session.execute(
                text("INSERT INTO rooms (lh_number, capacity) VALUES (:lh, 65)"),
                {"lh": room_lh},
            )
        timings_config = [
            "08:30-09:15",
            "09:15-10:00",
            "10:15-11:00",
            "11:00-11:45",
            "11:45-12:30",
            "13:15-14:00",
            "14:00-14:45",
            "15:00-15:45",
            "15:45-16:30",
        ]
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        for time_slot in timings_config:
            for day in days:
                await session.execute(
                    text(
                        "INSERT OR IGNORE INTO timings (time, day_of_week, timing_group) VALUES (:time, :day, :group)"
                    ),
                    {"time": time_slot, "day": day, "group": "all_years"},
                )
        course_templates = [
            {"id": "PHY", "name": "Engineering Physics", "type": "Theory"},
            {"id": "MAT", "name": "Mathematics", "type": "Theory", "is_daily": True},
            {"id": "ENG", "name": "Technical English", "type": "Theory"},
            {"id": "CPL", "name": "C Programming Lab", "type": "Laboratory"},
            {"id": "PRC", "name": "Programming in C", "type": "Theory"},
            {
                "id": "DST",
                "name": "Data Structures",
                "type": "Theory",
                "is_daily": True,
            },
            {"id": "DEL", "name": "Digital Electronics", "type": "Theory"},
            {"id": "PHL", "name": "Physics Lab", "type": "Laboratory"},
            {"id": "WKP", "name": "Workshop Practice", "type": "Laboratory"},
            {"id": "OSY", "name": "Operating Systems", "type": "Theory"},
            {"id": "DBM", "name": "DBMS", "type": "Theory", "is_daily": True},
            {"id": "CNW", "name": "Computer Networks", "type": "Theory"},
            {"id": "OOP", "name": "Object Oriented Prog.", "type": "Theory"},
            {"id": "DMS", "name": "Discrete Mathematics", "type": "Special"},
            {"id": "MPR", "name": "Microprocessors", "type": "Theory"},
        ]
        course_teacher_mapping = {t["id"]: [] for t in course_templates}
        for i, course_id in enumerate(course_teacher_mapping.keys()):
            course_teacher_mapping[course_id] = teacher_id_list[
                i % len(teacher_id_list)
            ]
        for year in [1, 2, 3]:
            for sec_char in ["A", "B"]:
                section_key = f"{year}{sec_char}"
                current_section_id = section_ids[section_key]
                courses_for_this_section = (
                    course_templates * (51 // len(course_templates) + 1)
                )[:51]
                for i, course_tpl in enumerate(courses_for_this_section):
                    teacher_idx = (i + year + (1 if sec_char == "B" else 0)) % len(
                        teacher_id_list
                    )
                    await session.execute(
                        text("""INSERT INTO courses 
                        (course_id, course_name, teacher_id, year, department_id, course_type, section_id, continuous_periods, is_daily)
                        VALUES (:cid, :cname, :tid, :year, :dept_id, :ctype, :sid, :cp, :daily)
                    """),
                        {
                            "cid": f"{course_tpl['id']}{year}{sec_char}-{i}",
                            "cname": course_tpl["name"],
                            "tid": teacher_id_list[teacher_idx],
                            "year": year,
                            "dept_id": cs_dept_id,
                            "ctype": course_tpl["type"],
                            "sid": current_section_id,
                            "cp": 3 if course_tpl["type"] == "Laboratory" else 1,
                            "daily": 1 if course_tpl.get("is_daily") else 0,
                        },
                    )

    @rx.event
    async def check_login(self):
        from app.states.auth_state import AuthState

        auth_state = await self.get_state(AuthState)
        if not auth_state.is_logged_in:
            return rx.redirect("/login")
        self.current_user = auth_state.current_user
        return

    @rx.event
    async def load_teachers(self):
        async with rx.asession() as session:
            result = await session.execute(
                text("SELECT id, tuid, full_name FROM teachers ORDER BY tuid")
            )
            self.teachers = [dict(row) for row in result.mappings().all()]

    @rx.event
    async def add_teacher(self, form_data: dict):
        tuid = form_data.get("tuid")
        full_name = form_data.get("full_name")
        if not tuid or not full_name:
            yield rx.toast("Teacher ID and Full Name are required.", duration=3000)
            return
        async with rx.asession() as session:
            async with session.begin():
                res = await session.execute(
                    text("SELECT id FROM teachers WHERE tuid = :tuid"), {"tuid": tuid}
                )
                if res.first():
                    yield rx.toast(
                        f"Teacher with ID {tuid} already exists.", duration=3000
                    )
                    return
                await session.execute(
                    text(
                        "INSERT INTO teachers (tuid, full_name) VALUES (:tuid, :full_name)"
                    ),
                    {"tuid": tuid, "full_name": full_name},
                )
        yield rx.toast("Teacher added successfully!", duration=3000)
        yield DashboardState.load_teachers

    @rx.event
    async def delete_teacher(self, teacher_id: int):
        async with rx.asession() as session:
            async with session.begin():
                await session.execute(
                    text("DELETE FROM teachers WHERE id = :id"), {"id": teacher_id}
                )
        yield rx.toast("Teacher deleted.", duration=3000)
        yield DashboardState.load_teachers

    @rx.event
    async def load_rooms(self):
        async with rx.asession() as session:
            result = await session.execute(
                text(
                    "SELECT id, year, section_id, lh_number, capacity FROM rooms ORDER BY year, section_id, lh_number"
                )
            )
            self.rooms = [dict(row) for row in result.mappings().all()]

    @rx.event
    async def add_room(self, form_data: dict):
        year = form_data.get("year")
        section_id = form_data.get("section_id")
        lh_number = form_data.get("lh_number")
        capacity = form_data.get("capacity")
        if not all([year, section_id, lh_number, capacity]):
            yield rx.toast("All fields are required.", duration=3000)
            return
        async with rx.asession() as session:
            async with session.begin():
                res = await session.execute(
                    text(
                        "SELECT id FROM rooms WHERE lh_number = :lh_number AND year = :year AND section_id = :section_id"
                    ),
                    {
                        "lh_number": lh_number,
                        "year": int(year),
                        "section_id": section_id,
                    },
                )
                if res.first():
                    yield rx.toast(
                        f"Room {lh_number} for Year {year}, Section {section_id} already exists.",
                        duration=4000,
                    )
                    return
                await session.execute(
                    text(
                        "INSERT INTO rooms (year, section_id, lh_number, capacity) VALUES (:year, :section_id, :lh, :cap)"
                    ),
                    {
                        "year": int(year),
                        "section_id": section_id,
                        "lh": lh_number,
                        "cap": int(capacity),
                    },
                )
        yield rx.toast("Room added successfully!", duration=3000)
        yield DashboardState.load_rooms

    @rx.event
    async def delete_room(self, room_id: int):
        async with rx.asession() as session:
            async with session.begin():
                await session.execute(
                    text("DELETE FROM rooms WHERE id = :id"), {"id": room_id}
                )
        yield rx.toast("Room deleted.", duration=3000)
        yield DashboardState.load_rooms

    @rx.event
    async def load_timings(self):
        async with rx.asession() as session:
            result = await session.execute(
                text(
                    "SELECT id, time, day_of_week, timing_group FROM timings ORDER BY timing_group, day_of_week, time"
                )
            )
            self.timings = [dict(row) for row in result.mappings().all()]

    @rx.event
    async def add_timing(self, form_data: dict):
        time = form_data.get("time")
        days_of_week = form_data.get("days_of_week", [])
        timing_group = form_data.get("timing_group")
        if not isinstance(days_of_week, list):
            days_of_week = [days_of_week]
        if not time or not days_of_week or (not timing_group):
            yield rx.toast(
                "Time, Timing Group, and at least one Day of Week are required.",
                duration=3000,
            )
            return
        added_count = 0
        existing_count = 0
        async with rx.asession() as session:
            for day in days_of_week:
                try:
                    async with session.begin():
                        result = await session.execute(
                            text(
                                "SELECT id FROM timings WHERE time = :time AND day_of_week = :day AND timing_group = :group"
                            ),
                            {"time": time, "day": day, "group": timing_group},
                        )
                        if result.first():
                            existing_count += 1
                            continue
                        await session.execute(
                            text(
                                "INSERT INTO timings (time, day_of_week, timing_group) VALUES (:time, :day, :group)"
                            ),
                            {"time": time, "day": day, "group": timing_group},
                        )
                        added_count += 1
                except Exception as e:
                    logging.exception(f"Error adding timing: {e}")
                    if "UNIQUE constraint failed" in str(e):
                        existing_count += 1
                    else:
                        yield rx.toast(f"An error occurred: {e}", duration=5000)
        if added_count > 0:
            yield rx.toast(f"{added_count} timing(s) added.", duration=3000)
        if existing_count > 0:
            yield rx.toast(
                f"{existing_count} timing(s) already existed.",
                duration=3000,
                style={"background": "#FFA500"},
            )
        yield DashboardState.load_timings

    @rx.event
    async def delete_timing(self, timing_id: int):
        async with rx.asession() as session:
            async with session.begin():
                await session.execute(
                    text("DELETE FROM timings WHERE id = :id"), {"id": timing_id}
                )
        yield rx.toast("Timing deleted.", duration=3000)
        yield DashboardState.load_timings

    @rx.event
    async def handle_timing_upload(self, files: list[rx.UploadFile]):
        if not files:
            self.upload_status = "No file selected."
            return
        self.upload_status = "Processing..."
        yield
        timings_to_add = {
            "year_1_and_4": [
                ("8:30-9:15", "Period 1"),
                ("9:15-10:00", "Period 2"),
                ("10:15-11:00", "Period 3"),
                ("11:00-11:45", "Period 4"),
                ("11:45-12:30", "Period 5"),
                ("1:15-2:00", "Period 6"),
                ("2:00-2:45", "Period 7"),
                ("3:00-3:45", "Period 8"),
                ("3:45-4:30", "Period 9"),
            ],
            "year_2_and_3": [
                ("8:30-9:15", "Period 1"),
                ("9:15-10:00", "Period 2"),
                ("10:00-10:45", "Period 3"),
                ("11:00-11:45", "Period 4"),
                ("11:45-12:30", "Period 5"),
                ("12:30-1:15", "Period 6"),
                ("2:00-2:45", "Period 7"),
                ("2:45-3:30", "Period 8"),
                ("3:45-4:30", "Period 9"),
            ],
        }
        days_of_week = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
        ]
        added_count = 0
        existing_count = 0
        async with rx.asession() as session:
            for timing_group, times in timings_to_add.items():
                for time_slot, period_name in times:
                    for day in days_of_week:
                        try:
                            async with session.begin():
                                res = await session.execute(
                                    text(
                                        "SELECT id FROM timings WHERE time = :time AND day_of_week = :day AND timing_group = :group"
                                    ),
                                    {
                                        "time": time_slot,
                                        "day": day,
                                        "group": timing_group,
                                    },
                                )
                                if res.first():
                                    existing_count += 1
                                    continue
                                await session.execute(
                                    text(
                                        "INSERT INTO timings (time, day_of_week, timing_group) VALUES (:time, :day, :group)"
                                    ),
                                    {
                                        "time": time_slot,
                                        "day": day,
                                        "group": timing_group,
                                    },
                                )
                                added_count += 1
                        except Exception as e:
                            logging.exception(f"Error adding timing: {e}")
                            if "UNIQUE constraint failed" in str(e):
                                existing_count += 1
        self.upload_status = (
            f"Upload complete! Added: {added_count}, Existing: {existing_count}"
        )
        yield rx.toast(
            "Timings have been populated from the official source.", duration=5000
        )
        yield DashboardState.load_timings

    @rx.event
    async def load_courses(self):
        async with rx.asession() as session:
            query = text("""SELECT c.*, t.full_name as teacher_name, d.name as department_name, s.section_id as section_name
                          FROM courses c
                          LEFT JOIN teachers t ON c.teacher_id = t.id
                          LEFT JOIN departments d ON c.department_id = d.id
                          LEFT JOIN sections s ON c.section_id = s.id
                          ORDER BY c.course_id""")
            result = await session.execute(query)
            self.courses = [dict(row) for row in result.mappings().all()]

    @rx.event
    async def add_course(self, form_data: dict):
        required_fields = [
            "course_id",
            "course_name",
            "teacher_id",
            "department_id",
            "course_type",
            "section_id",
        ]
        if not all((form_data.get(k) for k in required_fields)):
            yield rx.toast("All course fields are required.", duration=3000)
            return
        try:
            async with rx.asession() as session:
                async with session.begin():
                    section_res = await session.execute(
                        text("SELECT year FROM sections WHERE id = :sid"),
                        {"sid": int(form_data["section_id"])},
                    )
                    year = section_res.scalar_one_or_none()
                    if not year:
                        yield rx.toast(
                            "Could not find year for the selected section.",
                            duration=3000,
                        )
                        return
                    params = {
                        "cid": form_data["course_id"],
                        "cname": form_data["course_name"],
                        "tid": int(form_data["teacher_id"]),
                        "year": year,
                        "did": int(form_data["department_id"]),
                        "ctype": form_data["course_type"],
                        "sid": int(form_data["section_id"]),
                        "is_daily": 1 if form_data.get("is_daily") else 0,
                        "cont_p": int(form_data.get("continuous_periods", 1)),
                        "is_comb": 1 if form_data.get("is_combined_class") else 0,
                        "comb_g": form_data.get("combined_class_group"),
                        "is_fixed": 1 if form_data.get("is_fixed_teacher") else 0,
                    }
                    await session.execute(
                        text("""INSERT INTO courses (
                                   course_id, course_name, teacher_id, year, department_id, 
                                   course_type, section_id, is_daily, continuous_periods,
                                   is_combined_class, combined_class_group, is_fixed_teacher
                               )
                               VALUES (
                                   :cid, :cname, :tid, :year, :did, :ctype, :sid, :is_daily,
                                   :cont_p, :is_comb, :comb_g, :is_fixed
                               )"""),
                        params,
                    )
            yield rx.toast("Course added!", duration=3000)
            yield DashboardState.load_courses
        except Exception as e:
            logging.exception(e)
            yield rx.toast(f"An error occurred: {e}", duration=3000)

    @rx.event
    async def delete_course(self, course_id: int):
        async with rx.asession() as session:
            async with session.begin():
                await session.execute(
                    text("DELETE FROM courses WHERE id = :id"), {"id": course_id}
                )
        yield rx.toast("Course deleted.", duration=3000)
        yield DashboardState.load_courses

    @rx.event
    async def load_departments(self):
        async with rx.asession() as session:
            query = text("SELECT id, name FROM departments ORDER BY name")
            result = await session.execute(query)
            self.departments = [dict(row) for row in result.mappings().all()]

    @rx.event
    async def add_department(self, form_data: dict):
        dept_name = form_data.get("department_name")
        if not dept_name:
            yield rx.toast("Department Name is required.", duration=3000)
            return
        async with rx.asession() as session:
            async with session.begin():
                res = await session.execute(
                    text("SELECT id FROM departments WHERE name = :name"),
                    {"name": dept_name},
                )
                if res.first():
                    yield rx.toast(
                        f"Department '{dept_name}' already exists.", duration=3000
                    )
                    return
                await session.execute(
                    text("INSERT INTO departments (name) VALUES (:name)"),
                    {"name": dept_name},
                )
        yield rx.toast("Department added!", duration=3000)
        yield DashboardState.load_departments

    @rx.event
    async def delete_department(self, dept_id: int):
        async with rx.asession() as session:
            async with session.begin():
                await session.execute(
                    text("DELETE FROM departments WHERE id = :id"), {"id": dept_id}
                )
        yield rx.toast("Department deleted.", duration=3000)
        yield DashboardState.load_departments

    @rx.event
    async def load_sections(self):
        async with rx.asession() as session:
            query = text("""SELECT s.id, s.section_id, s.department_id, s.year, 
                                 s.periods_monday, s.periods_tuesday, s.periods_wednesday, 
                                 s.periods_thursday, s.periods_friday, s.periods_saturday, 
                                 d.name as department_name 
                          FROM sections s
                          LEFT JOIN departments d ON s.department_id = d.id
                          ORDER BY d.name, s.year, s.section_id""")
            result = await session.execute(query)
            self.sections = [dict(row) for row in result.mappings().all()]

    @rx.event
    async def add_section(self, form_data: dict):
        section_id = form_data.get("section_id")
        department_id = form_data.get("department_id")
        year = form_data.get("year")
        if not all([section_id, department_id, year]):
            yield rx.toast(
                "Year, Section ID and Department are required.", duration=3000
            )
            return
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]
        periods = {day: int(form_data.get(f"periods_{day}", 0) or 0) for day in days}
        async with rx.asession() as session:
            async with session.begin():
                res = await session.execute(
                    text(
                        "SELECT id FROM sections WHERE section_id = :sid AND department_id = :did AND year = :year"
                    ),
                    {"sid": section_id, "did": int(department_id), "year": int(year)},
                )
                if res.first():
                    yield rx.toast(
                        f"Section '{section_id}' for year {year} in this department already exists.",
                        duration=3000,
                    )
                    return
                await session.execute(
                    text("""INSERT INTO sections (section_id, department_id, year,
                                                periods_monday, periods_tuesday, periods_wednesday, 
                                                periods_thursday, periods_friday, periods_saturday)
                          VALUES (:sid, :did, :year, :p_mon, :p_tue, :p_wed, :p_thu, :p_fri, :p_sat)"""),
                    {
                        "sid": section_id,
                        "did": int(department_id),
                        "year": int(year),
                        "p_mon": periods["monday"],
                        "p_tue": periods["tuesday"],
                        "p_wed": periods["wednesday"],
                        "p_thu": periods["thursday"],
                        "p_fri": periods["friday"],
                        "p_sat": periods["saturday"],
                    },
                )
        yield rx.toast("Section added!", duration=3000)
        yield DashboardState.load_sections

    @rx.event
    async def delete_section(self, section_id: int):
        async with rx.asession() as session:
            async with session.begin():
                await session.execute(
                    text("DELETE FROM sections WHERE id = :id"), {"id": section_id}
                )
        yield rx.toast("Section deleted.", duration=3000)
        yield DashboardState.load_sections

    @rx.event
    async def handle_logout(self):
        auth_state = await self.get_state(AuthState)
        auth_state.is_logged_in = False
        auth_state.current_user = ""
        self.reset()
        return rx.redirect("/")