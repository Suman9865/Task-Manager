
class UserAlreadyExistsError(Exception):
    pass

class InvalidCredentialsError(Exception):
    pass

class InvalidEmailFormatError(Exception):
    pass

class RateLimitExceededError(Exception):

    def __init__(
        self,
        message: str,
        retry_after: int,
        limit: int
    ):
        self.message = message
        self.retry_after = retry_after
        self.limit = limit

        super().__init__(message)

class AuthenticationError(Exception):
    def __init__(self, message: str = "Could not validate credentials"):
        self.message = message
        super().__init__(self.message)

class ServiceUnavailableError(Exception):

    def __init__(
        self,
        message: str = "Service temporarily unavailable",
        retry_after: int = 5
    ):
        self.message = message
        self.retry_after = retry_after

        super().__init__(self.message)
