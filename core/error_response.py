from http import HTTPStatus
import logging
import time

logger = logging.getLogger(__name__)

class CustomError(Exception):
    def __init__(self, message: str, status: int):
        super().__init__(message)
        self.status = status
        if status == HTTPStatus.INTERNAL_SERVER_ERROR.value:
            logger.error(f"{int(time.time() * 1000)} - {self.status} - {message}")

class ErrorResponse(CustomError):
    def __init__(self, message: str, status: int):
        super().__init__(message, status)

class ConflictError(ErrorResponse):
    def __init__(self, message: str = HTTPStatus.CONFLICT.phrase):
        super().__init__(message, HTTPStatus.CONFLICT.value)

class NotFoundError(ErrorResponse):
    def __init__(self, message: str = HTTPStatus.NOT_FOUND.phrase):
        super().__init__(message, HTTPStatus.NOT_FOUND.value)

class BadRequestError(ErrorResponse):
    def __init__(self, message: str = HTTPStatus.BAD_REQUEST.phrase):
        super().__init__(message, HTTPStatus.BAD_REQUEST.value)

class UnauthorizedError(ErrorResponse):
    def __init__(self, message: str = HTTPStatus.UNAUTHORIZED.phrase):
        super().__init__(message, HTTPStatus.UNAUTHORIZED.value)

class ForbiddenError(ErrorResponse):
    def __init__(self, message: str = HTTPStatus.FORBIDDEN.phrase):
        super().__init__(message, HTTPStatus.FORBIDDEN.value)

class InternalServerError(ErrorResponse):
    def __init__(self, message: str = HTTPStatus.INTERNAL_SERVER_ERROR.phrase):
        super().__init__(message, HTTPStatus.INTERNAL_SERVER_ERROR.value)

class NotImplemented(ErrorResponse):
    def __init__(self, message: str = HTTPStatus.NOT_IMPLEMENTED.phrase):
        super().__init__(message, HTTPStatus.NOT_IMPLEMENTED.value)

class GoneError(ErrorResponse):
    def __init__(self, message: str = HTTPStatus.GONE.phrase):
        super().__init__(message, HTTPStatus.GONE.value)