class ServerNotAliveError(Exception):
    def __init__(self, message="Server is not running. Cannot stop it."):
        super().__init__(message)
