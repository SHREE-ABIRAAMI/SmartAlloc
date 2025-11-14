import reflex as rx
from typing import TypedDict


class Teacher(TypedDict):
    id: int
    full_name: str


class Course(TypedDict):
    id: int
    name: str


class Section(TypedDict):
    id: int
    name: str


class Room(TypedDict):
    id: int
    name: str


class Department(TypedDict):
    id: int
    name: str


class TimetableSlot(TypedDict):
    day: str
    start_time: str
    end_time: str
    course: str
    teacher: str
    section: str
    room: str


class TimetableGenerationState(rx.State):
    teachers: list[Teacher] = [
        {"id": 1, "full_name": "Prof. Dumbledore"},
        {"id": 2, "full_name": "Prof. Snape"},
    ]
    courses: list[Course] = [
        {"id": 1, "name": "Potions"},
        {"id": 2, "name": "Defense Against the Dark Arts"},
    ]
    sections: list[Section] = [{"id": 1, "name": "1A"}, {"id": 2, "name": "2B"}]
    rooms: list[Room] = [{"id": 1, "name": "Dungeon"}, {"id": 2, "name": "Room 3C"}]
    departments: list[Department] = [{"id": 1, "name": "Magic"}]
    days_of_week: list[str] = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    timetable: list[TimetableSlot] = [
        {
            "day": "Monday",
            "start_time": "09:00",
            "end_time": "10:00",
            "course": "Potions",
            "teacher": "Prof. Snape",
            "section": "1A",
            "room": "Dungeon",
        },
        {
            "day": "Monday",
            "start_time": "10:00",
            "end_time": "11:00",
            "course": "Defense Against the Dark Arts",
            "teacher": "Prof. Dumbledore",
            "section": "1A",
            "room": "Room 3C",
        },
        {
            "day": "Tuesday",
            "start_time": "09:00",
            "end_time": "10:00",
            "course": "Defense Against the Dark Arts",
            "teacher": "Prof. Dumbledore",
            "section": "2B",
            "room": "Room 3C",
        },
    ]