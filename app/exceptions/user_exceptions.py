
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
