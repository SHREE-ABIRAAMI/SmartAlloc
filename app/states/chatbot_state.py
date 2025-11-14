import reflex as rx
import re
import datetime
import logging
from typing import TypedDict, Coroutine, Callable
from collections import defaultdict
from app.states.timetable_generation_state import TimetableGenerationState, Course


class Message(TypedDict):
    role: str
    content: str


class ChatbotState(rx.State):
    show_chat: bool = False
    messages: list[Message] = [
        {
            "role": "assistant",
            "content": """Hello! I'm the HOD Assistant. Once the timetable is generated, you can ask me anything about it. Try queries like:
- *'What is the schedule for Prof. Snape?'*
- *'Show me the schedule for section 1A on Tuesday.'*
- *'What does section 2B have on Friday?'*
- *'Who teaches Potions?'*
- *'Which courses does Prof. Dumbledore teach?'*
- *'How many continuous periods does section 1A have?'*
- *'Where is the Potions class?'*
- *'When is the Defense Against the Dark Arts class?'*
- *'Who is free at 10 AM on Wednesday?'*
- *'List all laboratory courses.'*
- *'How many teachers are there?'*""",
        }
    ]
    is_processing: bool = False

    @rx.event
    def toggle_chat(self):
        self.show_chat = not self.show_chat

    @rx.event
    def handle_submit(self, form_data: dict[str, str]):
        query = form_data.get("query")
        if not query or self.is_processing:
            return
        self.messages.append({"role": "user", "content": query})
        self.is_processing = True
        return ChatbotState.process_query(query)

    @rx.event
    def add_assistant_message(self, content: str):
        self.messages.append({"role": "assistant", "content": content})
        self.is_processing = False

    def _find_item(self, collection: list[dict], key: str, value: str) -> dict | None:
        value_lower = value.lower().strip()
        for item in collection:
            if str(item.get(key, "")).lower().strip() == value_lower:
                return item
        return None

    async def _handle_teacher_schedule(
        self, match: re.Match, tt_state: TimetableGenerationState
    ) -> str:
        teacher_name = match.group(1).strip()
        teacher = self._find_item(tt_state.teachers, "full_name", teacher_name)
        if not teacher:
            return f"Sorry, I couldn't find a teacher named '{teacher_name}'."
        schedule = sorted(
            [
                slot
                for slot in tt_state.timetable
                if slot["teacher"] == teacher["full_name"]
            ],
            key=lambda x: (tt_state.days_of_week.index(x["day"]), x["start_time"]),
        )
        if not schedule:
            return f"It seems {teacher_name} has no classes assigned."
        response = f"**Schedule for {teacher_name}:**\n\n"
        for day in tt_state.days_of_week:
            day_schedule = [s for s in schedule if s["day"] == day]
            if day_schedule:
                response += f"**{day}:**\n"
                for slot in day_schedule:
                    response += f"- **{slot['start_time']}-{slot['end_time']}:** {slot['course']} (Section {slot['section']}) in Room {slot['room']}\n"
                response += """
"""
        return response

    async def _handle_section_schedule(
        self, match: re.Match, tt_state: TimetableGenerationState
    ) -> str:
        section_name = match.group(1).strip()
        day_query = match.group(3).strip().capitalize() if match.group(3) else None
        section = self._find_item(tt_state.sections, "name", section_name)
        if not section:
            return f"Sorry, I couldn't find a section named '{section_name}'."
        schedule = sorted(
            [slot for slot in tt_state.timetable if slot["section"] == section["name"]],
            key=lambda x: (tt_state.days_of_week.index(x["day"]), x["start_time"]),
        )
        if not schedule:
            return f"It seems Section {section_name} has no classes assigned."
        days_to_show = (
            [day_query]
            if day_query and day_query in tt_state.days_of_week
            else tt_state.days_of_week
        )
        response = f"**Schedule for Section {section_name}"
        if day_query:
            response += f" on {day_query}"
        response += """:**

"""
        found_classes = False
        for day in days_to_show:
            day_schedule = [s for s in schedule if s["day"] == day]
            if day_schedule:
                found_classes = True
                response += f"**{day}:**\n"
                for slot in day_schedule:
                    response += f"- **{slot['start_time']}-{slot['end_time']}:** {slot['course']} ({slot['teacher']}) in Room {slot['room']}\n"
                response += """
"""
        if not found_classes:
            return (
                f"Section {section_name} has no classes scheduled on {day_query}."
                if day_query
                else f"Section {section_name} has no classes scheduled."
            )
        return response

    async def _handle_who_teaches(
        self, match: re.Match, tt_state: TimetableGenerationState
    ) -> str:
        course_name = match.group(1).strip()
        slots = [
            slot
            for slot in tt_state.timetable
            if slot["course"].lower() == course_name.lower()
        ]
        if not slots:
            return f"I couldn't find any information about the course '{course_name}'. Is it in the timetable?"
        teachers = sorted(list(set((slot["teacher"] for slot in slots))))
        return f"**{course_name}** is taught by: **{', '.join(teachers)}**."

    async def _handle_teacher_courses(
        self, match: re.Match, tt_state: TimetableGenerationState
    ) -> str:
        teacher_name = match.group(1).strip()
        teacher = self._find_item(tt_state.teachers, "full_name", teacher_name)
        if not teacher:
            return f"Sorry, I couldn't find a teacher named '{teacher_name}'."
        courses = sorted(
            list(
                set(
                    (
                        slot["course"]
                        for slot in tt_state.timetable
                        if slot["teacher"] == teacher["full_name"]
                    )
                )
            )
        )
        if not courses:
            return (
                f"{teacher_name} is not teaching any courses in the current timetable."
            )
        return (
            f"**{teacher_name}** teaches the following courses:\n- "
            + """
- """.join(courses)
        )

    async def _handle_count(
        self, match: re.Match, tt_state: TimetableGenerationState
    ) -> str:
        item_type = match.group(1).lower().strip()
        counts = {
            "teacher": ("teachers", len(tt_state.teachers)),
            "section": ("sections", len(tt_state.sections)),
            "course": ("courses", len(tt_state.courses)),
            "subject": ("subjects (courses)", len(tt_state.courses)),
            "room": ("rooms", len(tt_state.rooms)),
            "department": ("departments", len(tt_state.departments)),
        }
        for key, (plural, count) in counts.items():
            if item_type.startswith(key):
                return f"There are **{count}** {plural} in total."
        return "I can count teachers, sections, courses, rooms, and departments."

    async def _handle_teacher_free(
        self, match: re.Match, tt_state: TimetableGenerationState
    ) -> str:
        time_str = match.group(1).strip()
        day_str = (
            match.group(3).strip().capitalize()
            if match.group(3)
            else datetime.date.today().strftime("%A")
        )
        if day_str not in tt_state.days_of_week:
            return f"Sorry, '{day_str}' is not a valid school day in the timetable."
        try:
            query_time = datetime.datetime.strptime(time_str.upper(), "%I %p").time()
        except ValueError as e:
            logging.exception(f"Error parsing time: {e}")
            try:
                query_time = datetime.datetime.strptime(time_str, "%H:%M").time()
            except ValueError as e2:
                logging.exception(f"Error parsing time again: {e2}")
                return "Please use a valid time format like '10 AM' or '14:00'."
        busy_teachers = {
            slot["teacher"]
            for slot in tt_state.timetable
            if slot["day"] == day_str
            and datetime.datetime.strptime(slot["start_time"], "%H:%M").time()
            <= query_time
            < datetime.datetime.strptime(slot["end_time"], "%H:%M").time()
        }
        all_teachers = {t["full_name"] for t in tt_state.teachers}
        free_teachers = sorted(list(all_teachers - busy_teachers))
        if not free_teachers:
            return f"It seems no teachers are free at {time_str} on {day_str}."
        return (
            f"**Teachers free at {time_str} on {day_str}:**\n- "
            + """
- """.join(free_teachers)
        )

    async def _handle_course_timing_or_location(
        self, match: re.Match, tt_state: TimetableGenerationState
    ) -> str:
        query_type = match.group(1).lower()
        course_name = match.group(2).strip()
        slots = [
            s for s in tt_state.timetable if s["course"].lower() == course_name.lower()
        ]
        if not slots:
            return f"I couldn't find '{course_name}' in the timetable."
        info = defaultdict(list)
        if query_type == "when":
            for slot in slots:
                info[
                    f"**{slot['day']}** from **{slot['start_time']} to {slot['end_time']}**"
                ].append(f"Section {slot['section']}")
            response = f"**Timings for {course_name}:**\n\n"
            for timing, sections in info.items():
                response += f"- {timing} (for {', '.join(sorted(sections))})\n"
            return response
        elif query_type == "where":
            for slot in slots:
                info[f"Room **{slot['room']}**"].append(
                    f"on {slot['day']} for Section {slot['section']}"
                )
            response = f"**Locations for {course_name}:**\n\n"
            for location, details in info.items():
                response += f"- In {location} ({', '.join(sorted(details))})\n"
            return response
        return "I can find when or where a class is."

    async def _handle_lab_courses(
        self, match: re.Match, tt_state: TimetableGenerationState
    ) -> str:
        lab_courses = [
            course["name"] for course in tt_state.courses if course.get("is_lab")
        ]
        if not lab_courses:
            return "There are no laboratory courses specified in the data."
        return """**Laboratory Courses:**
- """ + """
- """.join(sorted(lab_courses))

    async def _handle_continuous_periods(
        self, match: re.Match, tt_state: TimetableGenerationState
    ) -> str:
        section_name = match.group(1).strip()
        section = self._find_item(tt_state.sections, "name", section_name)
        if not section:
            return f"Sorry, I couldn't find a section named '{section_name}'."
        schedule_by_day = defaultdict(list)
        for slot in tt_state.timetable:
            if slot["section"] == section["name"]:
                schedule_by_day[slot["day"]].append(slot)
        response = f"**Continuous periods for Section {section_name}:**\n\n"
        found_continuous = False
        for day in tt_state.days_of_week:
            day_schedule = sorted(schedule_by_day[day], key=lambda x: x["start_time"])
            if len(day_schedule) < 2:
                continue
            continuous_blocks = []
            current_block = [day_schedule[0]]
            for i in range(1, len(day_schedule)):
                if day_schedule[i]["start_time"] == current_block[-1]["end_time"]:
                    current_block.append(day_schedule[i])
                else:
                    if len(current_block) > 1:
                        continuous_blocks.append(current_block)
                    current_block = [day_schedule[i]]
            if len(current_block) > 1:
                continuous_blocks.append(current_block)
            if continuous_blocks:
                found_continuous = True
                response += f"**{day}:**\n"
                for block in continuous_blocks:
                    start = block[0]["start_time"]
                    end = block[-1]["end_time"]
                    courses = " -> ".join([c["course"] for c in block])
                    response += f"- {len(block)} periods ({start}-{end}): {courses}\n"
                response += """
"""
        if not found_continuous:
            return f"Section {section_name} has no continuous periods scheduled."
        return response

    @rx.event(background=True)
    async def process_query(self, query: str):
        async with self:
            timetable_state = await self.get_state(TimetableGenerationState)
            response = "I'm sorry, I can't answer that right now. The timetable might not be generated yet."
            if timetable_state.timetable:
                query_patterns: dict[
                    str,
                    Callable[
                        [re.Match, TimetableGenerationState], Coroutine[None, None, str]
                    ],
                ] = {
                    "(?:schedule for|show schedule for|what is the schedule for) section ([\\w\\d-]+)(?: on (\\w+))?\\?*": self._handle_section_schedule,
                    "(?:what is the schedule for|schedule for|show schedule for) (prof\\.?\\s*\\w+\\s*\\w+)\\?*": self._handle_teacher_schedule,
                    "(?:what|which) courses does (prof\\.?\\s*\\w+\\s*\\w+) teach\\?*": self._handle_teacher_courses,
                    "who teaches (.*?)\\?*": self._handle_who_teaches,
                    "(when|where) is the (.*?) class\\?*": self._handle_course_timing_or_location,
                    "how many (teachers|sections|courses|subjects|rooms|departments) are there\\?*": self._handle_count,
                    "who is free at (\\d{1,2}(?::\\d{2})?\\s*(?:AM|PM))\\s*(?:on (\\w+))?\\?*": self._handle_teacher_free,
                    "(?:list|show|which courses are) (?:all )?lab(?:oratory)? courses\\?*": self._handle_lab_courses,
                    "(?:how many continuous periods|list continuous periods for) section ([\\w\\d-]+)\\?*": self._handle_continuous_periods,
                }
                matched = False
                for pattern, handler in query_patterns.items():
                    match = re.search(pattern, query, re.IGNORECASE)
                    if match:
                        try:
                            response = await handler(match, timetable_state)
                            matched = True
                            break
                        except Exception as e:
                            logging.exception(
                                f"Error processing query with handler {handler.__name__}: {e}"
                            )
                            response = "I encountered an error while processing your request. Please try again."
                            break
                if not matched:
                    response = "I'm not sure how to answer that. Please try rephrasing your question or ask for 'help'."
        yield ChatbotState.add_assistant_message(response)