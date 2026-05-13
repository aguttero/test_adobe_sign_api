class AppError(Exception):
    pass

class DatabaseError(AppError):
    def __init__(self, message, original_exc=None):
        super().__init__(message)
        self.original_exc = original_exc

class APIError(AppError):
    def __init__(self, message, status_code=None, original_exc=None):
        super().__init__(message)
        self.status_code = status_code
        self.original_exc = original_exc

class AuthError(AppError):         # <-- new
    def __init__(self, message, original_exc=None):
        super().__init__(message)
        self.original_exc = original_exc