""" Test the complete Canvas agent """

from src.agents.canvas_agent import CanvasAgent

def test_get_active_courses():
    agent = CanvasAgent()
    courses = agent.get_active_courses()
    
    print(f"Found {len(courses)} courses:")
    for course in courses:
        print(f"  - {course['course_code']}: {course['name']}")
    
    return courses

def test_get_course_assignments():
    agent = CanvasAgent()
    courses = agent.get_active_courses()
    
    print(f"\nFetching assignments for {len(courses)} courses:\n")
    print("=" * 80)
    
    for course in courses:
        print(f"\n{course['course_code']}: {course['name']}")
        print("-" * 80)
        
        try:
            assignments = agent.get_course_assignments(course['id'])
            print(f"  Found {len(assignments)} assignment(s)")
            
            # Show first 3 assignments as examples
            for i, assignment in enumerate(assignments[:3], 1):
                print(f"  {i}. {assignment['name']}")
                print(f"     Due: {assignment.get('due_at', 'No due date')}")
                
            if len(assignments) > 3:
                print(f"  ... and {len(assignments) - 3} more")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")

def test_get_announcements():
    agent = CanvasAgent()
    courses = agent.get_active_courses()
    
    print(f"\nFetching announcements for {len(courses)} courses:\n")
    print("=" * 80)
    
    for course in courses:
        print(f"\n{course['course_code']}: {course['name']}")
        print("-" * 80)
        
        try:
            announcements = agent.get_course_announcements(course['id'])
            print(f"  Found {len(announcements)} announcement(s)")
            
            for i, announcement in enumerate(announcements[:3], 1):
                print(f"\n  {i}. {announcement.get('title', 'No title')}")
                print(f"     Posted: {announcement.get('posted_at')}")
                # Message is HTML, so just show first 100 chars
                message = announcement.get('message', '')
                if message:
                    clean_msg = message.replace('<p>', '').replace('</p>', '')[:100]
                    print(f"     Preview: {clean_msg}...")
                    
        except Exception as e:
            print(f"  ❌ Error: {e}")

def test_get_course_front_page():
    """Test fetching course front page content."""
    agent = CanvasAgent()
    
    # Get your courses first
    courses = agent.get_active_courses()
    
    if not courses:
        print("No courses found!")
        return
    
    print(f"Found {len(courses)} courses. Testing front page for each...\n")
    print("=" * 80)
    
    # Try to get front page for each course
    for course in courses:
        course_id = course['id']
        course_name = course['name']
        
        print(f"\nCourse: {course_name}")
        print(f"Course ID: {course_id}")
        print("-" * 80)
        
        front_page = agent.get_course_front_page(course_id)
        
        if not front_page:
            print("  ❌ No front page set for this course")
        else:
            print(f"  ✅ Front page found!")
            print(f"  Title: {front_page.get('title', 'N/A')}")
            print(f"  URL: {front_page.get('url', 'N/A')}")
            print(f"  Last updated: {front_page.get('updated_at', 'N/A')}")
            
            # Show first 200 chars of body content
            body = front_page.get('body', '')
            if body:
                preview = body[:200].replace('\n', ' ')
                print(f"  Content preview: {preview}...")
            else:
                print("  (No body content)")
    
    print("\n" + "=" * 80)

def test_quizzes_and_modules():
    """Test fetching quizzes and modules."""
    agent = CanvasAgent()
    
    # Get courses
    courses = agent.get_active_courses()
    
    if not courses:
        print("No courses found!")
        return
    
    print(f"Found {len(courses)} courses\n")
    print("=" * 80)
    
    for course in courses:
        course_id = course['id']
        course_name = course['name']
        
        print(f"\n📚 Course: {course_name}")
        print(f"Course ID: {course_id}")
        print("-" * 80)
        
        # Test Quizzes
        quizzes = agent.get_course_quizzes(course_id)
        print(f"\n  📝 Quizzes: {len(quizzes)}")
        if quizzes:
            for quiz in quizzes[:3]:  # Show first 3
                print(f"    • {quiz.get('title', 'Untitled')}")
                print(f"      Due: {quiz.get('due_at', 'No due date')}")
                print(f"      Points: {quiz.get('points_possible', 'N/A')}")
        
        # Test Modules
        modules = agent.get_course_modules(course_id)
        print(f"\n  📦 Modules: {len(modules)}")
        if modules:
            for module in modules[:3]:  # Show first 3
                print(f"    • {module.get('name', 'Untitled')}")
                print(f"      Position: {module.get('position', 'N/A')}")
                unlock = module.get('unlock_at', 'No unlock date')
                if unlock != 'No unlock date':
                    print(f"      Unlocks: {unlock}")
        
        print()
    
    print("=" * 80)
def test_fetch_all():
    """Test the fetch_all() function to get everything at once."""
    print("Testing fetch_all() - Getting all Canvas data...\n")
    print("=" * 80)
    
    agent = CanvasAgent()
    
    try:
        # Fetch everything
        all_data = agent.fetch_all()
        
        # Print summary
        print("\n📊 FETCH ALL SUMMARY")
        print("=" * 80)
        print(f"Courses: {len(all_data['courses'])}")
        print(f"Assignments: {len(all_data['assignments'])}")
        print(f"Announcements: {len(all_data['announcements'])}")
        print(f"Front Pages: {len(all_data['front_pages'])}")
        print(f"Quizzes: {len(all_data['quizzes'])}")
        print(f"Modules: {len(all_data['modules'])}")
        
        # Show some sample data
        print("\n" + "=" * 80)
        print("📚 COURSES")
        print("=" * 80)
        for course in all_data['courses']:
            print(f"  • {course['name']} ({course['course_code']})")
        
        print("\n" + "=" * 80)
        print("📝 SAMPLE ASSIGNMENTS (first 5)")
        print("=" * 80)
        for assignment in all_data['assignments'][:5]:
            print(f"  • [{assignment['course_code']}] {assignment['name']}")
            print(f"    Due: {assignment.get('due_at', 'No due date')}")
            print(f"    Points: {assignment.get('points_possible', 'N/A')}")
            print()
        
        print("=" * 80)
        print("📢 SAMPLE ANNOUNCEMENTS (first 3)")
        print("=" * 80)
        for announcement in all_data['announcements'][:3]:
            print(f"  • [{announcement['course_code']}] {announcement['title']}")
            print(f"    Posted: {announcement.get('posted_at', 'N/A')}")
            print()
        
        print("=" * 80)
        print("📦 SAMPLE MODULES (first 5)")
        print("=" * 80)
        for module in all_data['modules'][:5]:
            print(f"  • [{module['course_code']}] {module['name']}")
            print(f"    Position: {module.get('position', 'N/A')}")
            print()
        
        print("=" * 80)
        print("✅ fetch_all() completed successfully!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fetch_all()