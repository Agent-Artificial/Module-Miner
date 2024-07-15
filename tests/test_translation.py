import pytest
from pathlib import Path
import torch
from unittest.mock import patch, MagicMock

from modules.translation.translation_module import SeamlessTranslator  # Replace 'your_module' with the actual module name
from modules.translation.data_models import TARGET_LANGUAGES, TASK_STRINGS


@pytest.fixture
def seamless_translator():
    return SeamlessTranslator()


def test_seamless_translator_init(seamless_translator):
    assert seamless_translator.model_name == "seamlessM4T_v2_large"
    assert seamless_translator.vocoder_name == "vocoder_v2"
    assert isinstance(seamless_translator.translator, MagicMock)  # We'll mock the Translator
    assert seamless_translator.task_strings == TASK_STRINGS
    assert seamless_translator.target_languages == TARGET_LANGUAGES


@patch('modules.transltion.translation.SeamlessTranslator')
@patch('torchaudio.save')
def test_seamless_translator_process(mock_torchaudio_save, mock_translator, seamless_translator, tmp_path):
    # Create a mock input file
    input_file = tmp_path / "test_input.wav"
    input_file.touch()

    # Mock the translator's predict method
    mock_translator_instance = mock_translator.return_value
    mock_translator_instance.predict.return_value = (["Translated text"], MagicMock(audio_wavs=[[torch.tensor([0.1, 0.2, 0.3])]], sample_rate=16000))

    # Call the process method
    result = seamless_translator.process(
        in_file=str(input_file),
        task_string="speech2text",
        source_language="English",
        target_lanaguages=["French"]
    )

    # Assertions
    assert result is not None
    assert len(result) == 2
    assert result[0] == "Translated text"
    assert isinstance(result[1], Path)

    # Check if the predict method was called with correct arguments
    mock_translator_instance.predict.assert_called_once_with(
        input=str(input_file),
        task_str="s2tt",
        src_lang="eng",
        tgt_lang="fra"
    )

    # Check if torchaudio.save was called
    mock_torchaudio_save.assert_called_once()


def test_seamless_translator_process_file_not_found(seamless_translator):
    with pytest.raises(FileNotFoundError):
        seamless_translator.process(
            in_file="non_existent_file.wav",
            task_string="speech2text",
            source_language="English",
            target_lanaguages=["French"]
        )


def test_seamless_translator_process_invalid_task_string(seamless_translator, tmp_path):
    input_file = tmp_path / "test_input.wav"
    input_file.touch()

    with pytest.raises(ValueError, match="Invalid task string"):
        seamless_translator.process(
            in_file=str(input_file),
            task_string="invalid_task",
            source_language="English",
            target_lanaguages=["French"]
        )


def test_seamless_translator_process_invalid_target_language(seamless_translator, tmp_path):
    input_file = tmp_path / "test_input.wav"
    input_file.touch()

    with pytest.raises(ValueError, match="Invalid target language"):
        seamless_translator.process(
            in_file=str(input_file),
            task_string="speech2text",
            source_language="English",
            target_lanaguages=["InvalidLanguage"]
        )