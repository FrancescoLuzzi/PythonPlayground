from json import dumps
from pathlib import Path
from shutil import rmtree

import pytest

from file_organizer import DirectoryFormatConfig

DEFAULT_FILE_CONTENT = ""


@pytest.fixture
def default_directory(tmp_path: Path, number_of_files: int) -> Path:
    for i in range(1, number_of_files + 1):
        tmp_f = tmp_path / f"file{i}.txt"
        tmp_f.write_text(DEFAULT_FILE_CONTENT)
    yield tmp_path
    rmtree(tmp_path)


@pytest.fixture
def default_directory_configuration() -> dict:
    return {
        "root_directory": {
            "sub_dir1": {"content": ["file1.txt", "file2.txt", "file3.txt"]},
            "sub_dir2": {
                "content": ["file4.txt", "file5.txt"],
                "sub_sub_dir1": {"content": ["file6.txt"]},
            },
        }
    }


@pytest.fixture
def configuration_slice() -> tuple[str, DirectoryFormatConfig]:
    return (
        "root_directory",
        {
            "content": ["file1.txt", "file2.txt"],
            "sub_dir": {"content": ["file3.txt"]},
        },
    )


@pytest.fixture
def directory_and_config(
    default_directory: Path, default_directory_configuration: dict
) -> tuple[Path, Path]:
    config_file = default_directory / "config.json"
    config_file.write_text(dumps(default_directory_configuration))
    yield default_directory, config_file
