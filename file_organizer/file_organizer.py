"""
Example:
    Configuration file format (directory_format.json):
    {
        "root_directory":{
            "content":[
                "file1.txt"
            ],
            "intra_directory1":{
                "content":[
                    "file2.txt",
                    "file3.txt"
                ]
            },
            "intra_directory2":{
                "content":[
                    "file4.txt",
                    "file5.txt"
                ]
            }
        }
    }

    from directory structured as follows:
    ├── file_organizer.py
    ├── directory_format.json
    └── project_dir
        ├── file1.txt
        ├── file2.txt
        ├── file3.txt
        ├── file4.txt
        └── file5.txt

    after executing:

    >>> from file_organizer import reorganize_directory
    >>> import json
    >>> with open("directory_format.json", "r") as config_file:
    ...         directory_configuration = load(config_file)
    ...
    >>> reorganize_directory("./project_dir","./project_dir",directory_configuration)

    the structure will be reorganized as follows:

    ├── file_organizer.py
    ├── directory_format.json
    └── project_dir
        └── root_directory
            ├── file1.txt
            ├── intra_directory1
            │   ├── file2.txt
            │   └── file3.txt
            └── intra_directory2
                ├── file4.txt
                └── file5.txt
Cli:
    This module can be used as a cli tool, example usage:
    $ python.exe file_organizer.py --root_directory project_dir directory_format.json

    For more informations:
    $ python.exe file_organizer.py -h

"""
import warnings
from argparse import ArgumentParser, Namespace
from json import JSONDecodeError, load
from os import getcwd, makedirs
from os.path import basename, exists, join, splitext
from shutil import move, rmtree
from sys import argv
from typing import Dict, List, Union, Callable


class FileExtensionError(OSError):
    pass


class JsonContentError(RuntimeError):
    pass


YELLOW: str = "\033[2;33m"
RED: str = "\033[2;31m"
RESET: str = "\033[0m\n"

old_format_warning: Callable = warnings.formatwarning


def custom_warning_formatter(message, category, filename, lineno, line=None):
    """Function to format a warning the standard way. But in yellow"""
    return old_format_warning(f"{YELLOW}{message}{RESET}", category, filename, lineno, line)


# warnings.warn will display as yellow text
warnings.formatwarning = custom_warning_formatter

FilesToMove = List[str]
DirectoryFormatConfig = Dict[str, Union[FilesToMove, "DirectoryFormatConfig"]]


def move_files(
    root_directory: str, target_dir: str, relative_destination_path: str, files_to_move: list[str]
) -> None:
    """Move files in files_to_move into the directory root_path/relative_destination_path

    Args:
        root_directory (str): directory where all files are stored
        target_directory (str): directory where all files will be moved and reogranized
        relative_destination_path (str): destination directory where to copy all the files
        files_to_move (list[str]): files to be moved
    """
    makedirs(join(target_dir, relative_destination_path), exist_ok=True)
    for file in files_to_move:
        try:
            move(join(root_directory, file), join(target_dir, relative_destination_path, file))
        except FileNotFoundError:
            warnings.warn(
                f"tried to move file {join(root_directory, file)} but wasn't found, skipping."
            )


def reorganize_directory_recursively(
    root_directory: str, target_dir: str, relative_destination_path: str, json_slice: dict
) -> None:
    """Move all files to be moved to current directory (if any), then recurse the operation to all subdirectories

    Args:
        root_directory (str): directory where all files are stored
        target_directory (str): directory where all files will be moved and reogranized
        relative_destination_path (str): current position in fs relative to root_directory
        json_slice (dict): slice of interest contained in configuration file
    """
    files_to_move: list[str] = []
    try:
        files_to_move = json_slice["content"]
    except KeyError:
        # key files not found, this is a directory containing only directories
        pass
    move_files(root_directory, target_dir, relative_destination_path, files_to_move)
    for dir_name, dir_content in json_slice.items():
        if dir_name == "content":  # ignore content key
            continue
        reorganize_directory_recursively(
            root_directory, target_dir, join(relative_destination_path, dir_name), dir_content
        )


def reorganize_directory(
    root_directory: str,
    target_dir: str,
    directory_configuration: DirectoryFormatConfig,
    clean_directories: bool,
) -> None:
    """Given a root_directory and the wanted directory format as a JSON dict,
    reorganizes all the files as specified in directory_configuration

    Args:
        root_directory (str): directory containing all the files to be reogranized
        target_directory (str): directory where all files will be moved and reogranized
        directory_configuration (DirectoryFormatConfig): JSON where is specified how the files will be reorganized
        clean_directories (bool): delete root directories(keys) specified in directory_configuration

    Raises:
        FileNotFoundError: if root_directory file doesn't exist
        FileNotFoundError: if target_dir file doesn't exist
    """
    if not exists(root_directory):
        raise FileNotFoundError(f"specified root_directory doesn't exist: {root_directory}")
    if not exists(target_dir):
        raise FileNotFoundError(f"specified target_dir doesn't exist: {target_dir}")

    for root_key in directory_configuration:
        if clean_directories:
            rmtree(join(target_dir, root_key), ignore_errors=True)
        reorganize_directory_recursively(
            root_directory, target_dir, root_key, directory_configuration[root_key]
        )


def check_json_extension(path: str) -> bool:
    """Check if the file has .json extension

    Args:
        path (str): path to the file

    Returns:
        bool: True if has .json extension, else False
    """
    _, file_ext = splitext(path)
    if file_ext == ".json":
        return True
    return False


def reorganize_directory_from_json(
    root_directory: str, target_dir: str, directory_configuration_path: str, clean_directories: bool
) -> None:
    """Given a root_directory and the wanted directory format as a JSON dict, reorganizes all the files as specified in directory_configuration

    Args:
        root_directory (str): directory containing all the files to be reogranized
        target_directory (str): directory where all files will be moved and reogranized
        directory_configuration_path (str): path to JSON file where is specified how the files will be reorganized
        clean_directories (bool): delete root directories(keys) specified in directory_configuration

    Raises:
        FileNotFoundError: if root_directory file doesn't exist
        FileNotFoundError: if target_dir file doesn't exist
        FileNotFoundError: directory_configuration_path doesn't exist
        FileExtensionError: directory_configuration_path has no .json extension
        JSONDecodeError: parsing json file failed
    """
    if not check_json_extension(directory_configuration_path):
        raise FileExtensionError(
            f"directory_configuration {directory_configuration_path} must have .json extension"
        )
    if not exists(directory_configuration_path):
        raise FileNotFoundError("directory_configuration_path file doesn't exist")

    directory_configuration: dict = {}
    try:
        with open(directory_configuration_path, "r", encoding="utf-8") as config_file:
            directory_configuration = load(config_file)
    except JSONDecodeError as err:
        raise JsonContentError("directory_configuration_path file content is not a JSON") from err
    reorganize_directory(root_directory, target_dir, directory_configuration, clean_directories)


def cli_main(args: list[str]):
    """main cli endpoint, parse the arguments passed by the user then execute reorganize_directory_from_json

    Args:
        args (list[str]): user arguments (example argv[1:])
    """
    executable_name = basename(__file__)
    executable_name, _ = splitext(executable_name)
    parser = ArgumentParser(
        executable_name,
        description="Reorganize files to follow the format defined in a JSON file",
    )

    # adding cli arguments

    ## position arguments
    parser.add_argument(
        "directory_configuration_path",
        help="json file where is defined the format of the installation folder",
    )

    ## optional flags
    parser.add_argument(
        "--root_directory",
        default=getcwd(),
        help="Optionally select the base directory where all the files reside. Defaults to cwd",
    )
    parser.add_argument(
        "--target_directory",
        default=getcwd(),
        help="Optionally select the base directory where all the files will be reoganized and moved to, the directory MUST exist. Defaults to cwd",
    )
    parser.add_argument(
        "--clean_start",
        default=False,
        action="store_true",
        help="delete root directories defined in the JSON format before copying",
    )

    # extracting cli arguments and checking validity
    parsed_args: Namespace = parser.parse_args(args)

    # FLAGS

    ## --root_directory
    root_directory: str = parsed_args.root_directory

    ## --target_directory
    target_directory: str = parsed_args.target_directory

    ## --clean_start
    clean_start: bool = parsed_args.clean_start

    # POSITIONAL ARGUMENTS

    ## directory_configuration_path
    directory_configuration_path: str = parsed_args.directory_configuration_path
    try:
        reorganize_directory_from_json(
            root_directory,
            target_directory,
            directory_configuration_path,
            clean_start,
        )
    except (FileNotFoundError, FileExtensionError, JsonContentError) as err:
        parser.error(f"{RED}{err}{RESET}")


if __name__ == "__main__":
    cli_main(argv[1:])
