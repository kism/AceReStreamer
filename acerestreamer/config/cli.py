"""CLI For Config generation."""

import argparse
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from acerestreamer import __version__
from acerestreamer.utils.constants import TEMPLATES_DIRECTORY
from acerestreamer.utils.logger import LOG_LEVELS, get_logger, setup_logger

from .models import (
    AceReStreamerConf,
    EPGInstanceConf,
    NginxConf,
    ScrapeSiteHTML,
    ScrapeSiteIPTV,
)

logger = get_logger(__name__)

GENERATE_HELP = """Help for --generate
Comma separated list of things to generate, if you do not specify anything, it will generate with default settings.
Example: --generate html,iptv,nginx
app config: `html`, `iptv`, `nginx`
    html: Include HTML scraper in the app config.
    iptv: Include IPTV M3U8 scraper in the app config.
    nginx: Include Nginx configuration in the app config.
nginx config: `complete`
    complete: Instead of generating a config for a site, generate a complete Nginx configuration file."""

TEMPLATES_DIR = TEMPLATES_DIRECTORY / "templates" / "nginx"


def _check_config_path(
    config_path: Path,
    extension: str,
    *,
    expect_config: bool = True,
    overwrite: bool = False,
) -> None:
    """Check if the config path is valid and has the correct extension."""
    cannot_proceed = False

    if expect_config and not config_path.is_file():
        logger.error("No configuration at: %s", config_path)
        cannot_proceed = True

    if overwrite:  # If we want to overwrite, we don't care if the file exists, break from this check
        pass
    elif (
        not expect_config  # If we don't expect a config, we continue this check
        and config_path.is_file()  # Fail if the file exists, since we are not expecting a config
    ):
        logger.error("Configuration file already exists at: %s", config_path)
        logger.error("Use --overwrite to overwrite the existing configuration file.")
        cannot_proceed = True

    if config_path.suffix != extension:
        logger.error("Configuration file must have a %s extension, got %s", extension, config_path.suffix)
        cannot_proceed = True

    if config_path.is_dir():
        logger.error("The specified path %s is a directory, not a file.", config_path)
        cannot_proceed = True

    if cannot_proceed:
        logger.error("Exiting due to configuration path issues.")
        sys.exit(1)


def generate_app_config_file(
    app_config_path: Path,
    generate_options: list[str],
    *,
    overwrite: bool = False,
) -> None:
    """Generate a default configuration file at the specified path."""
    msg = (
        f"Overwriting existing configuration file at {app_config_path}"
        if overwrite
        else f"Generating configuration file at {app_config_path}"
    )
    _check_config_path(app_config_path, ".json", expect_config=False, overwrite=overwrite)

    logger.info(msg)

    config = AceReStreamerConf()
    if app_config_path.is_file():  # If we are here, we are overwriting
        try:
            logger.info("Loading existing configuration from %s", app_config_path)
            config = AceReStreamerConf.load_config(app_config_path)
        except Exception:  # noqa: BLE001 Naa, we are generating config
            logger.error("Failed to load existing configuration")  # noqa: TRY400 Naa, we are generating config
            logger.info("Generating a new configuration file instead.")

    if "html" in generate_options:
        logger.info("Including HTML scraper in the configuration.")
        config.scraper.html.clear()
        config.scraper.html.append(ScrapeSiteHTML())

    if "iptv" in generate_options:
        logger.info("Including IPTV M3U8 scraper in the configuration.")
        config.scraper.iptv_m3u8.clear()
        config.scraper.iptv_m3u8.append(ScrapeSiteIPTV())

    if "epg" in generate_options:
        logger.info("Including EPG scraper in the configuration.")
        config.epgs.clear()
        config.epgs.append(EPGInstanceConf())

    if "nginx" in generate_options:
        logger.info("Including Nginx configuration in the configuration.")
        config.nginx = NginxConf()

    config.write_config(config_location=app_config_path)


def generate_nginx_config_file(
    app_config_path: Path,
    nginx_config_path: Path,
    generate_options: list[str],
    *,
    overwrite: bool = False,
) -> None:
    """Generate a default Nginx configuration file at the specified path."""
    # Check the app config path and load
    _check_config_path(app_config_path, ".json", expect_config=True)
    app_config = AceReStreamerConf.load_config(app_config_path)

    # Check the nginx config path
    _check_config_path(
        nginx_config_path,
        ".conf",
        expect_config=False,
        overwrite=overwrite,
    )

    flask_server_address = app_config.flask.SERVER_NAME.rstrip("/")  # Ensure no trailing slash
    if not app_config.nginx:
        logger.error("No nginx section in the app configuration, please regenerate.")
        logger.error("Generate the nginx configuration by running the CLI with --generate nginx.")
        logger.info("Exiting")
        sys.exit(1)

    required_fields = [app_config.nginx.server_name, app_config.nginx.cert_path, app_config.nginx.cert_key_path]
    if app_config.nginx.ip_allow_list_path == "":
        app_config.nginx.ip_allow_list_path = (Path("instance") / "ip_allow_list.conf").absolute()

    if isinstance(app_config.nginx.ip_allow_list_path, str):
        app_config.nginx.ip_allow_list_path = Path(app_config.nginx.ip_allow_list_path)

    if not app_config.nginx.ip_allow_list_path.is_file():
        with app_config.nginx.ip_allow_list_path.open("w", encoding="utf-8") as f:
            f.write("deny all;")

    if not all(required_fields):
        logger.error("Nginx configuration is missing required fields: server_name, cert_path, cert_key_path.")
        logger.info("Please set these fields in the app configuration file.")
        logger.info("Exiting")
        sys.exit(1)

    if "complete" in generate_options:
        logger.info("Generating COMPLETE Nginx configuration")
        logger.debug("Generating COMPLETE Nginx configuration file part 1.")
    else:
        logger.info("Generating SITE Nginx configuration file.")

    context = {
        "flask_server_address": flask_server_address,
        "nginx_server_name": app_config.nginx.server_name,
        "dhparam_path": app_config.nginx.dhparam_path,
        "cert_path": app_config.nginx.cert_path,
        "cert_key_path": app_config.nginx.cert_key_path,
        "extra_config_file_path": app_config.nginx.extra_config_file_path,
        "ip_allow_list_path": app_config.nginx.ip_allow_list_path,
    }

    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=True)
    template = env.get_template("site.conf.j2")
    nginx_config = template.render(context)

    if "complete" in generate_options:
        logger.debug("Generating COMPLETE Nginx configuration file part 2.")
        indented = "\n".join("    " + line for line in nginx_config.splitlines()) + "\n"
        complete_template = env.get_template("complete.conf.j2")
        nginx_config = complete_template.render({"servers": indented})

    with nginx_config_path.open("w", encoding="utf-8") as f:
        f.write(nginx_config)

    logger.info("Nginx configuration file generated successfully at %s", nginx_config_path)

    logger.info("Creating allowlist file at %s", app_config.nginx.ip_allow_list_path)
    with app_config.nginx.ip_allow_list_path.open("w", encoding="utf-8") as f:
        f.write("deny all;")


def main() -> None:
    """Main CLI for adhoc tasks."""
    parser = argparse.ArgumentParser(description=f"Acestream Webplayer CLI {__version__} for generating config.")
    parser.add_argument(
        "--app-config",
        type=Path,
        default=None,
        help="Path to save the generated application configuration file.",
    )
    parser.add_argument(
        "--nginx-config",
        type=Path,
        default=None,
        help="Path to save the generated Nginx configuration file.",
    )
    parser.add_argument(
        "--generate",
        type=lambda x: x.lower(),
        default="",
        help="Comma separated extra things to generate. --generate help for more details.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing configuration files if they exist.",
        default=False,
    )
    parser.add_argument(
        "--log-level",
        type=lambda x: x.upper(),
        default="INFO",
        choices=LOG_LEVELS,
        help="Set the logging level for the application.",
    )
    args = parser.parse_args()

    setup_logger(
        log_level=args.log_level,
        console_only=True,  # Only log to console for CLI
    )

    if args.generate == "help":
        logger.info(GENERATE_HELP)
        sys.exit(0)

    if args.app_config is None:
        logger.error("No application configuration path provided. Use --app-config to specify a path.")
        sys.exit(1)

    logger.info("Acestream Webplayer CLI %s started with log level: %s", __version__, args.log_level)

    if not args.nginx_config:  # Generate app config
        print()  # noqa: T201
        logger.info("--- Generating app configuration ---")
        generate_app_config_file(
            app_config_path=args.app_config,
            generate_options=args.generate.split(",") if args.generate else [],
            overwrite=args.overwrite,
        )
        sys.exit(0)
    elif args.nginx_config:  # Generate nginx config
        print()  # noqa: T201
        logger.info("--- Generating Nginx configuration ---")
        generate_nginx_config_file(
            app_config_path=args.app_config,
            generate_options=args.generate.split(",") if args.generate else [],
            nginx_config_path=args.nginx_config,
            overwrite=args.overwrite,
        )
        sys.exit(0)
