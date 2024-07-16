import pytest
import os
import json
import base64
import requests
import subprocess
from unittest.mock import patch, mock_open, MagicMock
from module_manager import ModuleManager
from data_models import MinerConfig, ModuleConfig, BaseModule


@pytest.fixture
def base_module():
    return MagicMock(spec=BaseModule)


@pytest.fixture
def module_manager(base_module):
    return ModuleManager(base_module)


@pytest.mark.parametrize(
    "config_exists, config_content, expected_result",
    [
        (
            True,
            '{"module1": {"module_name": "module1"}}',
            {"module1": {"module_name": "module1"}},
        ),
        (False, "{}", {}),
    ],
    ids=["config_exists", "config_not_exists"],
)
def test_get_configs(module_manager, config_exists, config_content, expected_result):
    # Arrange
    config_path = "data/instance_data/module_configs.json"
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with patch("builtins.open", mock_open(read_data=config_content)) as mock_file:
        with patch("os.path.exists", return_value=config_exists):
            # Act
            result = module_manager.get_configs()

            # Assert
            assert result == expected_result
            mock_file.assert_called_with(config_path, "r", encoding="utf-8")


@pytest.mark.parametrize(
    "module_configs, expected_modules",
    [
        ({"module1": {"module_name": "module1"}}, {"module1": "module1_module"}),
    ],
    ids=["single_module"],
)
def test_get_module(module_manager, module_configs, expected_modules):
    # Arrange
    module_manager.module_configs = module_configs
    with patch("os.listdir", return_value=["module1"]):
        with patch("importlib.import_module", return_value="module1_module"):
            with patch.object(module_manager, "save_registry"):
                # Act
                result = module_manager.get_module()

                # Assert
                assert result == expected_modules


@pytest.mark.parametrize(
    "module_name, module_path, module_endpoint, module_url, expected_module_name",
    [
        (None, None, None, None, "test_module"),
        ("module1", "path1", "endpoint1", "url1", "module1"),
    ],
    ids=["env_input", "direct_input"],
)
def test_add_module_config(
    module_manager,
    module_name,
    module_path,
    module_endpoint,
    module_url,
    expected_module_name,
):
    # Arrange
    with patch("builtins.input", return_value="test_module"):
        with patch.object(module_manager, "install_module") as mock_install_module:
            # Act
            module_manager.add_module_config(
                module_name, module_path, module_endpoint, module_url
            )

            # Assert
            assert expected_module_name in module_manager.module_configs
            mock_install_module.assert_called_once()


@pytest.mark.parametrize(
    "response_status, response_text, expected_exception",
    [
        (200, base64.b64encode(b"setup_code").decode("utf-8"), None),
        (404, "", requests.RequestException),
    ],
    ids=["successful_request", "failed_request"],
)
def test_request_module(
    module_manager, response_status, response_text, expected_exception
):
    # Arrange
    module_config = ModuleConfig(
        module_name="module1",
        module_path="path1",
        module_endpoint="endpoint1",
        module_url="url1",
    )
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = response_status
        mock_get.return_value.text = response_text
        mock_get.return_value.raise_for_status.side_effect = (
            requests.RequestException if response_status != 200 else None
        )

        # Act
        if expected_exception:
            with pytest.raises(expected_exception):
                module_manager.request_module(module_config)
        else:
            module_manager.request_module(module_config)

        # Assert
        if not expected_exception:
            with open(
                f"modules/{module_config.module_name}/setup_{module_config.module_name}.py",
                "r",
                encoding="utf-8",
            ) as f:
                assert f.read() == "setup_code"


@pytest.mark.parametrize(
    "subprocess_success", [True, False], ids=["success", "failure"]
)
def test_setup_module(module_manager, subprocess_success):
    # Arrange
    module_config = ModuleConfig(
        module_name="module1",
        module_path="path1",
        module_endpoint="endpoint1",
        module_url="url1",
    )
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = (
            subprocess.CalledProcessError(1, "cmd") if not subprocess_success else None
        )

        # Act
        if subprocess_success:
            module_manager.setup_module(module_config)
        else:
            with pytest.raises(subprocess.CalledProcessError):
                module_manager.setup_module(module_config)

        # Assert
        mock_run.assert_called_once_with(
            [
                "python",
                "-m",
                f"modules.{module_config.module_name}.setup_{module_config.module_name}",
            ],
            check=True,
        )


@pytest.mark.parametrize(
    "module_name, expected_active_modules",
    [
        ("module1", {}),
    ],
    ids=["remove_existing_module"],
)
def test_remove_module(module_manager, module_name, expected_active_modules):
    # Arrange
    module_config = ModuleConfig(
        module_name=module_name,
        module_path="path1",
        module_endpoint="endpoint1",
        module_url="url1",
    )
    module_manager.active_modules[module_name] = "module_data"

    # Act
    result = module_manager.remove_module(module_config)

    # Assert
    assert result == expected_active_modules


def test_save_configs(module_manager):
    # Arrange
    module_manager.module_configs = {"module1": {"module_name": "module1"}}
    with patch("builtins.open", mock_open()) as mock_file:
        # Act
        module_manager.save_configs()

        # Assert
        mock_file.assert_called_with(
            "data/instance_data/module_configs.json", "w", encoding="utf-8"
        )
        mock_file().write.assert_called_once_with(
            json.dumps(module_manager.module_configs, indent=4)
        )


def test_save_registry(module_manager):
    # Arrange
    module_manager.modules = {"module1": "module1_module"}
    with patch("builtins.open", mock_open()) as mock_file:
        # Act
        module_manager.save_registry()

        # Assert
        mock_file.assert_called_with("modules/registry.json", "w", encoding="utf-8")
        mock_file().write.assert_called_once_with(
            json.dumps({"module1": "module1_module"}, indent=4)
        )


def test_list_modules(module_manager, capsys):
    # Arrange
    module_manager.modules = {"module1": "module1_module"}

    # Act
    module_manager.list_modules()

    # Assert
    captured = capsys.readouterr()
    assert "Active Modules:\n- module1\n" in captured.out


def test_select_module(module_manager, capsys):
    # Arrange
    module_manager.modules = {"module1": "module1_module"}

    # Act
    module_manager.select_module()

    # Assert
    captured = capsys.readouterr()
    assert "Available Modules:\n1: module1.\n" in captured.out


def test_cli(module_manager):
    # Arrange
    with patch("builtins.input", side_effect=["1", "6"]):
        with patch.object(
            module_manager, "add_module_config"
        ) as mock_add_module_config:
            with patch("builtins.exit", side_effect=SystemExit):
                # Act
                with pytest.raises(SystemExit):
                    module_manager.cli()

                # Assert
                mock_add_module_config.assert_called_once()
