from json import load
from os import listdir, makedirs
from os.path import join
from pathlib import Path

import pytest

from file_organizer import (
    DirectoryFormatConfig,
    check_json_extension,
    cli_main,
    move_files,
    reorganize_directory,
    reorganize_directory_from_json,
    reorganize_directory_recursively,
)


def test_check_json_extension():
    assert check_json_extension("file.json")
    assert check_json_extension("file.j2son") is False


@pytest.mark.parametrize("number_of_files", [3])
def test_move_files(default_directory: Path):
    tmp_destination = join(default_directory, "test_out")
    makedirs(tmp_destination)
    move_files(default_directory, tmp_destination, "tmp1", ["file1.txt"])
    assert listdir(join(tmp_destination, "tmp1")) == ["file1.txt"]
    move_files(default_directory, tmp_destination, "tmp2", ["file3.txt"])
    assert listdir(join(tmp_destination, "tmp2")) == ["file3.txt"]
    move_files(default_directory, tmp_destination, "tmp1", ["file2.txt"])
    assert listdir(join(tmp_destination, "tmp1")) == ["file1.txt", "file2.txt"]


def check_subdir_organization(path: str, json_slice: DirectoryFormatConfig) -> None:
    """Helper function

    if current json_slice has a subdir, recurse into sub_dir configuration slice (https://en.wikipedia.org/wiki/Depth-first_search),
    then check current path content, files and directories

    if current json_slice doesn't have sub_dirs check current path content, files only

    Args:
        path (str): path containing the files and subdir specified in the configuration
        json_slice (DirectoryFormatConfig): configuration specifying the directory content
    """
    subdirs = [x for x in json_slice if x != "content"]
    has_subdirs = subdirs != []
    if has_subdirs:
        for subdir, sub_json_slice in json_slice.items():
            if subdir == "content":
                continue
            check_subdir_organization(join(path, subdir), sub_json_slice)
    content_list = []
    if "content" in json_slice:
        content_list += json_slice["content"]
    content_list += subdirs
    assert (
        listdir(path) == content_list
    ), f"subdir format not equal: {path}\nshould be: {listdir(path)}\nwas found: {content_list}"


@pytest.mark.parametrize("number_of_files", [3])
def test_reorganize_directory_recursively(
    default_directory: Path, configuration_slice: tuple[str, DirectoryFormatConfig]
):
    tmp_destination = join(default_directory, "test_out")
    makedirs(tmp_destination)
    relative_destination_path, json_slice = configuration_slice
    reorganize_directory_recursively(
        default_directory, tmp_destination, relative_destination_path, json_slice
    )
    assert listdir(tmp_destination) == [relative_destination_path]
    check_subdir_organization(join(tmp_destination, relative_destination_path), json_slice)


@pytest.mark.parametrize("number_of_files", [6])
def test_reorganize_directory(
    default_directory: Path, default_directory_configuration: DirectoryFormatConfig
):
    tmp_destination = join(default_directory, "test_out")
    makedirs(tmp_destination)
    reorganize_directory(default_directory, tmp_destination, default_directory_configuration, True)
    relative_destination_root_path = list(default_directory_configuration)[0]
    json_slice = default_directory_configuration[relative_destination_root_path]
    assert listdir(tmp_destination) == [relative_destination_root_path]
    check_subdir_organization(join(tmp_destination, relative_destination_root_path), json_slice)


@pytest.mark.parametrize("number_of_files", [6])
def test_reorganize_directory_from_json(directory_and_config: tuple[Path, Path]):
    default_directory, config_path = directory_and_config
    with open(config_path, "r") as config_fin:
        directory_configuration = load(config_fin)
    tmp_destination = join(default_directory, "test_out")
    makedirs(tmp_destination)
    reorganize_directory_from_json(default_directory, tmp_destination, config_path, True)
    relative_destination_root_path = list(directory_configuration)[0]
    json_slice = directory_configuration[relative_destination_root_path]
    assert listdir(tmp_destination) == [relative_destination_root_path]
    check_subdir_organization(join(tmp_destination, relative_destination_root_path), json_slice)


@pytest.mark.parametrize("number_of_files", [6])
def test_cli_main(directory_and_config: tuple[Path, Path]):
    default_directory, config_path = directory_and_config
    with open(config_path, "r") as config_fin:
        directory_configuration = load(config_fin)
    tmp_destination = join(default_directory, "test_out")
    makedirs(tmp_destination)
    cli_main(
        [
            "--root_directory",
            str(default_directory),
            "--target_directory",
            str(tmp_destination),
            "--clean_start",
            str(config_path),
        ]
    )
    relative_destination_root_path = list(directory_configuration)[0]
    json_slice = directory_configuration[relative_destination_root_path]
    assert listdir(tmp_destination) == [relative_destination_root_path]
    check_subdir_organization(join(tmp_destination, relative_destination_root_path), json_slice)
