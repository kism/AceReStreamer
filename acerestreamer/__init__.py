"""Flask webapp acerestreamer."""

from pathlib import Path
from pprint import pformat

from acerestreamer import instances
from acerestreamer.blueprints.api import ace_pool as ace_pool_api_bp
from acerestreamer.blueprints.api import auth as auth_api_bp
from acerestreamer.blueprints.api import health as health_api_bp
from acerestreamer.blueprints.api import scraper as scraper_api_bp
from acerestreamer.blueprints.api import streams as stream_api_bp
from acerestreamer.blueprints.web import auth as auth_bp
from acerestreamer.blueprints.web import epg as epg_bp
from acerestreamer.blueprints.web import home as home_bp
from acerestreamer.blueprints.web import info as info_bp
from acerestreamer.blueprints.web import iptv as iptv_bp
from acerestreamer.blueprints.web import streams as stream_bp
from acerestreamer.utils.content_id_infohash_mapping import content_id_infohash_mapping
from acerestreamer.config import AceReStreamerConf
from acerestreamer.utils.flask_helpers import FlaskAceReStreamer, cache, check_static_folder, register_error_handlers
from acerestreamer.utils.logger import get_logger, setup_logger

__version__ = "0.3.7"  # This is the version of the app, used in pyproject.toml, enforced in a test.
PROGRAM_NAME = "Ace ReStreamer"
URL = "https://github.com/kism/ace-restreamer"


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

    app.register_blueprint(home_bp.bp)
    app.register_blueprint(stream_bp.bp)
    app.register_blueprint(auth_bp.bp)
    app.register_blueprint(info_bp.bp)
    app.register_blueprint(epg_bp.bp)
    app.register_blueprint(iptv_bp.bp)
    app.register_blueprint(ace_pool_api_bp.bp)
    app.register_blueprint(auth_api_bp.bp)
    app.register_blueprint(scraper_api_bp.bp)
    app.register_blueprint(health_api_bp.bp)
    app.register_blueprint(stream_api_bp.bp)

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
    content_id_infohash_mapping.load_config(instance_path=app.instance_path)

    app.logger.info("Starting Web Server")
    app.logger.info("%s version: %s", PROGRAM_NAME, __version__)

    register_error_handlers(app)
    cache.init_app(app)

    return app
