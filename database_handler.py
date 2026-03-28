
# database_handler.py

class DatabaseHandler:
    """Simple in-memory database handler used for development and testing.

    This replaces a corrupted file and provides basic CRUD helpers for
    working with user records represented as dictionaries.
    """

    def __init__(self):
        # Mock data (will replace with real database later)
        self.mock_users = [
            {'id': 1, 'name': 'John Doe', 'email': 'john@email.com', 'city': 'New York'},
            {'id': 2, 'name': 'Jane Smith', 'email': 'jane@email.com', 'city': 'Los Angeles'},
            {'id': 3, 'name': 'Alice Brown', 'email': 'alice@example.com', 'city': 'Chicago'},
        ]
        self._next_id = max((u['id'] for u in self.mock_users), default=0) + 1

    def list_users(self):
        """Return a shallow copy of all users."""
        return list(self.mock_users)

    def find_user_by_name(self, name: str):
        """Return a list of users whose name contains the given substring (case-insensitive)."""
        name = (name or '').strip().lower()
        if not name:
            return []
        return [u for u in self.mock_users if name in u.get('name', '').lower()]

    def find_user_by_email(self, email: str):
        """Return the user matching the exact email (case-insensitive), or None."""
        email = (email or '').strip().lower()
        for u in self.mock_users:
            if u.get('email', '').lower() == email:
                return u
        return None

    def add_user(self, name: str, email: str, city: str = None):
        """Add a new user and return the created record."""
        user = {'id': self._next_id, 'name': name, 'email': email, 'city': city}
        self.mock_users.append(user)
        self._next_id += 1
        return user

    def remove_user(self, user_id: int):
        """Remove user by id and return the removed record, or None if not found."""
        for i, u in enumerate(self.mock_users):
            if u.get('id') == user_id:
                return self.mock_users.pop(i)
        return None

    def to_dict(self):
        """Return a serializable snapshot of the data."""
        return {'users': self.list_users()}

