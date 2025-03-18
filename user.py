class User:
    """Represents a system user."""
    def __init__(self, username: str, email: str):
        self.username = username
        self.email = email

    def get_info(self):
        return {"username": self.username, "email": self.email}
