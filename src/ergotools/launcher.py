"""Launch the integrated application independently of the working directory.

Desktop composition entry layer. Delegate runtime wiring to bootstrap and keep installed
startup independent of source checkout paths.
"""

import sys

from ergotools.bootstrap import application_settings_path
from ergotools.bootstrap import main as desktop_main


def main(argv: list[str] | None = None) -> int:
    """Run the integrated desktop with per-user settings or an explicit override.

    Installed console scripts and module execution share this entry point. The original
    development bootstrap flags remain available for diagnostic use. Assets are loaded
    from the installed package, never from the launch folder. A positional project path
    is forwarded to the normal desktop Open workflow. No dependency installation or
    automatic project saving occurs here.

    Args:
        argv: Arguments without program name; None forwards current process arguments,
            preserving a positional project path.

    Returns:
        Integrated desktop exit status after injecting the integrated-preview flag and a
        per-user settings path unless explicitly supplied.

    Raises:
        OSError: Qt supplies no configuration path or application settings/resources
            cannot be accessed.
        SystemExit: The delegated CLI parser handles help or invalid arguments.
    """
    arguments = list(sys.argv[1:] if argv is None else argv)
    if not any(a == "--settings" or a.startswith("--settings=") for a in arguments):
        arguments.extend(("--settings", str(application_settings_path())))
    return desktop_main(["--integrated-preview", *arguments])


if __name__ == "__main__":
    raise SystemExit(main())
