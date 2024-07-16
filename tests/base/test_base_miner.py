import pytest
from unittest.mock import MagicMock, patch
from fastapi import FastAPI
from typing import Any
from base.base_miner import BaseMiner
from base.base_module import BaseModule
from base.base_miner import MinerConfig, MinerRequest


class TestBaseMiner(BaseMiner):
    def process(self, miner_request: MinerRequest) -> Any:
        return "processed"


@pytest.fixture
def miner_config():
    return MinerConfig(
        miner_name="test_miner",
        miner_keypath="/path/to/key",
        miner_host="127.0.0.1",
        external_address="http://external.address",
        miner_port=8000,
        stake=100.0,
        netuid=1,
        funding_key="funding_key",
        funding_modifier=10.0,
    )


@pytest.fixture
def base_module():
    return MagicMock(spec=BaseModule)


@pytest.fixture
def base_miner(miner_config, base_module):
    return TestBaseMiner(miner_config, base_module)


@pytest.mark.parametrize(
    "file_exists, file_content, expected",
    [(True, '[{"key": "value"}]', [{"key": "value"}]), (False, "[]", [])],
    ids=["file_exists", "file_not_exists"],
)
def test_load_configs(file_exists, file_content, expected, base_miner):
    # Arrange
    file_path = "modules/miner_configs.json"
    with patch("pathlib.Path.exists", return_value=file_exists):
        with patch("pathlib.Path.read_text", return_value=file_content):
            with patch("pathlib.Path.write_text") as mock_write_text:

                # Act
                result = base_miner._load_configs(file_path)

                # Assert
                assert result == expected
                if not file_exists:
                    mock_write_text.assert_called_once_with("[]", encoding="utf-8")


def test_add_route(base_miner, base_module):
    # Arrange
    app = FastAPI()

    # Act
    base_miner.add_route(base_module, app)

    # Assert
    assert len(app.routes) > 0


def test_prompt_miner_config(monkeypatch):
    # Arrange
    inputs = iter(
        [
            "miner_name",
            "/path/to/key",
            "0.0.0.0",
            "http://external.address",
            "8000",
            "100.0",
            "1",
            "funding_key",
            "10.0",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    # Act
    result = TestBaseMiner._prompt_miner_config()

    # Assert
    assert result.miner_name == "miner_name"
    assert result.miner_keypath == "/path/to/key"
    assert result.miner_host == "0.0.0.0"
    assert result.external_address == "http://external.address"
    assert result.miner_port == 8000
    assert result.stake == 100.0
    assert result.netuid == 1
    assert result.funding_key == "funding_key"
    assert result.funding_modifier == 10.0


@pytest.mark.parametrize(
    "reload, register",
    [(True, True), (False, False)],
    ids=["reload_and_register", "no_reload_no_register"],
)
def test_serve_miner(reload, register, base_miner, miner_config):
    # Arrange
    with patch("uvicorn.run") as mock_run:
        with patch.object(base_miner, "register_miner") as mock_register_miner:

            # Act
            base_miner.serve_miner(miner_config, reload=reload, register=register)

            # Assert
            mock_run.assert_called_once_with(
                "base.api:app",
                host=miner_config.miner_host,
                port=miner_config.miner_port,
                reload=reload,
            )
            if register:
                mock_register_miner.assert_called_once_with(miner_config)


def test_register_miner(base_miner, miner_config):
    # Arrange
    with patch("subprocess.run") as mock_run:

        # Act
        base_miner.register_miner(miner_config)

        # Assert
        mock_run.assert_called_once_with(
            [
                "bash",
                "chains/commune/register_miner.sh",
                "register",
                miner_config.miner_name,
                miner_config.miner_keypath,
                miner_config.miner_host,
                str(miner_config.port),
                str(miner_config.netuid),
                str(miner_config.stake),
                miner_config.funding_key,
                str(miner_config.modifier),
            ],
            check=True,
        )


def test_process(base_miner):
    # Arrange
    miner_request = MagicMock(spec=MinerRequest)

    # Act
    result = base_miner.process(miner_request)

    # Assert
    assert result == "processed"
