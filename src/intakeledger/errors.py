class IntakeError(Exception):
    """A stable, payload-free error suitable for CLI and library callers."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
