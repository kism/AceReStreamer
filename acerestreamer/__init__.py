"""Flask webapp acerestreamer."""

from pprint import pformat

from . import authentication_bp, config, epg_bp, info_bp, logger, scraper_cache, scraper_helpers, stream_bp
from .flask_helpers import FlaskAceReStreamer, cache, check_static_folder, register_error_handlers

__version__ = "0.3.0"  # This is the version of the app, used in pyproject.toml, enforced in a test.
PROGRAM_NAME = "Ace ReStreamer"
URL = "https://github.com/kism/ace-restreamer"


def create_app(
    test_config: config.AceReStreamerConf | None = None,
    instance_path: str | None = None,
) -> FlaskAceReStreamer:
    """Create and configure an instance of the Flask application."""
    app = FlaskAceReStreamer(__name__, instance_relative_config=True, instance_path=instance_path)
    app.logger.handlers.clear()

    logger.setup_logger(in_loggers=[])  # Setup flask logger with defaults

    if test_config:  # For Python testing we will often pass in a config
        if not instance_path:
            app.logger.critical("When testing supply both test_config and instance_path!")
            raise AttributeError(instance_path)
        app.aw_conf = test_config

    check_static_folder(app.static_folder)

    app.logger.debug("Instance path is: %s", app.instance_path)

    logger.setup_logger(  # Setup logger with config
        log_level=app.aw_conf.logging.level,
        log_path=app.aw_conf.logging.path,
        in_loggers=[],
    )

    # Flask config, at the root of the config object.
    app.config.from_mapping(app.aw_conf.flask.model_dump())

    # Do some debug logging of config
    app_config_str = ">>>\nFlask config:"
    for key, value in app.config.items():
        app_config_str += f"\n  {key}: {pformat(value)}"

    app.logger.debug(app_config_str)

    app.register_blueprint(stream_bp.bp)
    app.register_blueprint(authentication_bp.bp)
    app.register_blueprint(info_bp.bp)
    app.register_blueprint(epg_bp.bp)

    # Start the objects
    scraper_cache.scraper_cache.load_config(instance_path=app.instance_path)
    scraper_helpers.m3u_replacer.load_config(instance_path=app.instance_path)
    stream_bp.ace_scraper.load_config(
        ace_scrape_settings=app.aw_conf.scraper,
        instance_path=app.instance_path,
    )
    stream_bp.ace_pool.load_config(
        app_config=app.aw_conf.app,
    )
    authentication_bp.ip_allow_list.load_config(
        instance_path=app.instance_path,
        nginx_allowlist_path=app.aw_conf.nginx.ip_allow_list_path if app.aw_conf.nginx else None,
    )
    epg_bp.epg_handler.load_config(
        epg_conf_list=app.aw_conf.epgs,
        instance_path=app.instance_path,
    )

    app.logger.info("Starting Web Server")
    app.logger.info("%s version: %s", PROGRAM_NAME, __version__)

    register_error_handlers(app)
    cache.init_app(app)

    return app
