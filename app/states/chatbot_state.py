import reflex as rx
from typing import TypedDict
from sqlalchemy import text
import asyncio
from app.states.timetable_state import TimetableGenerationState
import re


class Message(TypedDict):
    role: str
    content: str


class ChatbotState(rx.State):
    is_chat_open: bool = False
    messages: list[Message] = []
    processing: bool = False

    def _find_item(self, items: list, condition):
        return next((item for item in items if condition(item)), None)

    @rx.event
    def toggle_chat(self):
        self.is_chat_open = not self.is_chat_open
        if self.is_chat_open and (not self.messages):
            self.messages = [
                {
                    "role": "assistant",
                    "content": """Hello! I'm the HOD Assistant. After a timetable is generated, you can ask me questions like:

- 'Show section A schedule'
- 'When does Lakshmi Iyer teach?'
- 'Who teaches C Programming Lab?'
- 'Is Mathematics I daily for section A?'
- 'List all laboratory courses'
- 'Which room is C Programming Lab class in?'
- 'When is Engineering Physics class?'
- 'Who is free now?'

How can I help you today?""",
                }
            ]

    async def _process_query(self, query: str) -> str:
        timetable_state = await self.get_state(TimetableGenerationState)
        if (
            not timetable_state.timetable_generated
            or not timetable_state.best_chromosome
        ):
            return "The timetable has not been generated yet. Please generate it first from the 'Generate Timetable' page."
        query = query.lower()
        teacher_schedule_match = re.search(
            "(when does|schedule for|where is) (prof\\.?|dr\\.?|mrs\\.?|mr\\.?|ms\\.?\\s*)?(\\w+(\\s+\\w+)?)(\\'s)?\\s*(teach|work|have classes|schedule)?",
            query,
        )
        who_teaches_match = re.search("who teaches (.*)", query)
        section_schedule_match = re.search("show (section\\s*(\\w+)) schedule", query)
        how_many_match = re.search("how many (\\w+)s are there", query)
        daily_course_match = re.search("is (.*?) daily for section (.*)", query)
        combined_class_match = re.search("when is (the )?(.*?) combined class", query)
        continuous_periods_match = re.search(
            "which courses have continuous periods", query
        )
        teacher_courses_match = re.search(
            "what courses does (prof\\.?\\s*\\S+|\\S+) teach", query
        )
        course_schedule_match = re.search("(when is|schedule for) (.*?) class", query)
        who_teaches_match = re.search("who teaches (.*)", query)
        section_schedule_match = re.search("show (section (\\w+)) schedule", query)
        free_now_match = re.search("who is free now", query)
        if free_now_match:
            from datetime import datetime

            now = datetime.now()
            current_time_str = now.strftime("%H:%M")
            current_day = now.strftime("%A")
            timing = self._find_item(
                timetable_state._timings,
                lambda t: t["day_of_week"] == current_day
                and t["time"].split("-")[0]
                <= current_time_str
                <= t["time"].split("-")[1],
            )
            if not timing:
                return f"There are no classes scheduled right now ({current_time_str} on {current_day}). All teachers are likely free."
            timing_id = timing["id"]
            busy_teacher_ids = {
                gene["teacher_id"]
                for gene in timetable_state.best_chromosome["genes"]
                if gene["timing_id"] == timing_id
            }
            all_teacher_ids = {teacher["id"] for teacher in timetable_state._teachers}
            free_teacher_ids = all_teacher_ids - busy_teacher_ids
            if not free_teacher_ids:
                return f"No teachers are free right now ({timing['time']} on {current_day})."
            free_teachers = [
                self._find_item(timetable_state._teachers, lambda t: t["id"] == tid)
                for tid in free_teacher_ids
            ]
            free_teacher_names = sorted([t["full_name"] for t in free_teachers if t])
            response = (
                f"### Teachers free right now ({timing['time']} on {current_day}):\n\n- "
                + """
- """.join(free_teacher_names)
            )
            return response
        if teacher_schedule_match:
            teacher_name = teacher_schedule_match.group(3).strip()
            teacher = self._find_item(
                timetable_state._teachers,
                lambda t: teacher_name in t["full_name"].lower(),
            )
            if not teacher:
                return f"Sorry, I couldn't find a teacher named '{teacher_name}'."
            day_match = re.search(
                "on (monday|tuesday|wednesday|thursday|friday|saturday)", query
            )
            day_filter = day_match.group(1).capitalize() if day_match else None
            results = []
            for gene in timetable_state.best_chromosome["genes"]:
                if gene["teacher_id"] == teacher["id"]:
                    timing = self._find_item(
                        timetable_state._timings, lambda t: t["id"] == gene["timing_id"]
                    )
                    if day_filter and timing and (timing["day_of_week"] != day_filter):
                        continue
                    course = self._find_item(
                        timetable_state._courses, lambda c: c["id"] == gene["course_id"]
                    )
                    section = self._find_item(
                        timetable_state._sections,
                        lambda s: s["id"] == gene["section_id"],
                    )
                    room = self._find_item(
                        timetable_state._rooms, lambda r: r["id"] == gene["room_id"]
                    )
                    if all([course, timing, section, room]):
                        results.append(
                            f"- **{course['course_name']}** for Section **{section['section_id']}** on *{timing['day_of_week']}* at *{timing['time']}* in room *{room['lh_number']}*"
                        )
            if results:
                day_str = f" on {day_filter}" if day_filter else ""
                return (
                    f"### Schedule for {teacher['full_name']}{day_str}:\n\n"
                    + """
""".join(sorted(results))
                )
            return f"{teacher['full_name']} has no classes scheduled{(f' on {day_filter}' if day_filter else '')}."
        if who_teaches_match:
            course_name_query = who_teaches_match.group(1).strip().rstrip("?").strip()
            course = self._find_item(
                timetable_state._courses,
                lambda c: course_name_query in c["course_name"].lower(),
            )
            if not course:
                return f"I couldn't find a course named '{course_name_query}'."
            teacher = self._find_item(
                timetable_state._teachers, lambda t: t["id"] == course["teacher_id"]
            )
            if teacher:
                return (
                    f"**{teacher['full_name']}** teaches **{course['course_name']}**."
                )
            return f"I couldn't find who teaches {course['course_name']}."
        if how_many_match:
            item_type = how_many_match.group(1)
            count = 0
            if "sec" in item_type:
                count = len(timetable_state._sections)
                return f"There are {count} sections in total."
            elif "teacher" in item_type:
                count = len(timetable_state._teachers)
                return f"There are {count} teachers in total."
            elif "course" in item_type:
                count = len(timetable_state._courses)
                return f"There are {count} courses in total."
            elif "room" in item_type:
                count = len(timetable_state._rooms)
                return f"There are {count} rooms in total."
            elif "department" in item_type:
                count = len(timetable_state._departments)
                return f"There are {count} departments in total."
            return f"I'm not sure how to count '{item_type}s'."
        if teacher_schedule_match:
            teacher_name = teacher_schedule_match.group(3).strip()
            teacher = self._find_item(
                timetable_state._teachers,
                lambda t: teacher_name in t["full_name"].lower(),
            )
            if not teacher:
                return f"Sorry, I couldn't find a teacher named '{teacher_name}'."
            results = []
            for gene in timetable_state.best_chromosome["genes"]:
                if gene["teacher_id"] == teacher["id"]:
                    course = self._find_item(
                        timetable_state._courses, lambda c: c["id"] == gene["course_id"]
                    )
                    timing = self._find_item(
                        timetable_state._timings, lambda t: t["id"] == gene["timing_id"]
                    )
                    section = self._find_item(
                        timetable_state._sections,
                        lambda s: s["id"] == gene["section_id"],
                    )
                    if all([course, timing, section]):
                        results.append(
                            f"- **{course['course_name']}** for Section **{section['section_id']}** on *{timing['day_of_week']}* at *{timing['time']}*"
                        )
        if section_schedule_match:
            section_id_str = section_schedule_match.group(2).strip()
            section = self._find_item(
                timetable_state._sections,
                lambda s: section_id_str == s["section_id"].lower(),
            )
            if not section:
                return f"Sorry, I couldn't find Section '{section_id_str}'."
            day_match = re.search(
                "on (monday|tuesday|wednesday|thursday|friday|saturday)", query
            )
            day_filter = day_match.group(1).capitalize() if day_match else None
            results = []
            for gene in timetable_state.best_chromosome["genes"]:
                if gene["section_id"] == section["id"]:
                    timing = self._find_item(
                        timetable_state._timings, lambda t: t["id"] == gene["timing_id"]
                    )
                    if day_filter and timing and (timing["day_of_week"] != day_filter):
                        continue
                    course = self._find_item(
                        timetable_state._courses, lambda c: c["id"] == gene["course_id"]
                    )
                    teacher = self._find_item(
                        timetable_state._teachers,
                        lambda t: t["id"] == gene["teacher_id"],
                    )
                    room = self._find_item(
                        timetable_state._rooms, lambda r: r["id"] == gene["room_id"]
                    )
                    if all([course, teacher, timing, room]):
                        results.append(
                            f"- *{timing['day_of_week']}* at *{timing['time']}*: **{course['course_name']}** with *{teacher['full_name']}* in *{room['lh_number']}*"
                        )
            if results:
                day_str = f" on {day_filter}" if day_filter else ""
                return (
                    f"### Schedule for Section {section['section_id']}{day_str}:\n\n"
                    + """
""".join(sorted(results))
                )
            return f"Section {section['section_id']} has no classes scheduled{(f' on {day_filter}' if day_filter else '')}."
        if daily_course_match:
            course_name = daily_course_match.group(1).strip()
            section_id_str = daily_course_match.group(2).strip().rstrip("?").strip()
            section = self._find_item(
                timetable_state._sections,
                lambda s: section_id_str == s["section_id"].lower(),
            )
            if not section:
                return f"Could not find Section '{section_id_str}'."
            course = self._find_item(
                timetable_state._courses,
                lambda c: course_name in c["course_name"].lower()
                and c.get("section_id") == section["id"],
            )
            if course:
                return (
                    f"Yes, **{course['course_name']}** is a daily course for Section **{section['section_id']}**."
                    if course.get("is_daily")
                    else f"No, **{course['course_name']}** is not configured as a daily course for Section **{section['section_id']}**."
                )
            return (
                f"Could not find course '{course_name}' for Section '{section_id_str}'."
            )
        if combined_class_match:
            course_name = combined_class_match.group(2).strip()
            course = self._find_item(
                timetable_state._courses,
                lambda c: course_name in c["course_name"].lower()
                and c.get("is_combined_class"),
            )
            if course:
                gene = self._find_item(
                    timetable_state.best_chromosome["genes"],
                    lambda g: g["course_id"] == course["id"],
                )
                if gene:
                    timing = self._find_item(
                        timetable_state._timings, lambda t: t["id"] == gene["timing_id"]
                    )
                    room = self._find_item(
                        timetable_state._rooms, lambda r: r["id"] == gene["room_id"]
                    )
                    teacher = self._find_item(
                        timetable_state._teachers,
                        lambda t: t["id"] == gene["teacher_id"],
                    )
                    if all([timing, room, teacher]):
                        return f"The combined class for **{course['course_name']}** is on *{timing['day_of_week']}* at *{timing['time']}* in room *{room['lh_number']}* with *{teacher['full_name']}*."
            return f"Could not find a combined class schedule for '{course_name}'."
        if continuous_periods_match:
            courses = [
                c
                for c in timetable_state._courses
                if c.get("continuous_periods", 1) > 1
            ]
            if not courses:
                return "No courses are configured with continuous periods."
            response = """### Courses with Continuous Periods:

"""
            for course in courses:
                response += f"- **{course['course_name']}** ({course.get('continuous_periods')} periods)\n"
            return response
        if teacher_courses_match:
            teacher_name = teacher_courses_match.group(1).strip()
            teacher = self._find_item(
                timetable_state._teachers,
                lambda t: teacher_name in t["full_name"].lower(),
            )
            if not teacher:
                return f"Could not find teacher: {teacher_name}"
            courses = [
                c for c in timetable_state._courses if c["teacher_id"] == teacher["id"]
            ]
            if not courses:
                return f"{teacher['full_name']} is not assigned to any courses."
            response = f"### Courses taught by {teacher['full_name']}:\n\n"
            for course in courses:
                response += f"- **{course['course_name']}** ({course['course_id']})\n"
            return response
        lab_courses_match = re.search("list all laboratory courses", query)
        room_query_match = re.search("which room is (.*?) class in", query)
        course_timing_match = re.search("when is (.*?) class", query)
        free_teachers_match = re.search(
            "who is free at (\\d{1,2}:\\d{2}(?:-\\d{1,2}:\\d{2})?) on (monday|tuesday|wednesday|thursday|friday|saturday)",
            query,
        )
        if free_teachers_match:
            time_query = free_teachers_match.group(1)
            day_query = free_teachers_match.group(2).capitalize()
            timing = self._find_item(
                timetable_state._timings,
                lambda t: t["time"] == time_query and t["day_of_week"] == day_query,
            )
            if not timing:
                return f"I couldn't find the time slot {time_query} on {day_query}. Please use the exact time format (e.g., 08:30-09:15)."
            timing_id = timing["id"]
            busy_teacher_ids = {
                gene["teacher_id"]
                for gene in timetable_state.best_chromosome["genes"]
                if gene["timing_id"] == timing_id
            }
            all_teacher_ids = {teacher["id"] for teacher in timetable_state._teachers}
            free_teacher_ids = all_teacher_ids - busy_teacher_ids
            if not free_teacher_ids:
                return f"No teachers are free at {time_query} on {day_query}."
            free_teachers = [
                self._find_item(timetable_state._teachers, lambda t: t["id"] == tid)
                for tid in free_teacher_ids
            ]
            free_teacher_names = sorted([t["full_name"] for t in free_teachers if t])
            response = (
                f"### Teachers free at {time_query} on {day_query}:\n\n- "
                + """
- """.join(free_teacher_names)
            )
            return response
        if lab_courses_match:
            lab_courses = [
                c
                for c in timetable_state._courses
                if c.get("course_type") == "Laboratory"
            ]
            if not lab_courses:
                return "There are no laboratory courses."
            response = """### Laboratory Courses:

"""
            for course in lab_courses:
                response += f"- **{course['course_name']}** ({course['course_id']})\n"
            return response
        if room_query_match:
            course_name = room_query_match.group(1).strip()
            genes = [
                g
                for g in timetable_state.best_chromosome["genes"]
                if self._find_item(
                    timetable_state._courses,
                    lambda c: c["id"] == g["course_id"]
                    and course_name in c["course_name"].lower(),
                )
            ]
            if not genes:
                return f"I couldn't find any schedule for '{course_name}'."
            results = []
            for gene in genes:
                room = self._find_item(
                    timetable_state._rooms, lambda r: r["id"] == gene["room_id"]
                )
                timing = self._find_item(
                    timetable_state._timings, lambda t: t["id"] == gene["timing_id"]
                )
                section = self._find_item(
                    timetable_state._sections, lambda s: s["id"] == gene["section_id"]
                )
                if room and timing and section:
                    results.append(
                        f"- Section **{section['section_id']}** has **{course_name}** in room **{room['lh_number']}** on *{timing['day_of_week']}* at *{timing['time']}*."
                    )
            return (
                """
""".join(results)
                if results
                else f"No room assigned for '{course_name}'."
            )
        if course_timing_match:
            course_name = course_timing_match.group(1).strip()
            genes = [
                g
                for g in timetable_state.best_chromosome["genes"]
                if self._find_item(
                    timetable_state._courses,
                    lambda c: c["id"] == g["course_id"]
                    and course_name in c["course_name"].lower(),
                )
            ]
            if not genes:
                return f"I couldn't find any schedule for '{course_name}'."
            results = []
            for gene in genes:
                timing = self._find_item(
                    timetable_state._timings, lambda t: t["id"] == gene["timing_id"]
                )
                section = self._find_item(
                    timetable_state._sections, lambda s: s["id"] == gene["section_id"]
                )
                if timing and section:
                    results.append(
                        f"- Section **{section['section_id']}** has **{course_name}** on *{timing['day_of_week']}* at *{timing['time']}*."
                    )
            return (
                """
""".join(results)
                if results
                else f"No timing found for '{course_name}'."
            )
        return """I'm sorry, I don't understand that question. You can ask things like:
- 'Show section A schedule'
- 'Show section B schedule on Tuesday'
- 'When does Prof. Smith teach?'
- 'What is the schedule for Lakshmi Iyer on Monday?'
- 'Who teaches Data Structures?'
- 'Is Mathematics daily for section A?'
- 'List all laboratory courses'
- 'Which room is Mathematics class in?'
- 'When is Physics class?'
- 'Who is free at 08:30-09:15 on Monday?'"""

    @rx.event
    async def handle_submit(self, form_data: dict):
        query = form_data.get("query")
        if not query:
            return
        self.messages.append({"role": "user", "content": query})
        self.processing = True
        yield
        response = await self._process_query(query)
        await asyncio.sleep(1)
        self.messages.append({"role": "assistant", "content": response})
        self.processing = False