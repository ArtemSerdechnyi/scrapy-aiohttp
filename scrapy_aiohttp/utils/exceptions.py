class ServerNotAliveError(Exception):
    def __init__(self, message="Server is not running. Cannot stop it."):
        super().__init__(message)


class SettingVariableNotFoundError(Exception):
    def __init__(self, variable_name):
        super().__init__(f"Setting variable '{variable_name}' not found.")
