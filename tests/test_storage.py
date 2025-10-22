import sys
sys.path.append('../src')

from storage import insert_course, insert_assignment, insert_announcement, insert_front_page

# Test data
test_course = {
    'course_id': 147355,
    'course_code': 'CS 3240',
    'course_name': 'Advanced Software Development'
}

test_assignment = {
    'assignment_id': 123456,
    'course_id': 147355,
    'course_name': 'Advanced Software Development',
    'name': 'Test Assignment',
    'description': 'This is a test',
    'due_at': '2025-10-30T23:59:00Z',
    'points_possible': 100,
    'html_url': 'https://canvas.its.virginia.edu/courses/147355/assignments/123456',
    'submission_status': 'not_submitted'
}

test_announcement = {
    'id': 789012,  # Canvas uses 'id' not 'announcement_id'
    'course_id': 147355,
    'course_name': 'Advanced Software Development',
    'title': 'Test Announcement',
    'message': 'This is a test announcement',
    'posted_at': '2025-10-20T10:00:00Z',
    'html_url': 'https://canvas.its.virginia.edu/courses/147355/discussion_topics/789012'
}

test_front_page = {
    'course_id': 147355,
    'course_name': 'Advanced Software Development',
    'title': 'Welcome to CS 3240',
    'body': '<p>Course homepage content here</p>',
    'updated_at': '2025-10-15T12:00:00Z'
}

print("Testing insert_course()...")
insert_course(test_course)

print("\nTesting insert_assignment()...")
insert_assignment(test_assignment)

print("\nTesting insert_announcement()...")
insert_announcement(test_announcement)

print("\nTesting insert_front_page()...")
insert_front_page(test_front_page)

print("\n✅ All tests complete! Check all 4 tables in Supabase.")