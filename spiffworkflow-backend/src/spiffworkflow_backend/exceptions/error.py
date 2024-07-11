class MissingAccessTokenError(Exception):
    pass


class RefreshTokenStorageError(Exception):
    pass


class ProcessInstanceMigrationNotSafeError(Exception):
    pass


class ProcessInstanceMigrationError(Exception):
    pass


class ProcessInstanceMigrationUnnecessaryError(Exception):
    pass


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


class TaskMismatchError(Exception):
    pass


class PublishingAttemptWhileLockedError(Exception):
    pass
