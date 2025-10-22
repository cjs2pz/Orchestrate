"""
Canvas Sync Script

Orchestrates the data pipeline between Canvas LMS and PostgreSQL database.
Fetches courses, assignments, announcements, and front pages from Canvas API,
then persists to database with content-based deduplication.

This script is designed to run periodically via GitHub Actions (2x daily).
"""

import sys
import logging
from typing import Dict, Any

from src.agents.canvas_agent import CanvasAgent, CanvasAPIError
from src.storage import (
    insert_course, 
    insert_assignment, 
    insert_announcement, 
    insert_front_page
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def sync_canvas_to_database() -> Dict[str, Any]:
    """
    Fetch all Canvas data and persist to database.
    
    Returns:
        dict: Sync statistics including counts and errors
    """
    stats = {
        'courses': 0,
        'assignments': 0,
        'announcements': 0,
        'front_pages': 0,
        'errors': []
    }
    
    try:
        # Initialize Canvas API client
        logger.info("Initializing Canvas agent")
        agent = CanvasAgent()
        
        # Fetch all data from Canvas
        logger.info("Fetching data from Canvas API")
        canvas_data = agent.fetch_all()
        
        logger.info(f"Retrieved {len(canvas_data['courses'])} courses")
        logger.info(f"Retrieved {len(canvas_data['assignments'])} assignments")
        logger.info(f"Retrieved {len(canvas_data['announcements'])} announcements")
        logger.info(f"Retrieved {len(canvas_data['front_pages'])} front pages")
        
        # Persist courses
        logger.info("Syncing courses to database")
        for course in canvas_data['courses']:
            course_data = {
                'course_id': course['id'],
                'course_code': course['course_code'],
                'course_name': course['name']
            }
            if insert_course(course_data):
                stats['courses'] += 1
        
        # Persist assignments
        logger.info("Syncing assignments to database")
        for assignment in canvas_data['assignments']:
            assignment_data = {
                'assignment_id': assignment['id'],
                'course_id': assignment['course_id'],
                'course_name': assignment['course_name'],
                'name': assignment.get('name', 'Untitled'),
                'description': assignment.get('description'),
                'due_at': assignment.get('due_at'),
                'points_possible': assignment.get('points_possible'),
                'html_url': assignment.get('html_url'),
                'submission_status': assignment.get('submission_types')
            }
            if insert_assignment(assignment_data):
                stats['assignments'] += 1
        
        # Persist announcements
        logger.info("Syncing announcements to database")
        for announcement in canvas_data['announcements']:
            announcement_data = {
                'id': announcement['id'],
                'course_id': announcement['course_id'],
                'course_name': announcement['course_name'],
                'title': announcement.get('title', 'Untitled'),
                'message': announcement.get('message'),
                'posted_at': announcement.get('posted_at'),
                'html_url': announcement.get('html_url')
            }
            if insert_announcement(announcement_data):
                stats['announcements'] += 1
        
        # Persist front pages
        logger.info("Syncing front pages to database")
        for front_page in canvas_data['front_pages']:
            front_page_data = {
                'course_id': front_page['course_id'],
                'course_name': front_page['course_name'],
                'title': front_page.get('title'),
                'body': front_page.get('body'),
                'updated_at': front_page.get('updated_at')
            }
            if insert_front_page(front_page_data):
                stats['front_pages'] += 1
        
        # Log summary
        logger.info("Sync completed successfully")
        logger.info(f"Synced {stats['courses']} courses")
        logger.info(f"Synced {stats['assignments']} assignments")
        logger.info(f"Synced {stats['announcements']} announcements")
        logger.info(f"Synced {stats['front_pages']} front pages")
        
        return stats
        
    except CanvasAPIError as e:
        error_msg = f"Canvas API error: {str(e)}"
        logger.error(error_msg)
        stats['errors'].append(error_msg)
        return stats
        
    except Exception as e:
        error_msg = f"Unexpected error during sync: {str(e)}"
        logger.exception(error_msg)
        stats['errors'].append(error_msg)
        return stats


def main():
    """Entry point for sync script."""
    logger.info("Starting Canvas sync process")
    stats = sync_canvas_to_database()
    
    if stats['errors']:
        logger.error(f"Sync completed with {len(stats['errors'])} errors")
        sys.exit(1)
    else:
        logger.info("Sync process completed successfully")
        sys.exit(0)


if __name__ == "__main__":
    main()