"""Flask webapp acestreamwebplayer."""

from pprint import pformat

from flask import render_template

from . import stream_bp, config, logger
from .flask_helpers import FlaskAcestreamWebplayer

__version__ = "0.0.1"  # This is the version of the app, used in pyproject.toml, enforced in a test.
PROGRAM_NAME = "Acestream Webplayer"  # This is the name of the app, used in the config file.
URL = ""


def create_app(
    test_config: config.AcestreamWebplayerConfig | None = None,
    instance_path: str | None = None,
) -> FlaskAcestreamWebplayer:
    """Create and configure an instance of the Flask application."""
    app = FlaskAcestreamWebplayer(__name__, instance_relative_config=True, instance_path=instance_path)
    app.logger.handlers.clear()

    logger.setup_logger(in_loggers=[])  # Setup flask logger with defaults

    if test_config:  # For Python testing we will often pass in a config
        if not instance_path:
            app.logger.critical("When testing supply both test_config and instance_path!")
            raise AttributeError(instance_path)
        app.aw_conf = test_config

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

    # Now that we have loaded out configuration, we can import our blueprints
    # KISM-BOILERPLATE: This is a demo blueprint blueprint_one.py. Rename the file
    #  and vars to make your own http endpoints and pages. Use multiple blueprints if
    #  you have functionality you can categorise.
    app.register_blueprint(stream_bp.bp)  # Register blueprint

    # For modules that need information from the app object we need to start them under `with app.app_context():`
    # Since in the blueprint_one module, we use `from flask import current_app` to get the app object to get the config
    with app.app_context():
        stream_bp.start_scraper()

    # Flask homepage, generally don't have this as a blueprint.
    @app.route("/")
    def home() -> str:
        """Flask home."""
        return render_template("home.html.j2", __app_nice_name=__name__)  # Return a webpage

    app.logger.info("Starting Web Server")
    app.logger.info("%s version: %s", PROGRAM_NAME, __version__)

    return app
