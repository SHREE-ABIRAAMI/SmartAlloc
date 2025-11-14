import reflex as rx
import re
import datetime
import logging
from typing import TypedDict, Any, Coroutine, Callable
from app.states.timetable_generation_state import TimetableGenerationState


class Message(TypedDict):
    role: str
    content: str


class ChatbotState(rx.State):
    show_chat: bool = False
    messages: list[Message] = [
        {
            "role": "assistant",
            "content": """Hello! I'm the HOD Assistant. I can help you with timetable queries once it's generated. You can ask me things like:
- *'What is the schedule for Prof. Snape?'*
- *'Who teaches Potions?'*
- *'Show me the schedule for section 1A.'*
- *'How many teachers are there?'*
- *'Which classes does section 2B have on Monday?'*
- *'Who is free at 10 AM on Tuesday?'*""",
        }
    ]
    is_processing: bool = False

    @rx.event
    def toggle_chat(self):
        self.show_chat = not self.show_chat

    @rx.event
    def handle_submit(self, form_data: dict[str, str]):
        query = form_data.get("query")
        if not query:
            return
        self.messages.append({"role": "user", "content": query})
        self.is_processing = True
        return ChatbotState.process_query(query)

    @rx.event
    def add_assistant_message(self, content: str):
        self.messages.append({"role": "assistant", "content": content})
        self.is_processing = False

    def _find_item(self, collection: list[dict], key: str, value: str) -> dict | None:
        value_lower = value.lower()
        for item in collection:
            if str(item.get(key, "")).lower() == value_lower:
                return item
        return None

    async def _handle_teacher_schedule(
        self, match: re.Match, timetable_state: TimetableGenerationState
    ) -> str:
        teacher_name = match.group(1)
        teacher = self._find_item(timetable_state.teachers, "full_name", teacher_name)
        if not teacher:
            return f"Sorry, I couldn't find a teacher named '{teacher_name}'."
        schedule = sorted(
            [
                slot
                for slot in timetable_state.timetable
                if slot["teacher"] == teacher["full_name"]
            ],
            key=lambda x: (
                timetable_state.days_of_week.index(x["day"]),
                x["start_time"],
            ),
        )
        if not schedule:
            return f"It seems {teacher_name} has no classes assigned in the generated timetable."
        response = f"**Schedule for {teacher_name}:**\n\n"
        for day in timetable_state.days_of_week:
            day_schedule = [s for s in schedule if s["day"] == day]
            if day_schedule:
                response += f"**{day}:**\n"
                for slot in day_schedule:
                    response += f"- **{slot['start_time']} - {slot['end_time']}:** {slot['course']} (Section {slot['section']}) in Room {slot['room']}\n"
                response += """
"""
        return response

    async def _handle_section_schedule(
        self, match: re.Match, timetable_state: TimetableGenerationState
    ) -> str:
        section_name = match.group(1)
        section = self._find_item(timetable_state.sections, "name", section_name)
        if not section:
            return f"Sorry, I couldn't find a section named '{section_name}'."
        schedule = sorted(
            [
                slot
                for slot in timetable_state.timetable
                if slot["section"] == section["name"]
            ],
            key=lambda x: (
                timetable_state.days_of_week.index(x["day"]),
                x["start_time"],
            ),
        )
        if not schedule:
            return f"It seems Section {section_name} has no classes assigned."
        response = f"**Schedule for Section {section_name}:**\n\n"
        day_query = match.group(3).capitalize() if match.group(3) else None
        days_to_show = (
            [day_query]
            if day_query and day_query in timetable_state.days_of_week
            else timetable_state.days_of_week
        )
        for day in days_to_show:
            day_schedule = [s for s in schedule if s["day"] == day]
            if day_schedule:
                response += f"**{day}:**\n"
                for slot in day_schedule:
                    response += f"- **{slot['start_time']} - {slot['end_time']}:** {slot['course']} ({slot['teacher']}) in Room {slot['room']}\n"
                response += """
"""
        if not any((s for s in schedule if s["day"] in days_to_show)):
            return f"Section {section_name} has no classes scheduled on {day_query}."
        return response

    async def _handle_who_teaches(
        self, match: re.Match, timetable_state: TimetableGenerationState
    ) -> str:
        course_name = match.group(1)
        slots = [
            slot
            for slot in timetable_state.timetable
            if slot["course"].lower() == course_name.lower()
        ]
        if not slots:
            return f"I couldn't find any information about the course '{course_name}'. Is it in the timetable?"
        teachers = sorted(list(set((slot["teacher"] for slot in slots))))
        return f"**{course_name}** is taught by: **{', '.join(teachers)}**."

    async def _handle_count(
        self, match: re.Match, timetable_state: TimetableGenerationState
    ) -> str:
        item_type = match.group(1).lower()
        if item_type.startswith("teacher"):
            count = len(timetable_state.teachers)
            return f"There are **{count}** teachers in total."
        if item_type.startswith("section"):
            count = len(timetable_state.sections)
            return f"There are **{count}** sections in total."
        if item_type.startswith("course") or item_type.startswith("subject"):
            count = len(timetable_state.courses)
            return f"There are **{count}** courses in total."
        if item_type.startswith("room"):
            count = len(timetable_state.rooms)
            return f"There are **{count}** rooms available."
        if item_type.startswith("department"):
            count = len(timetable_state.departments)
            return f"There are **{count}** departments."
        return "I can count teachers, sections, courses, rooms, and departments."

    async def _handle_teacher_free(
        self, match: re.Match, timetable_state: TimetableGenerationState
    ) -> str:
        time_str = match.group(1)
        day_str = (
            match.group(3).capitalize()
            if match.group(3)
            else datetime.date.today().strftime("%A")
        )
        if day_str not in timetable_state.days_of_week:
            return f"Sorry, '{day_str}' is not a valid school day in the timetable."
        try:
            query_time = (
                datetime.datetime.strptime(time_str, "%I %p").time()
                or datetime.datetime.strptime(time_str, "%H:%M").time()
            )
        except ValueError as e:
            logging.exception(f"Error: {e}")
            return "Please use a valid time format like '10 AM' or '14:00'."
        busy_teachers = set()
        for slot in timetable_state.timetable:
            if slot["day"] == day_str:
                start_time = datetime.datetime.strptime(
                    slot["start_time"], "%H:%M"
                ).time()
                end_time = datetime.datetime.strptime(slot["end_time"], "%H:%M").time()
                if start_time <= query_time < end_time:
                    busy_teachers.add(slot["teacher"])
        all_teachers = {t["full_name"] for t in timetable_state.teachers}
        free_teachers = sorted(list(all_teachers - busy_teachers))
        if not free_teachers:
            return f"It seems no teachers are free at {time_str} on {day_str}."
        return (
            f"**Teachers free at {time_str} on {day_str}:**\n- "
            + """
- """.join(free_teachers)
        )

    @rx.event(background=True)
    async def process_query(self, query: str):
        async with self:
            timetable_state = await self.get_state(TimetableGenerationState)
        response = "I'm sorry, I don't have enough information to answer that. Has the timetable been generated yet?"
        if timetable_state.timetable:
            query_patterns = {
                "(?:what is the schedule for|schedule for|show schedule for) (\\w+\\.?\\s*\\w+)": self._handle_teacher_schedule,
                "who teaches (.*?)\\?*": self._handle_who_teaches,
                "(?:schedule for|show schedule for|what is the schedule for) section (\\w+)( on (\\w+))?\\?*": self._handle_section_schedule,
                "how many (teachers|sections|courses|subjects|rooms|departments) are there\\?*": self._handle_count,
                "who is free at (\\d{1,2}(?::\\d{2})?\\s*(?:AM|PM)?)?( on (\\w+))?\\?*": self._handle_teacher_free,
            }
            found_match = False
            for pattern, handler in query_patterns.items():
                match = re.search(pattern, query, re.IGNORECASE)
                if match:
                    response = await handler(match, timetable_state)
                    found_match = True
                    break
            if not found_match:
                response = "I'm not sure how to answer that. Please try rephrasing your question."
        async with self:
            self.add_assistant_message(response)