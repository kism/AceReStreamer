"""Flask webapp acerestreamer."""

from pathlib import Path
from pprint import pformat

from . import (
    _obj_instances,
    authentication_bp,
    config,
    epg_bp,
    info_bp,
    iptv_bp,
    logger,
    stream_bp,
    ace_pool_api_bp,
    scraper_api_bp,
    health_api_bp,
)
from .flask_helpers import FlaskAceReStreamer, cache, check_static_folder, register_error_handlers

__version__ = "0.3.2"  # This is the version of the app, used in pyproject.toml, enforced in a test.
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
            msg = "When testing supply both test_config and instance_path!"
            app.logger.critical(msg)
            raise ValueError(msg)
        app.aw_conf = test_config
    else:
        app.logger.info("Loading real configuration from instance path: %s", app.instance_path)
        config_path = Path(app.instance_path) / "config.toml"
        app.aw_conf = config.load_config(config_path)

    check_static_folder(app.static_folder)

    app.logger.debug("Instance path is: %s", app.instance_path)

    logger.setup_logger(  # Setup logger with config
        log_level=app.aw_conf.logging.level,
        log_path=app.aw_conf.logging.path,
        in_loggers=[],
    )
    app.logger = logger.get_logger(__name__)

    # Flask config, at the root of the config object.
    app.config.from_mapping(app.aw_conf.flask.model_dump())

    # Do some debug logging of config
    app_config_str = ">>>\nFlask config:"
    for key, value in app.config.items():
        app_config_str += f"\n  {key}: {pformat(value)}"

    app.logger.trace(app_config_str)

    app.register_blueprint(stream_bp.bp)
    app.register_blueprint(authentication_bp.bp)
    app.register_blueprint(info_bp.bp)
    app.register_blueprint(epg_bp.bp)
    app.register_blueprint(iptv_bp.bp)
    app.register_blueprint(ace_pool_api_bp.bp)
    app.register_blueprint(scraper_api_bp.bp)
    app.register_blueprint(health_api_bp.bp)

    # Start the objects
    _obj_instances.scraper_cache.load_config(instance_path=app.instance_path)
    _obj_instances.m3u_replacer.load_config(instance_path=app.instance_path)
    _obj_instances.ace_scraper.load_config(
        ace_scrape_settings=app.aw_conf.scraper,
        instance_path=app.instance_path,
    )
    _obj_instances.ace_pool.load_config(
        app_config=app.aw_conf.app,
    )
    _obj_instances.ip_allow_list.load_config(
        instance_path=app.instance_path,
        nginx_allowlist_path=app.aw_conf.nginx.ip_allow_list_path if app.aw_conf.nginx else None,
    )
    _obj_instances.epg_handler.load_config(
        epg_conf_list=app.aw_conf.epgs,
        instance_path=app.instance_path,
    )

    app.logger.info("Starting Web Server")
    app.logger.info("%s version: %s", PROGRAM_NAME, __version__)

    register_error_handlers(app)
    cache.init_app(app)

    return app
