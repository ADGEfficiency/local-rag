import loguru
from rich.console import Console
from rich.logging import RichHandler


def setup_logging(log_level: str) -> None:
    # setup logging
    loguru.logger.remove()
    loguru.logger.add(
        RichHandler(
            console=Console(),
            rich_tracebacks=True,
            tracebacks_show_locals=True,
            tracebacks_extra_lines=2,
            tracebacks_theme="monokai",
            show_path=False,
        ),
        level=log_level,
        format="{message}",
    )
