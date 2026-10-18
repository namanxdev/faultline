"""The drift interface. A drift is stateless; per-trial state lives on the tool service."""


class ToolFailure(Exception):
    """A deliberate error that the agent is allowed to see."""


class Drift:
    name = "baseline"
    rationale = "Stable tools: the control condition."

    def specs(self, service, specs: list) -> list:
        """Change the published tool list (names, parameters, descriptions)."""
        return specs

    def before(self, service, name: str, args: dict) -> dict:
        """Translate or reject arguments before the call is counted."""
        return args

    def gate(self, service, name: str, args: dict) -> None:
        """Fail a counted call before it runs."""

    def after(self, service, name: str, args: dict, result: dict) -> dict:
        """Change or fail a result after the call ran."""
        return result

    def policy_version(self) -> int | None:
        return None
