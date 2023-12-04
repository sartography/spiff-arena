class MissingAccessTokenError(Exception):
    pass


class RefreshTokenStorageError(Exception):
    pass


# These could be either 'id' OR 'access' tokens and we can't always know which


class TokenExpiredError(Exception):
    pass


class TokenInvalidError(Exception):
    pass


class TokenNotProvidedError(Exception):
    pass


class OpenIdConnectionError(Exception):
    pass


class UserNotLoggedInError(Exception):
    pass


class NotAuthorizedError(Exception):
    pass


class PermissionsFileNotSetError(Exception):
    pass


class HumanTaskNotFoundError(Exception):
    pass


class HumanTaskAlreadyCompletedError(Exception):
    pass


class UserDoesNotHaveAccessToTaskError(Exception):
    pass


class InvalidPermissionError(Exception):
    pass


class InvalidRedirectUrlError(Exception):
    pass
