""" 
Canvas Agent Module

Fetches course assignments from Canvas using the REST API.

CANVAS API OVERVIEW:
- RESTful API with token authentication
- Rate limit: 3000 requests/hour 
- Returns max 100 items per request (pagination available)
- Docs: https://developerdocs.instructure.com/services/canvas

ARCHITECTURAL NOTE:
- Canvas API is simple REST - just HTTP GET requests
- No LangChain needed for simple data fetching
- Keeping it simple = easier to debug and faster execution

"""

from datetime import datetime, timedelta
from typing import List, Dict, Any
import requests

from src.utils.config import config


class CanvasAPIError(Exception):
    """Custom exception for Canvas API errors."""
    pass


class CanvasAgent:
    """
    Agent for fetching assignments from Canvas LMS.

    Agent knows how to:
    - Authenticate using API token
    - Get a list of courses
    - Fetch assignments for each course
    - Normalize data to our standard format
    """

    def __init__(self):
        # Validate config on initialization
        config.validate_canvas()

        self.base_url = config.CANVAS_BASE_URL.rstrip('/')
        self.api_token = config.CANVAS_API_TOKEN

        # Create HTTP session with auth headers
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_token}', 
            'Accept': 'application/json'
        })

    def _make_request(self, endpoint: str) -> Any:
        """
        Make GET request to Canvas API.
        All API calls go through here.
        
        Args:
            endpoint: API endpoint (e.g., '/api/v1/courses')
            
        Returns:
            JSON response (dict or list)
            
        Raises:
            CanvasAPIError: If request fails
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()  # Raises exception for 4xx/5xx
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            # Canvas returns error details in response body
            try:
                error_msg = response.json().get('errors', [{}])[0].get('message', str(e))
            except:
                error_msg = str(e)
            raise CanvasAPIError(f"Canvas API error: {error_msg}")
            
        except requests.exceptions.RequestException as e:
            raise CanvasAPIError(f"Network error: {str(e)}")

    def get_active_courses(self) -> List[Dict[str, Any]]:
        """
        Fetch list of active courses for the user.
        Uses favorites if set, otherwise returns all active courses.
        
        Returns:
            List of course dicts with keys: id, name, course_code
        """
        # Try favorites first
        endpoint = '/api/v1/users/self/favorites/courses'
        courses = self._make_request(endpoint)
        
        active = [
            {
                'id': course['id'],
                'name': course.get('name', 'Unnamed Course'),
                'course_code': course.get('course_code', 'N/A')
            }
            for course in courses
        ]
        
        return active
    
    def get_course_assignments(self, course_id: int) -> List[Dict[str, Any]]:
        """
        Fetch ALL assignments for a specific course.
        
        Args:
            course_id: Canvas course ID
            
        Returns:
            List of ALL assignment dictionaries (with or without due dates)
        """
        endpoint = f'/api/v1/courses/{course_id}/assignments?per_page=100'
        assignments = self._make_request(endpoint)
        
        # Handle None case (shouldn't happen, but being safe)
        if assignments is None:
            return []
        
        return assignments
    
    def get_course_announcements(self, course_id: int, days_back: int = 120) -> List[Dict[str, Any]]:
        """
        Fetch announcements for a specific course.
        
        Args:
            course_id: Canvas course ID
            days_back: How many days back to look (default 120 = ~4 months)
            
        Returns:
            List of announcement dictionaries
        """
        # Start from X days ago, end today
        start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        endpoint = (
            f'/api/v1/announcements?'
            f'context_codes[]=course_{course_id}&'
            f'start_date={start_date}&'
            f'end_date={end_date}&'
            f'per_page=100'
        )
        
        announcements = self._make_request(endpoint)
        
        if announcements is None:
            return []
        
        return announcements
    
    def get_course_front_page(self, course_id: int) -> Dict[str, Any]:
        """
        Fetch the front page (home page) content for a specific course.
        
        Args:
            course_id: Canvas course ID
            
        Returns:
            Dictionary containing front page data, or empty dict if no front page exists
        """
        endpoint = f'/api/v1/courses/{course_id}/front_page'
        
        front_page = self._make_request(endpoint)
        
        # Handle None case (course might not have a front page set)
        if front_page is None:
            return {}
        
        return front_page
    
    def get_course_quizzes(self, course_id: int) -> List[Dict[str, Any]]:
        """
        Fetch quizzes for a specific course.
        
        Args:
            course_id: Canvas course ID
            
        Returns:
            List of quiz dictionaries, or empty list if quizzes not available
        """
        endpoint = f'/api/v1/courses/{course_id}/quizzes'
        
        try:
            quizzes = self._make_request(endpoint)
            
            if quizzes is None:
                return []
            
            return quizzes
        except CanvasAPIError as e:
            # If 404, course probably doesn't have quizzes or feature disabled
            if "404" in str(e):
                return []
            # Re-raise other errors
            raise
    
    def get_course_modules(self, course_id: int) -> List[Dict[str, Any]]:
        """
        Fetch modules for a specific course.
        
        Args:
            course_id: Canvas course ID
            
        Returns:
            List of module dictionaries
        """
        endpoint = f'/api/v1/courses/{course_id}/modules'
        
        modules = self._make_request(endpoint)
        
        if modules is None:
            return []
        
        return modules
    
    def fetch_all(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fetch ALL data from all active courses.
        
        Returns a dictionary organized by course with all available data:
        {
            'courses': [...],
            'assignments': [...],
            'announcements': [...],
            'front_pages': [...],
            'quizzes': [...],
            'modules': [...]
        }
        
        Each item includes course metadata for easy filtering.
        """
        result = {
            'courses': [],
            'assignments': [],
            'announcements': [],
            'front_pages': [],
            'quizzes': [],
            'modules': []
        }
        
        # Get all courses
        courses = self.get_active_courses()
        result['courses'] = courses
        
        # For each course, fetch everything
        for course in courses:
            course_id = course['id']
            course_name = course['name']
            course_code = course['course_code']
            
            # Add course context to each item
            course_context = {
                'course_id': course_id,
                'course_name': course_name,
                'course_code': course_code
            }
            
            # Get assignments
            assignments = self.get_course_assignments(course_id)
            for assignment in assignments:
                assignment.update(course_context)
            result['assignments'].extend(assignments)
            
            # Get announcements
            announcements = self.get_course_announcements(course_id)
            for announcement in announcements:
                announcement.update(course_context)
            result['announcements'].extend(announcements)
            
            # Get front page
            front_page = self.get_course_front_page(course_id)
            if front_page:
                front_page.update(course_context)
                result['front_pages'].append(front_page)
            
            # Get quizzes
            quizzes = self.get_course_quizzes(course_id)
            for quiz in quizzes:
                quiz.update(course_context)
            result['quizzes'].extend(quizzes)
            
            # Get modules
            modules = self.get_course_modules(course_id)
            for module in modules:
                module.update(course_context)
            result['modules'].extend(modules)
        
        return result