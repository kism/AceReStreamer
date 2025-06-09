"""CLI For Adhoc Tasks."""

import argparse
import logging
import sys
from pathlib import Path

from . import __version__
from .config import NginxConfDef, AcestreamWebplayerConfig, ScrapeSiteHTML, ScrapeSiteIPTV, load_config
from .logger import LOG_LEVELS, _set_log_level

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)

logger = logging.getLogger(__name__)


def _check_config_path(config_path: Path, extension: str) -> None:
    """Check if the config path is valid and has the correct extension."""
    if config_path.exists():
        logger.error("Configuration already exists at: %s", config_path)
        logger.info("Exiting")
        sys.exit(1)

    if config_path.is_dir():
        logger.error("The specified path %s is a directory, not a file.", config_path)
        logger.info("Exiting")
        sys.exit(1)

    if config_path.suffix != extension:
        logger.error("Configuration file must have a %s extension, got %s", extension, config_path.suffix)
        logger.info("Exiting")
        sys.exit(1)


def generate_config_file(
    config_path: Path,
    *,
    include_html: bool = False,
    include_iptv: bool = False,
    include_nginx: bool = False,
) -> None:
    """Generate a default configuration file at the specified path."""
    _check_config_path(config_path, ".toml")

    logger.info("Generating default configuration file at %s", config_path)
    config = AcestreamWebplayerConfig()

    if include_html:
        logger.info("Including HTML scraper in the configuration.")
        config.app.ace_scrape_settings.site_list_html.append(ScrapeSiteHTML())

    if include_iptv:
        logger.info("Including IPTV M3U8 scraper in the configuration.")
        config.app.ace_scrape_settings.site_list_iptv_m3u8.append(ScrapeSiteIPTV())

    if include_nginx:
        logger.info("Including Nginx configuration in the configuration.")
        config.nginx = NginxConfDef()

    config.write_config(config_location=config_path)


def generate_nginx_config_file(config: AcestreamWebplayerConfig, nginx_config_path: Path) -> None:
    """Generate a default Nginx configuration file at the specified path."""
    _check_config_path(nginx_config_path, ".conf")

    logger.info("Generating default Nginx configuration file at %s", nginx_config_path)

    flask_server_address = config.flask.SERVER_NAME.rstrip("/")  # Ensure no trailing slash
    if not config.nginx:
        logger.error("Nginx server_name is not set in the configuration.")
        logger.info("Exiting")
        sys.exit(1)

    nginx_server_name = config.nginx.server_name

    nginx_config = f"""
    server {{
        listen 80;
        server_name {nginx_server_name};

        location / {{
            proxy_pass {flask_server_address};
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }}
    }}
    """
    logger.info("Nginx configuration content:\n%s", nginx_config)


def main() -> None:
    """Main CLI for adhoc tasks."""
    parser = argparse.ArgumentParser(description="Acestream Webplayer CLI for generating config.")
    parser.add_argument(
        "--version",
        action="store_true",
        help="Show the version of the Acestream Webplayer.",
    )
    parser.add_argument(
        "--config-path",
        type=Path,
        default=None,
        required=True,
    )
    parser.add_argument(
        "--generate-app-config",
        action="store_true",
        help="Generate a default configuration file.",
    )
    parser.add_argument(
        "--generate-app-config-html-scraper",
        action="store_true",
        help="Include a scraper for HTML sites in the generated configuration.",
    )
    parser.add_argument(
        "--generate-app-config-iptv-scraper",
        action="store_true",
        help="Include a scraper for IPTV M3U8 sites in the generated configuration.",
    )
    parser.add_argument(
        "--generate-app-config-nginx",
        action="store_true",
        help="Include Nginx configuration in the generated configuration.",
    )
    parser.add_argument(
        "--generate-nginx-config-path",
        type=Path,
        default=None,
        required=False,
        help="Generate a default Nginx configuration file.",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=LOG_LEVELS,
        help="Set the logging level for the application.",
    )
    args = parser.parse_args()

    _set_log_level(logger, args.log_level)

    logger.info("Acestream Webplayer CLI %s started with log level: %s", __version__, args.log_level)

    if args.version:
        logger.info("Acestream Webplayer version %s", __version__)
        sys.exit(0)

    if args.generate_app_config:
        logger.info("Generating configuration file at %s", args.config_path)
        generate_config_file(
            args.config_path,
            include_html=args.generate_app_config_html_scraper,
            include_iptv=args.generate_app_config_iptv_scraper,
            include_nginx=args.generate_app_config_nginx,
        )
        sys.exit(0)

    if args.generate_nginx_config_path:
        logger.info("Generating Nginx configuration file at %s", args.config_path)
        app_config = load_config(args.config_path)
        generate_nginx_config_file(
            app_config,
            nginx_config_path=args.generate_nginx_config_path,
        )
        sys.exit(0)


if __name__ == "__main__":
    main()
