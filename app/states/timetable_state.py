import reflex as rx
from typing import TypedDict, Any
import random
import asyncio
from sqlalchemy import text
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import io
import os
import logging


class TimetableEntry(TypedDict):
    course_name: str
    teacher_name: str
    room_number: str
    course_type: str


class Gene(TypedDict):
    course_id: int
    teacher_id: int
    room_id: int
    timing_id: int
    section_id: int


class Chromosome(TypedDict):
    genes: list[Gene]
    fitness: float


class GenerationResult(TypedDict):
    generation: int
    fitness: float


class TimetableGenerationState(rx.State):
    def _find_item(self, items: list, condition):
        return next((item for item in items if condition(item)), None)

    is_generating: bool = False
    progress: int = 0
    current_generation: int = 0
    best_fitness: float = 0.0
    generation_history: list[GenerationResult] = []
    timetable_generated: bool = False
    sorted_timings: list[str] = []
    _courses: list[dict] = []
    _teachers: list[dict] = []
    _rooms: list[dict] = []
    _timings: list[dict] = []
    _sections: list[dict] = []
    _departments: list[dict] = []
    _absent_teachers: list[int] = []
    best_chromosome: Chromosome | None = None
    selected_section_id: str = ""

    def _parse_time_for_sorting(self, time_str: str) -> float:
        start_time = time_str.split("-")[0].strip()
        try:
            if "." in start_time:
                hours_str, minutes_str = start_time.split(".")
            elif ":" in start_time:
                hours_str, minutes_str = start_time.split(":")
            else:
                return 0.0
            hours = int(hours_str)
            minutes = int(minutes_str)
            if 1 <= hours <= 7:
                hours += 12
            return hours + minutes / 60.0
        except (ValueError, IndexError) as e:
            logging.exception(f"Error parsing time string: {e}")
            return 0.0

    @rx.var
    def timetable_for_selected_section(self) -> list[tuple[str, list[dict[str, str]]]]:
        if (
            not self.selected_section_id
            or not self.timetable_generated
            or (not self.best_chromosome)
        ):
            return []
        try:
            section_id_int = int(self.selected_section_id)
        except (ValueError, TypeError) as e:
            logging.exception(f"Error converting section_id: {e}")
            return []
        days_order = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
        ]
        course_map = {c["id"]: c for c in self._courses}
        teacher_map = {t["id"]: t for t in self._teachers}
        room_map = {r["id"]: r for r in self._rooms}
        timing_map = {t["id"]: t for t in self._timings}
        section_genes_info = []
        for gene in self.best_chromosome["genes"]:
            if gene["section_id"] == section_id_int:
                timing = timing_map.get(gene["timing_id"])
                course = course_map.get(gene["course_id"])
                teacher = teacher_map.get(gene["teacher_id"])
                room = room_map.get(gene["room_id"])
                if all([timing, course, teacher, room]):
                    section_genes_info.append(
                        {
                            "day": timing["day_of_week"],
                            "time_sort": self._parse_time_for_sorting(timing["time"]),
                            "details": {
                                "course_name": course["course_name"],
                                "teacher_name": teacher["full_name"],
                                "room_number": room["lh_number"],
                                "course_type": course.get("course_type", "Theory"),
                            },
                        }
                    )
        if not section_genes_info:
            return []
        genes_by_day = {day: [] for day in days_order}
        for info in section_genes_info:
            if info["day"] in genes_by_day:
                genes_by_day[info["day"]].append(info)
        final_grid = []
        for day in days_order:
            day_genes = genes_by_day[day]
            if day_genes:
                sorted_day_genes = sorted(day_genes, key=lambda x: x["time_sort"])
                day_slots = [gene["details"] for gene in sorted_day_genes]
                final_grid.append((day, day_slots))
        return final_grid

    @rx.var
    def timetable_grid_data(self) -> list[tuple[str, list[dict]]]:
        return self.timetable_for_selected_section

    @rx.var
    def section_options(self) -> list[dict[str, str]]:
        return sorted(
            [
                {
                    "value": str(s["id"]),
                    "label": f"{s.get('year', 'N/A')} - {s['section_id']} - {s.get('department_name', 'N/A')}",
                }
                for s in self._sections
            ],
            key=lambda x: x["label"],
        )

    @rx.event
    def on_section_change(self, section_id: str):
        self.selected_section_id = section_id

    @rx.event
    async def load_all_data(self):
        async with rx.asession() as session:
            course_res = await session.execute(
                text(
                    "SELECT c.*, d.name as department_name, s.section_id as section_name, s.year, t.full_name as teacher_name FROM courses c LEFT JOIN departments d ON c.department_id = d.id LEFT JOIN sections s ON c.section_id = s.id LEFT JOIN teachers t ON c.teacher_id = t.id"
                )
            )
            self._courses = [dict(row) for row in course_res.mappings().all()]
            teacher_res = await session.execute(text("SELECT * FROM teachers"))
            self._teachers = [dict(row) for row in teacher_res.mappings().all()]
            room_res = await session.execute(text("SELECT * FROM rooms"))
            self._rooms = [dict(row) for row in room_res.mappings().all()]
            timing_res = await session.execute(text("SELECT * FROM timings"))
            self._timings = [dict(row) for row in timing_res.mappings().all()]
            section_res = await session.execute(
                text(
                    "SELECT s.*, d.name as department_name FROM sections s LEFT JOIN departments d on s.department_id = d.id"
                )
            )
            self._sections = [dict(row) for row in section_res.mappings().all()]
            department_res = await session.execute(text("SELECT * FROM departments"))
            self._departments = [dict(row) for row in department_res.mappings().all()]
            self._absent_teachers = []

    def _get_periods_per_week(self, course: dict) -> int:
        course_name = course.get("course_name", "").lower()
        course_type = course.get("course_type", "").lower()
        if (
            course.get("is_daily")
            or "maths" in course_name
            or "mathematics" in course_name
        ):
            return 5
        if course_type in ["laboratory", "workshop"]:
            return 1
        if course_type == "theory":
            return 4
        return 4

    def _get_courses_for_section(self, section: dict) -> list:
        return [c for c in self._courses if c.get("section_id") == section["id"]]

    def _find_consecutive_timings(self, num_periods: int) -> list[list[int]]:
        consecutive_groups = []
        timings_by_day = {}
        for t in self._timings:
            timings_by_day.setdefault(t["day_of_week"], []).append(t)
        for day, day_timings in timings_by_day.items():
            sorted_timings = sorted(
                day_timings, key=lambda t: self._parse_time_for_sorting(t["time"])
            )
            for i in range(len(sorted_timings) - num_periods + 1):
                group = sorted_timings[i : i + num_periods]
                is_consecutive = True
                for j in range(num_periods - 1):
                    t1_end_str = group[j]["time"].split("-")[1]
                    t2_start_str = group[j + 1]["time"].split("-")[0]
                    if t1_end_str != t2_start_str:
                        is_consecutive = False
                        break
                if is_consecutive:
                    consecutive_groups.append([t["id"] for t in group])
        return consecutive_groups

    def _get_morning_timings(self) -> list[list[int]]:
        morning_groups = []
        timings_by_day = {}
        for t in self._timings:
            timings_by_day.setdefault(t["day_of_week"], []).append(t)
        for day, day_timings in timings_by_day.items():
            sorted_timings = sorted(
                day_timings, key=lambda t: self._parse_time_for_sorting(t["time"])
            )
            morning_session_timings = [
                t
                for t in sorted_timings
                if self._parse_time_for_sorting(t["time"]) < 13
            ]
            if len(morning_session_timings) >= 5:
                morning_groups.append([t["id"] for t in morning_session_timings[:5]])
        return morning_groups

    def _find_consecutive_timings(self, num_periods: int) -> list[list[int]]:
        consecutive_groups = []
        timings_by_day = {}
        for t in self._timings:
            timings_by_day.setdefault(t["day_of_week"], []).append(t)
        for day, day_timings in timings_by_day.items():
            sorted_timings = sorted(
                day_timings, key=lambda t: self._parse_time_for_sorting(t["time"])
            )
            for i in range(len(sorted_timings) - num_periods + 1):
                group = sorted_timings[i : i + num_periods]
                is_consecutive = True
                for j in range(num_periods - 1):
                    t1_end_str = group[j]["time"].split("-")[1].strip()
                    t2_start_str = group[j + 1]["time"].split("-")[0].strip()
                    if t1_end_str != t2_start_str:
                        is_consecutive = False
                        break
                if is_consecutive:
                    consecutive_groups.append([t["id"] for t in group])
        return consecutive_groups

    def _get_morning_timings(self) -> list[list[int]]:
        morning_groups = []
        timings_by_day = {}
        for t in self._timings:
            timings_by_day.setdefault(t["day_of_week"], []).append(t)
        for day, day_timings in timings_by_day.items():
            sorted_timings = sorted(
                day_timings, key=lambda t: self._parse_time_for_sorting(t["time"])
            )
            if len(sorted_timings) >= 5:
                morning_groups.append([t["id"] for t in sorted_timings[:5]])
        return morning_groups

    def _create_initial_population(self, size: int) -> list[Chromosome]:
        population = []
        for _ in range(size):
            genes = []
            used_slots = set()
            timings_by_day = {
                d: []
                for d in [
                    "Monday",
                    "Tuesday",
                    "Wednesday",
                    "Thursday",
                    "Friday",
                    "Saturday",
                ]
            }
            for t in self._timings:
                timings_by_day[t["day_of_week"]].append(t)
            for section in self._sections:
                section_id = section["id"]
                courses_for_section = [
                    c for c in self._courses if c.get("section_id") == section_id
                ]
                if not courses_for_section:
                    continue
                section_periods_config = {
                    day.lower(): section.get(f"periods_{day.lower()}", 0)
                    for day in timings_by_day.keys()
                }
                total_section_periods = sum(section_periods_config.values())
                if total_section_periods == 0:
                    continue
                base_classes = []
                for course in courses_for_section:
                    if course.get("course_type") in ["Laboratory", "Workshop"]:
                        base_classes.append(course)
                    else:
                        periods_needed = self._get_periods_per_week(course)
                        base_classes.extend([course] * periods_needed)
                random.shuffle(base_classes)
                daily_scheduled_count = {day: 0 for day in timings_by_day.keys()}
                for course in base_classes:
                    if sum(daily_scheduled_count.values()) >= total_section_periods:
                        break
                    is_lab_or_workshop = course.get("course_type") in [
                        "Laboratory",
                        "Workshop",
                    ]
                    periods_to_schedule = 2 if is_lab_or_workshop else 1
                    shuffled_days = list(timings_by_day.keys())
                    random.shuffle(shuffled_days)
                    scheduled = False
                    for day in shuffled_days:
                        if (
                            daily_scheduled_count[day] + periods_to_schedule - 1
                            >= section_periods_config[day.lower()]
                        ):
                            continue
                        if is_lab_or_workshop:
                            consecutive_pairs = self._find_consecutive_timings(2)
                            day_consecutive_pairs = [
                                p
                                for p in consecutive_pairs
                                if self._find_item(
                                    self._timings, lambda t: t["id"] == p[0]
                                )["day_of_week"]
                                == day
                            ]
                            random.shuffle(day_consecutive_pairs)
                            for t_pair in day_consecutive_pairs:
                                timing1_id, timing2_id = t_pair
                                if all(
                                    (
                                        ("teacher", course["teacher_id"], tid)
                                        not in used_slots
                                        and ("section", section_id, tid)
                                        not in used_slots
                                        for tid in t_pair
                                    )
                                ):
                                    available_rooms = [
                                        r
                                        for r in self._rooms
                                        if all(
                                            (
                                                ("room", r["id"], tid) not in used_slots
                                                for tid in t_pair
                                            )
                                        )
                                    ]
                                    if available_rooms:
                                        room = random.choice(available_rooms)
                                        for tid in t_pair:
                                            genes.append(
                                                {
                                                    "course_id": course["id"],
                                                    "teacher_id": course["teacher_id"],
                                                    "room_id": room["id"],
                                                    "timing_id": tid,
                                                    "section_id": section_id,
                                                }
                                            )
                                            used_slots.add(
                                                ("teacher", course["teacher_id"], tid)
                                            )
                                            used_slots.add(("room", room["id"], tid))
                                            used_slots.add(("section", section_id, tid))
                                        daily_scheduled_count[day] += 2
                                        scheduled = True
                                        break
                            if scheduled:
                                break
                        else:
                            available_timings_for_day = [
                                t
                                for t in timings_by_day[day]
                                if ("section", section_id, t["id"]) not in used_slots
                                and ("teacher", course["teacher_id"], t["id"])
                                not in used_slots
                            ]
                            if available_timings_for_day:
                                timing = random.choice(available_timings_for_day)
                                timing_id = timing["id"]
                                available_rooms = [
                                    r
                                    for r in self._rooms
                                    if ("room", r["id"], timing_id) not in used_slots
                                ]
                                if available_rooms:
                                    room = random.choice(available_rooms)
                                    genes.append(
                                        {
                                            "course_id": course["id"],
                                            "teacher_id": course["teacher_id"],
                                            "room_id": room["id"],
                                            "timing_id": timing_id,
                                            "section_id": section_id,
                                        }
                                    )
                                    used_slots.add(
                                        ("teacher", course["teacher_id"], timing_id)
                                    )
                                    used_slots.add(("room", room["id"], timing_id))
                                    used_slots.add(("section", section_id, timing_id))
                                    daily_scheduled_count[day] += 1
                                    scheduled = True
                                    break
                    if scheduled:
                        continue
            chromosome: Chromosome = {"genes": genes, "fitness": 0.0}
            population.append(chromosome)
        for chrom in population:
            chrom["fitness"] = self._calculate_enhanced_fitness(chrom)
        return population

    def _find_available_timings(self, course, used_slots, daily_course_days):
        available_slots = []
        course_id = course["id"]
        teacher_id = course["teacher_id"]
        section_id = course["section_id"]
        is_daily = course.get("is_daily", False)
        for timing in self._timings:
            timing_id = timing["id"]
            if ("teacher", teacher_id, timing_id) in used_slots or (
                "section",
                section_id,
                timing_id,
            ) in used_slots:
                continue
            if is_daily and timing["day_of_week"] in daily_course_days.get(
                course_id, set()
            ):
                continue
            for room in self._rooms:
                if ("room", room["id"], timing_id) not in used_slots:
                    available_slots.append((timing_id, room["id"]))
                    break
        return available_slots

    def _calculate_fitness(self, chromosome: Chromosome) -> float:
        clashes = 0
        teacher_slots, room_slots, section_slots = (set(), set(), set())
        if not chromosome["genes"]:
            return 0.0
        teacher_daily_load = {}
        for gene in chromosome["genes"]:
            teacher_id, timing_id, room_id, section_id = (
                gene["teacher_id"],
                gene["timing_id"],
                gene["room_id"],
                gene["section_id"],
            )
            t_slot = (teacher_id, timing_id)
            if t_slot in teacher_slots:
                clashes += 1
            teacher_slots.add(t_slot)
            r_slot = (room_id, timing_id)
            if r_slot in room_slots:
                clashes += 1
            room_slots.add(r_slot)
            s_slot = (section_id, timing_id)
            if s_slot in section_slots:
                clashes += 5
            section_slots.add(s_slot)
            timing = self._find_item(self._timings, lambda t: t["id"] == timing_id)
            if timing:
                day = timing["day_of_week"]
                key = (teacher_id, day)
                teacher_daily_load[key] = teacher_daily_load.get(key, 0) + 1
        workload_penalty = 0
        for load in teacher_daily_load.values():
            if load > 5:
                workload_penalty += (load - 5) * 2
        total_required_slots = sum(
            (
                section.get(f"periods_{day.lower()}", 0)
                for section in self._sections
                for day in [
                    "Monday",
                    "Tuesday",
                    "Wednesday",
                    "Thursday",
                    "Friday",
                    "Saturday",
                ]
            )
        )
        num_filled_slots = len(chromosome["genes"])
        coverage_ratio = (
            num_filled_slots / total_required_slots if total_required_slots > 0 else 0
        )
        coverage_penalty = (1 - coverage_ratio) * total_required_slots
        total_penalty = clashes + workload_penalty + coverage_penalty
        fitness = 1.0 / (1.0 + total_penalty)
        return min(fitness, 1.0)

    def _selection(self, population: list[Chromosome]) -> list[Chromosome]:
        return sorted(population, key=lambda c: c["fitness"], reverse=True)[
            : len(population) // 2
        ]

    def _crossover(self, parent1: Chromosome, parent2: Chromosome) -> Chromosome:
        child_genes = []
        for gene1, gene2 in zip(parent1["genes"], parent2["genes"]):
            child_genes.append(random.choice([gene1, gene2]))
        child: Chromosome = {"genes": child_genes, "fitness": 0.0}
        child["fitness"] = self._calculate_fitness(child)
        return child

    def _mutation(self, chromosome: Chromosome) -> Chromosome:
        if random.random() < 0.4 and chromosome["genes"]:
            gene_to_mutate = random.choice(chromosome["genes"])
            if self._timings:
                gene_to_mutate["timing_id"] = random.choice(self._timings)["id"]
            if self._rooms:
                gene_to_mutate["room_id"] = random.choice(self._rooms)["id"]
        chromosome["fitness"] = self._calculate_fitness(chromosome)
        return chromosome

    def _calculate_teacher_workload(self, chromosome: Chromosome) -> dict:
        workload = {
            teacher["id"]: {
                "total": 0,
                "daily": {
                    d: 0
                    for d in [
                        "Monday",
                        "Tuesday",
                        "Wednesday",
                        "Thursday",
                        "Friday",
                        "Saturday",
                    ]
                },
                "max_consecutive": 0,
                "weekly_distribution": 0,
            }
            for teacher in self._teachers
        }
        if not chromosome["genes"]:
            return workload
        timing_map = {t["id"]: t for t in self._timings}
        teacher_slots_by_day = {
            t["id"]: {d: [] for d in workload[t["id"]]["daily"]} for t in self._teachers
        }
        for gene in chromosome["genes"]:
            teacher_id = gene["teacher_id"]
            timing = timing_map.get(gene["timing_id"])
            if teacher_id in workload and timing:
                day = timing["day_of_week"]
                workload[teacher_id]["total"] += 1
                workload[teacher_id]["daily"][day] += 1
                teacher_slots_by_day[teacher_id][day].append(
                    self._parse_time_for_sorting(timing["time"])
                )
        for teacher_id, daily_slots in teacher_slots_by_day.items():
            max_consecutive = 0
            for day, slots in daily_slots.items():
                if not slots:
                    continue
                sorted_slots = sorted(slots)
                current_consecutive = 1
                for i in range(1, len(sorted_slots)):
                    if sorted_slots[i] - sorted_slots[i - 1] < 1.1:
                        current_consecutive += 1
                    else:
                        max_consecutive = max(max_consecutive, current_consecutive)
                        current_consecutive = 1
                max_consecutive = max(max_consecutive, current_consecutive)
            workload[teacher_id]["max_consecutive"] = max_consecutive
            daily_loads = list(workload[teacher_id]["daily"].values())
            if sum(daily_loads) > 0:
                mean_load = (
                    sum(daily_loads) / len([ld for ld in daily_loads if ld > 0])
                    if any(daily_loads)
                    else 0
                )
                variance = (
                    sum([(x - mean_load) ** 2 for x in daily_loads if x > 0])
                    / len([ld for ld in daily_loads if ld > 0])
                    if any((ld > 0 for ld in daily_loads))
                    else 0
                )
                workload[teacher_id]["weekly_distribution"] = variance
        return workload

    def _check_consecutive_classes(self, chromosome: Chromosome) -> int:
        workload = self._calculate_teacher_workload(chromosome)
        if not workload:
            return 0
        return (
            max((stats.get("max_consecutive", 0) for stats in workload.values()))
            if workload
            else 0
        )

    def _calculate_workload_balance_score(self, chromosome: Chromosome) -> float:
        workload = self._calculate_teacher_workload(chromosome)
        if not workload:
            return 1.0
        total_classes = sum((stats["total"] for stats in workload.values()))
        if total_classes == 0:
            return 1.0
        teacher_loads = [stats["total"] for stats in workload.values()]
        mean_load = total_classes / len(self._teachers)
        load_variance = sum([(load - mean_load) ** 2 for load in teacher_loads]) / len(
            self._teachers
        )
        load_penalty = load_variance / mean_load**2 if mean_load > 0 else 0
        consecutive_penalty = 0
        for stats in workload.values():
            if stats["max_consecutive"] > 4:
                consecutive_penalty += (stats["max_consecutive"] - 4) * 0.2
        distribution_penalty = sum(
            (stats["weekly_distribution"] for stats in workload.values())
        ) / len(self._teachers)
        total_penalty = load_penalty + consecutive_penalty + distribution_penalty / 10
        return max(0.0, 1.0 - total_penalty)

    def _calculate_enhanced_fitness(self, chromosome: Chromosome) -> float:
        if not chromosome["genes"]:
            return 0.0
        clashes = 0
        teacher_slots, room_slots, section_slots = (set(), set(), set())
        for gene in chromosome["genes"]:
            t_slot = (gene["teacher_id"], gene["timing_id"])
            if t_slot in teacher_slots:
                clashes += 1
            teacher_slots.add(t_slot)
            r_slot = (gene["room_id"], gene["timing_id"])
            if r_slot in room_slots:
                clashes += 1
            room_slots.add(r_slot)
            s_slot = (gene["section_id"], gene["timing_id"])
            if s_slot in section_slots:
                clashes += 5
            section_slots.add(s_slot)
        total_required_slots = sum(
            (
                section.get(f"periods_{day.lower()}", 0)
                for section in self._sections
                for day in [
                    "Monday",
                    "Tuesday",
                    "Wednesday",
                    "Thursday",
                    "Friday",
                    "Saturday",
                ]
            )
        )
        num_filled_slots = len(chromosome["genes"])
        coverage_ratio = (
            num_filled_slots / total_required_slots if total_required_slots > 0 else 0
        )
        conflict_penalty = clashes * 0.01
        coverage_bonus = coverage_ratio * 0.5
        fitness = 1.0 - conflict_penalty + coverage_bonus
        return max(0.0, min(1.0, fitness))

    def _smart_initial_population(self, size: int) -> list[Chromosome]:
        return self._create_initial_population(size)

    def _repair_chromosome(self, chromosome: Chromosome) -> Chromosome:
        conflicts = set()
        teacher_slots, room_slots, section_slots = (set(), set(), set())
        for i, gene in enumerate(chromosome["genes"]):
            t_slot = (gene["teacher_id"], gene["timing_id"])
            r_slot = (gene["room_id"], gene["timing_id"])
            s_slot = (gene["section_id"], gene["timing_id"])
            if (
                t_slot in teacher_slots
                or r_slot in room_slots
                or s_slot in section_slots
            ):
                conflicts.add(i)
            else:
                teacher_slots.add(t_slot)
                room_slots.add(r_slot)
                section_slots.add(s_slot)
        if conflicts:
            chromosome["genes"] = [
                gene for i, gene in enumerate(chromosome["genes"]) if i not in conflicts
            ]
        chromosome["fitness"] = self._calculate_enhanced_fitness(chromosome)
        return chromosome

    def _adaptive_mutation(self, chromosome: Chromosome, generation: int) -> Chromosome:
        mutation_rate = 0.1 + generation / 100 * 0.3
        if random.random() < mutation_rate and chromosome["genes"]:
            gene_to_mutate = random.choice(chromosome["genes"])
            if self._timings:
                gene_to_mutate["timing_id"] = random.choice(self._timings)["id"]
            if self._rooms:
                gene_to_mutate["room_id"] = random.choice(self._rooms)["id"]
        chromosome = self._repair_chromosome(chromosome)
        return chromosome

    def _aggressive_gap_filling(self, chromosome: Chromosome) -> Chromosome:
        scheduled_courses = {}
        for gene in chromosome["genes"]:
            key = (gene["course_id"], gene["section_id"])
            scheduled_courses[key] = scheduled_courses.get(key, 0) + 1
        all_required_classes = {}
        for course in self._courses:
            key = (course["id"], course["section_id"])
            all_required_classes[key] = self._get_periods_per_week(course)
        missing_courses = []
        for key, required_count in all_required_classes.items():
            missing_count = required_count - scheduled_courses.get(key, 0)
            if missing_count > 0:
                course_id, section_id = key
                course = self._find_item(self._courses, lambda c: c["id"] == course_id)
                if course:
                    missing_courses.extend([course] * missing_count)
        if not missing_courses:
            pass
        used_slots = set()
        for gene in chromosome["genes"]:
            used_slots.add(("teacher", gene["teacher_id"], gene["timing_id"]))
            used_slots.add(("room", gene["room_id"], gene["timing_id"]))
            used_slots.add(("section", gene["section_id"], gene["timing_id"]))
        for course in missing_courses:
            available_slots = []
            for timing in self._timings:
                timing_id = timing["id"]
                if ("teacher", course["teacher_id"], timing_id) not in used_slots and (
                    "section",
                    course["section_id"],
                    timing_id,
                ) not in used_slots:
                    for room in self._rooms:
                        if ("room", room["id"], timing_id) not in used_slots:
                            available_slots.append((timing_id, room["id"]))
                            break
            if available_slots:
                timing_id, room_id = random.choice(available_slots)
                chromosome["genes"].append(
                    {
                        "course_id": course["id"],
                        "teacher_id": course["teacher_id"],
                        "room_id": room_id,
                        "timing_id": timing_id,
                        "section_id": course["section_id"],
                    }
                )
                used_slots.add(("teacher", course["teacher_id"], timing_id))
                used_slots.add(("room", room_id, timing_id))
                used_slots.add(("section", course["section_id"], timing_id))
        chromosome["fitness"] = self._calculate_enhanced_fitness(chromosome)
        return chromosome

    @rx.event(background=True)
    async def run_genetic_algorithm(self):
        async with self:
            self.is_generating = True
            self.progress = 0
            self.generation_history = []
            self.timetable_generated = False
        try:
            if not all(
                [
                    self._courses,
                    self._teachers,
                    self._rooms,
                    self._timings,
                    self._sections,
                ]
            ):
                yield rx.toast(
                    "Error: Not enough data to generate. Please check all categories.",
                    duration=5000,
                )
                async with self:
                    self.is_generating = False
                return
            logging.info("Starting timetable generation...")
            population_size = 10
            num_generations = 20
            population = self._create_initial_population(size=population_size)
            if not population or not any((p["genes"] for p in population)):
                yield rx.toast(
                    "Error: Failed to create initial population.", duration=5000
                )
                async with self:
                    self.is_generating = False
                return
            logging.info(
                f"Initial population created with {len(population)} chromosomes."
            )
            for gen in range(num_generations):
                population = sorted(
                    population, key=lambda c: c["fitness"], reverse=True
                )
                elitism_count = 2
                next_gen = population[:elitism_count]
                selected = (
                    population[: len(population) // 2]
                    if len(population) > 1
                    else population
                )
                while len(next_gen) < population_size:
                    parent1, parent2 = random.choices(selected, k=2)
                    child = self._crossover(parent1, parent2)
                    child = self._adaptive_mutation(child, gen)
                    next_gen.append(child)
                population = [self._aggressive_gap_filling(chrom) for chrom in next_gen]
                best_in_gen = max(population, key=lambda c: c["fitness"])
                async with self:
                    self.current_generation = gen + 1
                    self.progress = int((gen + 1) / num_generations * 100)
                    self.best_fitness = best_in_gen["fitness"]
                    self.generation_history.append(
                        {"generation": gen + 1, "fitness": self.best_fitness}
                    )
                logging.info(f"Gen {gen + 1}: Fitness = {best_in_gen['fitness']:.4f}")
                yield
                if best_in_gen["fitness"] >= 0.98:
                    logging.info("Early termination: Target fitness reached.")
                    break
            best_chromosome = max(population, key=lambda c: c["fitness"])
            async with self:
                self.best_chromosome = self._repair_chromosome(best_chromosome)
                self.timetable_generated = True
                self.progress = 100
            yield TimetableGenerationState.prepare_timetable_display
            yield rx.toast(
                f"Timetable generated! Fitness: {self.best_fitness:.4f}", duration=5000
            )
        except Exception as e:
            logging.exception(f"Timetable generation failed: {e}")
            yield rx.toast(f"Error: {e}", duration=5000)
        finally:
            async with self:
                self.is_generating = False

    def _generate_pdf_for_section(
        self, section_id: int, best_chromosome: dict
    ) -> bytes | None:
        section = next((s for s in self._sections if s["id"] == section_id), None)
        if not section:
            return None
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
        elements = []
        styles = getSampleStyleSheet()
        title = f"Timetable for {section.get('department_name', 'N/A')} - Year {section.get('year', 'N/A')}, Section {section.get('section_id', 'N/A')}"
        elements.append(Paragraph(title, styles["h1"]))
        days = [
            "Time",
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
        ]
        data = [days]
        course_map = {c["id"]: c for c in self._courses}
        teacher_map = {t["id"]: t for t in self._teachers}
        room_map = {r["id"]: r for r in self._rooms}
        timing_map = {t["id"]: t for t in self._timings}
        unique_times = sorted(
            list({t["time"] for t in self._timings}), key=self._parse_time_for_sorting
        )
        grid = {time: {day: "" for day in days[1:]} for time in unique_times}
        if best_chromosome:
            for gene in best_chromosome["genes"]:
                if gene["section_id"] == section_id:
                    timing = timing_map.get(gene["timing_id"])
                    if not timing:
                        continue
                    day = timing["day_of_week"]
                    time = timing["time"]
                    if day not in days[1:] or time not in unique_times:
                        continue
                    course = course_map.get(gene["course_id"])
                    teacher = teacher_map.get(gene["teacher_id"])
                    room = room_map.get(gene["room_id"])
                    if all([course, teacher, room]):
                        grid[time][day] = (
                            f"{course['course_name']}\n{teacher['full_name']}\n{room['lh_number']}"
                        )
        for time in unique_times:
            row = [time]
            for day in days[1:]:
                row.append(grid[time].get(day, ""))
            data.append(row)
        table = Table(data)
        style = TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, 1), (0, -1), colors.beige),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
        table.setStyle(style)
        elements.append(table)
        footer_text = "Generated by SmartAlloc - AI-Powered Timetable Generator"
        elements.append(Paragraph(footer_text, styles["Italic"]))
        doc.build(elements)
        return buffer.getvalue()

    @rx.event
    def prepare_timetable_display(self):
        if not self.best_chromosome:
            return
        unique_times = sorted(
            list({t["time"] for t in self._timings}), key=self._parse_time_for_sorting
        )
        self.sorted_timings = unique_times
        if self._sections:
            self.selected_section_id = str(self._sections[0]["id"])
            if len(self._sections) > 1:
                pass

    def _generate_pdf_for_section(
        self, section_id: int, best_chromosome: dict
    ) -> bytes | None:
        section = next((s for s in self._sections if s["id"] == section_id), None)
        if not section:
            return None
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
        elements = []
        styles = getSampleStyleSheet()
        title = f"Timetable for {section.get('department_name', 'N/A')} - Year {section.get('year', 'N/A')}, Section {section.get('section_id', 'N/A')}"
        elements.append(Paragraph(title, styles["h1"]))
        days = [
            "Time",
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
        ]
        data = [days]
        course_map = {c["id"]: c for c in self._courses}
        teacher_map = {t["id"]: t for t in self._teachers}
        room_map = {r["id"]: r for r in self._rooms}
        timing_map = {t["id"]: t for t in self._timings}
        grid = {time: {day: "" for day in days[1:]} for time in self.sorted_timings}
        if best_chromosome:
            for gene in best_chromosome["genes"]:
                if gene["section_id"] == section_id:
                    timing = timing_map.get(gene["timing_id"])
                    if not timing:
                        continue
                    day = timing["day_of_week"]
                    time = timing["time"]
                    course = course_map.get(gene["course_id"])
                    teacher = teacher_map.get(gene["teacher_id"])
                    room = room_map.get(gene["room_id"])
                    if all([course, teacher, room]):
                        grid[time][day] = (
                            f"{course['course_name']}\n{teacher['full_name']}\n{room['lh_number']}"
                        )
        for time in self.sorted_timings:
            row = [time]
            for day in days[1:]:
                row.append(grid[time][day])
            data.append(row)
        table = Table(data)
        style = TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, 1), (0, -1), colors.beige),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
        table.setStyle(style)
        elements.append(table)
        footer_text = "Generated by SmartAlloc - AI-Powered Timetable Generator"
        elements.append(Paragraph(footer_text, styles["Italic"]))
        doc.build(elements)
        return buffer.getvalue()

    @rx.event
    def prepare_timetable_display(self):
        if not self.best_chromosome:
            return
        unique_times = sorted(
            list({t["time"] for t in self._timings}), key=self._parse_time_for_sorting
        )
        self.sorted_timings = unique_times
        if self._sections:
            self.selected_section_id = str(self._sections[0]["id"])

    @rx.event
    def download_current_section_pdf(self):
        if not self.selected_section_id or not self.best_chromosome:
            return rx.toast("Please select a section and generate a timetable first.")
        pdf_bytes = self._generate_pdf_for_section(
            int(self.selected_section_id), self.best_chromosome
        )
        if pdf_bytes:
            section = next(
                (s for s in self._sections if s["id"] == int(self.selected_section_id)),
                None,
            )
            filename = f"timetable_{section['department_name']}_{section['year']}_{section['section_id']}.pdf".replace(
                " ", "_"
            )
            return rx.download(data=pdf_bytes, filename=filename)

    @rx.event
    async def download_all_sections_zip(self):
        import zipfile

        if not self.best_chromosome:
            return rx.toast("Please generate a timetable first.")
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
            for section in self._sections:
                pdf_bytes = self._generate_pdf_for_section(
                    section["id"], self.best_chromosome
                )
                if pdf_bytes:
                    filename = f"timetable_{section['department_name']}_{section['year']}_{section['section_id']}.pdf".replace(
                        " ", "_"
                    )
                    zipf.writestr(filename, pdf_bytes)
        zip_buffer.seek(0)
        return rx.download(
            data=zip_buffer.getvalue(), filename="timetables_all_sections.zip"
        )