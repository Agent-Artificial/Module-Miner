import pytest
import os
import requests
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path
from base.base_module import BaseModule, ModuleConfig


@pytest.fixture
def module_config():
    return ModuleConfig(
        module_path="test_path",
        module_url="http://test_url",
        module_name="test_module",
        module_endpoint="/test_endpoint",
    )


@pytest.fixture
def base_module(module_config):
    return BaseModule(module_config=module_config)


@pytest.mark.parametrize(
    "path_exists, user_input, expected",
    [(True, "y", None), (True, "n", "file content"), (False, "", None)],
    ids=["overwrite", "keep_existing", "file_not_exist"],
)
def test_check_and_prompt(path_exists, user_input, expected, base_module):
    # Arrange
    path = Path("test_path/file.txt")
    message = "Test message"
    with patch("builtins.input", return_value=user_input), patch(
        "pathlib.Path.exists", return_value=path_exists
    ), patch("pathlib.Path.read_text", return_value="file content"):

        # Act
        result = base_module._check_and_prompt(path, message)

    # Assert
    assert result == expected


@pytest.mark.parametrize(
    "public_key_exists, user_input, expected",
    [(True, "y", None), (True, "n", "public key content"), (False, "", None)],
    ids=["overwrite_public_key", "keep_existing_public_key", "public_key_not_exist"],
)
def test_check_public_key(public_key_exists, user_input, expected, base_module):
    # Arrange
    with patch("builtins.input", return_value=user_input), patch(
        "pathlib.Path.exists", return_value=public_key_exists
    ), patch("pathlib.Path.read_text", return_value="public key content"):

        # Act
        result = base_module.check_public_key()

    # Assert
    assert result == expected


@pytest.mark.parametrize(
    "existing_key, expected",
    [(None, "new_public_key"), ("existing_public_key", "existing_public_key")],
    ids=["new_key", "existing_key"],
)
def test_get_public_key(existing_key, expected, base_module):
    # Arrange
    with patch("requests.get", return_value=MagicMock(text="new_public_key")), patch(
        "base.base_module.BaseModule.check_public_key", return_value=existing_key
    ), patch("pathlib.Path.write_text") as mock_write_text:

        # Act
        result = base_module.get_public_key()

    # Assert
    if existing_key is None:
        mock_write_text.assert_called_once_with("new_public_key", encoding="utf-8")
    assert result == expected


@pytest.mark.parametrize(
    "module_exists, user_input, expected",
    [(True, "y", None), (True, "n", "module content"), (False, "", None)],
    ids=["overwrite_module", "keep_existing_module", "module_not_exist"],
)
def test_check_for_existing_module(module_exists, user_input, expected, base_module):
    # Arrange
    with patch("builtins.input", return_value=user_input), patch(
        "pathlib.Path.exists", return_value=module_exists
    ), patch("pathlib.Path.read_text", return_value="module content"):

        # Act
        result = base_module.check_for_existing_module()

    # Assert
    assert result == expected


@pytest.mark.parametrize(
    "existing_module, expected",
    [(None, "new_module"), ("existing_module", "existing_module")],
    ids=["new_module", "existing_module"],
)
def test_get_module(existing_module, expected, base_module):
    # Arrange
    with patch(
        "requests.get",
        return_value=MagicMock(text=base64.b64encode(b"new_module").decode("utf-8")),
    ), patch(
        "base.base_module.BaseModule.check_for_existing_module",
        return_value=existing_module,
    ), patch(
        "pathlib.Path.write_text"
    ) as mock_write_text:

        # Act
        result = base_module.get_module()

    # Assert
    if existing_module is None:
        mock_write_text.assert_called_once_with("new_module", encoding="utf-8")
    assert result == expected


def test_remove_module(base_module):
    # Arrange
    with patch("pathlib.Path.rmdir") as mock_rmdir:

        # Act
        base_module.remove_module()

    # Assert
    mock_rmdir.assert_called_once()


def test_save_module(base_module):
    # Arrange
    module_data = base64.b16encode(b"module content").decode("utf-8")
    with patch("pathlib.Path.write_text") as mock_write_text:

        # Act
        base_module.save_module(module_data)

    # Assert
    mock_write_text.assert_called_once_with("module content", encoding="utf-8")


def test_setup_module(base_module):
    # Arrange
    with patch("subprocess.run") as mock_run:

        # Act
        base_module.setup_module()

    # Assert
    mock_run.assert_called_once_with(
        ["python", "-m", "test_path.setup_test_module"], check=True
    )


def test_update_module(base_module, module_config):
    # Arrange
    with patch.object(base_module, "install_module") as mock_install_module:

        # Act
        base_module.update_module(module_config)

    # Assert
    mock_install_module.assert_called_once_with(module_config)


def test_install_module(base_module, module_config):
    # Arrange
    with patch.object(base_module, "get_module") as mock_get_module, patch.object(
        base_module, "setup_module"
    ) as mock_setup_module, patch("subprocess.run") as mock_run:

        # Act
        base_module.install_module(module_config)

    # Assert
    mock_get_module.assert_called_once()
    mock_setup_module.assert_called_once()
    mock_run.assert_called_once_with(
        ["bash", "test_path/install_test_module.sh"], check=True
    )
