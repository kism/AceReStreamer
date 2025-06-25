"""These are some tests to ensure that the flask app you have made won't accidentally pollute your tests.

Testing was hell for a couple of days, tests would pass when I just ran one test module, but fail when run all together.
After much frustration I realised that tests were interfering with each other since I was using real directories.
PyTest is multi threaded and thus multiple tests can (and will) be running at the same time.
Without tmp_path they will use each other's config/data.

Tests should always use the tmp_path fixture as an instance_path as it means they won't pollute each other.
And thus in the boilerplate I have some checks to ensure that your tests aren't possibly getting polluted.
"""

import pytest

from acerestreamer import create_app


def test_instance_path_check(get_test_config):
    """TEST: When passed a dictionary as a config, the instance path must be specified."""
    with pytest.raises(ValueError, match="When testing supply both test_config and instance_path!"):
        create_app(test_config=get_test_config("testing_true_valid.toml"))
