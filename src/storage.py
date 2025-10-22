import psycopg2
from psycopg2 import pool
import os
from dotenv import load_dotenv
import hashlib
from typing import Dict, Any, Optional

# Load environment variables
load_dotenv()

# Database connection pool (production pattern)
# Why? Reusing connections is faster than creating new ones each time
DATABASE_URL = os.getenv('DATABASE_URL')

# Create a connection pool (min 1, max 10 connections)
connection_pool = psycopg2.pool.SimpleConnectionPool(
    1, 10,
    DATABASE_URL
)

def generate_content_hash(data: Dict[str, Any]) -> str:
    """
    Generate SHA-256 hash of content for deduplication.
    
    Why SHA-256? 
    - Fast to compute
    - Collision-resistant (virtually impossible to have 2 different assignments with same hash)
    - Industry standard for content deduplication
    
    Args:
        data: Dictionary of content to hash (assignment fields)
        
    Returns:
        Hex string of hash (64 characters)
    """
    # Convert dict to sorted string to ensure consistent hashing
    content_string = str(sorted(data.items()))
    return hashlib.sha256(content_string.encode()).hexdigest()

def insert_course(course_data: Dict[str, Any]) -> bool:
    """
    Insert a course into the database.
    Uses UPSERT pattern (INSERT ... ON CONFLICT UPDATE) to handle duplicates.
    
    Why UPSERT? If course already exists, update it instead of erroring.
    
    Args:
        course_data: Dict with keys: course_id, course_code, course_name
        
    Returns:
        True if successful, False otherwise
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # UPSERT query - insert or update if exists
        query = """
            INSERT INTO courses (course_id, course_code, course_name, last_synced_at)
            VALUES (%(course_id)s, %(course_code)s, %(course_name)s, NOW())
            ON CONFLICT (course_id) 
            DO UPDATE SET 
                course_code = EXCLUDED.course_code,
                course_name = EXCLUDED.course_name,
                last_synced_at = NOW();
        """
        
        cursor.execute(query, course_data)
        conn.commit()
        cursor.close()
        
        print(f"✅ Inserted/updated course: {course_data['course_name']}")
        return True
        
    except Exception as e:
        if conn:
            conn.rollback()  # Undo changes on error
        print(f"Error inserting course: {e}")
        return False
        
    finally:
        if conn:
            return_connection(conn)

def insert_assignment(assignment_data: Dict[str, Any]) -> bool:
    """
    Insert an assignment into the database with deduplication via content hash.
    
    Why content hash? 
    - Detects if assignment changed (due date moved, description updated)
    - Prevents duplicate entries
    - Hash is based on: name, due_at, description, points
    
    Args:
        assignment_data: Dict with keys:
            - assignment_id (required)
            - course_id (required)
            - course_name (required)
            - name (required)
            - description (optional)
            - due_at (optional)
            - points_possible (optional)
            - html_url (optional)
            - submission_status (optional)
            
    Returns:
        True if successful, False otherwise
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Generate content hash from key fields
        hash_data = {
            'name': assignment_data.get('name'),
            'due_at': assignment_data.get('due_at'),
            'description': assignment_data.get('description'),
            'points_possible': assignment_data.get('points_possible')
        }
        content_hash = generate_content_hash(hash_data)
        
        # UPSERT query
        query = """
            INSERT INTO assignments (
                assignment_id, course_id, course_name, name, description,
                due_at, points_possible, html_url, submission_status,
                content_hash, last_synced_at
            )
            VALUES (
                %(assignment_id)s, %(course_id)s, %(course_name)s, %(name)s, %(description)s,
                %(due_at)s, %(points_possible)s, %(html_url)s, %(submission_status)s,
                %(content_hash)s, NOW()
            )
            ON CONFLICT (assignment_id)
            DO UPDATE SET
                name = EXCLUDED.name,
                description = EXCLUDED.description,
                due_at = EXCLUDED.due_at,
                points_possible = EXCLUDED.points_possible,
                submission_status = EXCLUDED.submission_status,
                content_hash = EXCLUDED.content_hash,
                last_synced_at = NOW(),
                updated_at = NOW();
        """
        
        # Prepare data for query
        query_data = {
            'assignment_id': assignment_data['assignment_id'],
            'course_id': assignment_data['course_id'],
            'course_name': assignment_data['course_name'],
            'name': assignment_data['name'],
            'description': assignment_data.get('description'),
            'due_at': assignment_data.get('due_at'),
            'points_possible': assignment_data.get('points_possible'),
            'html_url': assignment_data.get('html_url'),
            'submission_status': assignment_data.get('submission_status'),
            'content_hash': content_hash
        }
        
        cursor.execute(query, query_data)
        conn.commit()
        cursor.close()
        
        print(f"✅ Inserted/updated assignment: {assignment_data['name']}")
        return True
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error inserting assignment: {e}")
        return False
        
    finally:
        if conn:
            return_connection(conn)

def insert_announcement(announcement_data: Dict[str, Any]) -> bool:
    """
    Insert an announcement into the database with deduplication via content hash.
    
    Args:
        announcement_data: Dict with keys:
            - announcement_id (required) - Canvas ID
            - course_id (required)
            - course_name (required)
            - title (required)
            - message (optional)
            - posted_at (optional)
            - html_url (optional)
            
    Returns:
        True if successful, False otherwise
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Generate content hash from key fields
        hash_data = {
            'title': announcement_data.get('title'),
            'message': announcement_data.get('message'),
            'posted_at': announcement_data.get('posted_at')
        }
        content_hash = generate_content_hash(hash_data)
        
        # UPSERT query
        query = """
            INSERT INTO announcements (
                announcement_id, course_id, course_name, title, message,
                posted_at, html_url, content_hash, last_synced_at
            )
            VALUES (
                %(announcement_id)s, %(course_id)s, %(course_name)s, %(title)s, %(message)s,
                %(posted_at)s, %(html_url)s, %(content_hash)s, NOW()
            )
            ON CONFLICT (announcement_id)
            DO UPDATE SET
                title = EXCLUDED.title,
                message = EXCLUDED.message,
                posted_at = EXCLUDED.posted_at,
                content_hash = EXCLUDED.content_hash,
                last_synced_at = NOW();
        """
        
        # Prepare data for query
        query_data = {
            'announcement_id': announcement_data['id'],  # Canvas returns 'id', not 'announcement_id'
            'course_id': announcement_data['course_id'],
            'course_name': announcement_data['course_name'],
            'title': announcement_data.get('title', 'Untitled'),
            'message': announcement_data.get('message'),
            'posted_at': announcement_data.get('posted_at'),
            'html_url': announcement_data.get('html_url'),
            'content_hash': content_hash
        }
        
        cursor.execute(query, query_data)
        conn.commit()
        cursor.close()
        
        print(f"✅ Inserted/updated announcement: {announcement_data.get('title', 'Untitled')}")
        return True
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error inserting announcement: {e}")
        return False
        
    finally:
        if conn:
            return_connection(conn)

def insert_front_page(front_page_data: Dict[str, Any]) -> bool:
    """
    Insert a course front page into the database with deduplication via content hash.
    
    Why this matters:
    - Some professors put deadlines/announcements on the course homepage
    - We need to detect when homepage content changes
    
    Args:
        front_page_data: Dict with keys:
            - course_id (required)
            - course_name (required)
            - title (optional)
            - body (optional) - HTML content of the page
            - updated_at (optional)
            
    Returns:
        True if successful, False otherwise
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Generate content hash from key fields
        hash_data = {
            'title': front_page_data.get('title'),
            'body': front_page_data.get('body'),
            'updated_at': front_page_data.get('updated_at')
        }
        content_hash = generate_content_hash(hash_data)
        
        # UPSERT query (course_id is PRIMARY KEY, so only one front page per course)
        query = """
            INSERT INTO front_pages (
                course_id, course_name, title, body, updated_at,
                content_hash, last_synced_at
            )
            VALUES (
                %(course_id)s, %(course_name)s, %(title)s, %(body)s, %(updated_at)s,
                %(content_hash)s, NOW()
            )
            ON CONFLICT (course_id)
            DO UPDATE SET
                title = EXCLUDED.title,
                body = EXCLUDED.body,
                updated_at = EXCLUDED.updated_at,
                content_hash = EXCLUDED.content_hash,
                last_synced_at = NOW();
        """
        
        # Prepare data for query
        query_data = {
            'course_id': front_page_data['course_id'],
            'course_name': front_page_data['course_name'],
            'title': front_page_data.get('title'),
            'body': front_page_data.get('body'),
            'updated_at': front_page_data.get('updated_at'),
            'content_hash': content_hash
        }
        
        cursor.execute(query, query_data)
        conn.commit()
        cursor.close()
        
        print(f"✅ Inserted/updated front page for: {front_page_data['course_name']}")
        return True
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f" Error inserting front page: {e}")
        return False
        
    finally:
        if conn:
            return_connection(conn)

def get_connection():
    """Get a connection from the pool"""
    return connection_pool.getconn()

def return_connection(conn):
    """Return a connection to the pool"""
    connection_pool.putconn(conn)