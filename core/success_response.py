from http import HTTPStatus

class SuccessResponse:
    def __init__(self, message: str, status: int, data=None):
        self.message = message
        self.status = status
        self.data = data

class OkResponse(SuccessResponse):
    def __init__(self, message: str = HTTPStatus.OK.phrase, data=None):
        super().__init__(message, HTTPStatus.OK.value, data)

class CreatedResponse(SuccessResponse):
    def __init__(self, message: str = HTTPStatus.CREATED.phrase, data=None):
        super().__init__(message, HTTPStatus.CREATED.value, data)

class NoContentResponse(SuccessResponse):
    def __init__(self, message: str = HTTPStatus.NO_CONTENT.phrase):
        super().__init__(message, HTTPStatus.NO_CONTENT.value)