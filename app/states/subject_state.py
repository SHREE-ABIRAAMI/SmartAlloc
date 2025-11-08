import reflex as rx
from typing import TypedDict


class Subject(TypedDict):
    id: int
    name: str
    department: str
    year: int


class SubjectState(rx.State):
    subjects: list[Subject] = [
        {
            "id": 1,
            "name": "Introduction to Programming",
            "department": "Computer Science",
            "year": 1,
        },
        {
            "id": 2,
            "name": "Discrete Mathematics",
            "department": "Computer Science",
            "year": 1,
        },
        {
            "id": 3,
            "name": "Data Structures",
            "department": "Computer Science",
            "year": 2,
        },
        {"id": 4, "name": "Algorithms", "department": "Computer Science", "year": 2},
        {"id": 5, "name": "Basic Electronics", "department": "Electronics", "year": 1},
        {"id": 6, "name": "Circuit Theory", "department": "Electronics", "year": 1},
        {
            "id": 7,
            "name": "Digital Logic Design",
            "department": "Electronics",
            "year": 2,
        },
        {
            "id": 8,
            "name": "Signals and Systems",
            "department": "Electronics",
            "year": 2,
        },
    ]
    new_subject_name: str = ""
    new_subject_department: str = "Computer Science"
    new_subject_year: str = "1"
    departments: list[str] = ["Computer Science", "Electronics", "Mechanical", "Civil"]
    years: list[int] = [1, 2, 3, 4]

    @rx.event
    def add_subject(self):
        if self.new_subject_name:
            new_id = len(self.subjects) + 1
            self.subjects.append(
                {
                    "id": new_id,
                    "name": self.new_subject_name,
                    "department": self.new_subject_department,
                    "year": int(self.new_subject_year),
                }
            )
            self.new_subject_name = ""

    @rx.event
    def delete_subject(self, subject_id: int):
        self.subjects = [sub for sub in self.subjects if sub["id"] != subject_id]