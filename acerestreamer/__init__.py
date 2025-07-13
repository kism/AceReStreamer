"""Flask webapp acerestreamer."""

from pathlib import Path
from pprint import pformat

from acerestreamer import instances, instances_mapping
from acerestreamer.blueprints import api as api_bps
from acerestreamer.blueprints import web as web_bps
from acerestreamer.config import AceReStreamerConf
from acerestreamer.utils.flask_helpers import FlaskAceReStreamer, cache, check_static_folder, register_error_handlers
from acerestreamer.utils.logger import get_logger, setup_logger
from acerestreamer.version import PROGRAM_NAME, __version__


def create_app(
    test_config: AceReStreamerConf | None = None,
    instance_path: str | None = None,
) -> FlaskAceReStreamer:
    """Create and configure an instance of the Flask application."""
    app = FlaskAceReStreamer(__name__, instance_relative_config=True, instance_path=instance_path)
    app.logger.handlers.clear()

    setup_logger(in_loggers=[])  # Setup flask logger with defaults

    if test_config:  # For Python testing we will often pass in a config
        if not instance_path:
            msg = "When testing supply both test_config and instance_path!"
            app.logger.critical(msg)
            raise ValueError(msg)
        app.are_conf = test_config
    else:
        app.logger.info("Loading real configuration from instance path: %s", app.instance_path)
        config_path = Path(app.instance_path) / "config.json"
        app.are_conf = AceReStreamerConf.load_config(config_path)

    check_static_folder(app.static_folder)

    app.logger.debug("Instance path is: %s", app.instance_path)

    setup_logger(  # Setup logger with config
        log_level=app.are_conf.logging.level,
        log_path=app.are_conf.logging.path,
        in_loggers=[],
    )
    app.logger = get_logger(__name__)

    # Flask config, at the root of the config object.
    app.config.from_mapping(app.are_conf.flask.model_dump())

    # Do some debug logging of config
    app_config_str = ">>>\nFlask config:"
    for key, value in app.config.items():
        app_config_str += f"\n  {key}: {pformat(value)}"

    app.logger.trace(app_config_str)

    app.register_blueprint(web_bps.home_bp)
    app.register_blueprint(web_bps.streams_bp)
    app.register_blueprint(web_bps.auth_bp)
    app.register_blueprint(web_bps.info_bp)
    app.register_blueprint(web_bps.epg_bp)
    app.register_blueprint(web_bps.iptv_bp)
    app.register_blueprint(api_bps.ace_pool_bp)
    app.register_blueprint(api_bps.auth_bp)
    app.register_blueprint(api_bps.epg_bp)
    app.register_blueprint(api_bps.scraper_bp)
    app.register_blueprint(api_bps.health_bp)
    app.register_blueprint(api_bps.streams_bp)
    app.register_blueprint(api_bps.xc_bp)

    # Start the mapping objects, these first since the objects in the next section want them loaded
    instances_mapping.content_id_infohash_mapping.load_config(
        instance_path=app.instance_path,
        ace_url=app.are_conf.app.ace_address,
    )
    instances_mapping.content_id_xc_id_mapping.load_config(
        instance_path=app.instance_path,
    )
    instances_mapping.category_xc_category_id_mapping.load_config(
        instance_path=app.instance_path,
    )

    # Start the objects
    instances.ace_scraper.load_config(
        ace_scrape_settings=app.are_conf.scraper,
        instance_path=app.instance_path,
        epg_conf_list=app.are_conf.epgs,
        external_url=app.are_conf.flask.SERVER_NAME,
        ace_url=app.are_conf.app.ace_address,
    )
    instances.ace_pool.load_config(
        app_config=app.are_conf.app,
    )
    instances.ip_allow_list.load_config(
        instance_path=app.instance_path,
        password=app.are_conf.app.password,
    )

    app.logger.info("Starting Web Server: %s", app.are_conf.flask.SERVER_NAME)
    app.logger.info("%s version: %s", PROGRAM_NAME, __version__)

    register_error_handlers(app)
    cache.init_app(app)

    return app
