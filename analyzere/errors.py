class AnalyzeReError(Exception):
    def __init__(self, message=None, http_body=None, http_status=None,
                 json_body=None):
        super(AnalyzeReError, self).__init__(message)
        self.http_body = http_body
        self.http_status = http_status
        self.json_body = json_body


class ServerError(AnalyzeReError):
    pass


class InvalidRequestError(AnalyzeReError):
    pass


class AuthenticationError(AnalyzeReError):
    pass


class RetryAfter(AnalyzeReError):
    pass


class MissingIdError(AnalyzeReError):
    def __init__(self, message=None):
        message = message or 'Object needs an id to complete this operation.'
        super(MissingIdError, self).__init__(message)
