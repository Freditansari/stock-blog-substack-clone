from functools import wraps
from flask import request
from sqlalchemy.sql import func
from models import db, SiteVisit

def track_page_visit(func):
    """Decorator to track visits for any page."""
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        visited_url = request.path  # Automatically track full URL
        referrer = request.referrer  # Track where the visitor came from

        # Check if this URL already exists in tracking
        site_visit = SiteVisit.query.filter_by(url=visited_url, referrer=referrer).first()

        if site_visit:
            # ✅ Correct way to update last_visited timestamp
            site_visit.visitor_count += 1
            site_visit.last_visited = db.func.now()  # ✅ Fix: Use `db.func.now()`
        else:
            # Create new record if this URL + referrer combination is new
            site_visit = SiteVisit(url=visited_url, referrer=referrer)
            db.session.add(site_visit)

        db.session.commit()

        return func(*args, **kwargs)

    return wrapper


def require_human_verification(route_function):
    """Decorator to randomly require CAPTCHA verification before accessing a route."""
    def wrapper(*args, **kwargs):
        # ✅ Check if user is already verified
        if session.get("is_human"):
            return route_function(*args, **kwargs)

        # ✅ 30% Chance to Show CAPTCHA
        if random.random() < 0.3:
            return redirect(url_for("captcha"))

        return route_function(*args, **kwargs)

    # Preserve function name & docstring
    wrapper.__name__ = route_function.__name__
    return wrapper
