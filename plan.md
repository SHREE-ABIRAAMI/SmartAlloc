# SmartAlloc - Year-Wise Subject Allocation Enhancement

## Phase 1: Data Model & Course Entry Enhancement ✅
- [x] Add year field to courses/subjects model (1st year, 2nd year, 3rd year, 4th year)
- [x] Update course entry form to include year selection dropdown
- [x] Modify department-course relationship to support year-wise allocation
- [x] Update sections to include year information
- [x] Ensure database schema supports year and department-based subject filtering

## Phase 2: UI Updates for Year-Based Subject Management
- [ ] Add year selector in Add Courses page
- [ ] Update course listing to show year and department information
- [ ] Modify section creation to specify which year the section belongs to
- [ ] Add filters to view courses by year and department
- [ ] Update course-teacher mapping to respect year constraints

## Phase 3: Timetable Generation with Year-Specific Subjects
- [ ] Update timetable generation logic to only use courses matching section's year and department
- [ ] Ensure genetic algorithm considers year-wise subject constraints
- [ ] Update timetable display to show year information for each section
- [ ] Modify PDF generation to include year-wise timetable organization
- [ ] Update HOD Assistant chatbot to answer year-specific queries (e.g., "What subjects does 2nd year CSE have?")
