# file_organizer

## Local repository setup

First of all run:

```bash
pip install -r requirements_dev.txt
```

To enable repo's custom aliases, run:

```bash
git config include.path "../.custom_aliases/custom_aliases.alias"
```

This alias will add the following custom commands:

- ``` git build ``` to build the executable
- ``` git test ``` to test the project
- ``` git clean-dir ``` to clean project from `__pycache__` directories and other [debries](https://github.com/bittner/pyclean#clean-up-debris)

## How to build the executable

### **Before running the following steps read this [NOTE](https://pyinstaller.org/en/stable/operating-mode.html#what-pyinstaller-does-and-how-it-does-it)**

To generate the executable run:

- ``` pip install -r requirements_dev.txt ```
- ``` pytinstaller.exe --onefile file_organizer.py ``` (or ``` git build ``` if you followed [Local repository setup](#local-repository-setup)

You will find the executable in the **dist** folder.

## Parameters to run cli

```bash
positional arguments:
  directory_configuration_path
                        json file where is defined the format of the installation folder

options:
  -h, --help            show this help message and exit
  --root_directory ROOT_DIRECTORY
                        Optionally select the base directory where all the files reside. Defaults to cwd
  --target_directory TARGET_DIRECTORY
                        Optionally select the base directory where all the files will be reoganized and moved to, the directory MUST exist. Defaults to cwd
  --clean_start         delete root directories defined in the JSON format before copying
```

## Let's see it in action

Let's say you have a bunch of files that you want to organize following this format:

### folder_structure.json

```json
{
    "root_directory":{
        "content":[
            "file1"
        ],
        "sub_directory":{
            "content":[
                "file2",
                "file3"
            ],
            "sub_sub_directory":{
                    "content":[
                    "file4"
                ]
            }
        }
    }
}
```

Also you want to put all the organized files in the directory ` C:\super\secret\directory `

1. Download all the required files
2. create the folder ` C:\super\secret\directory `
3. Run ``` file_organizer.exe --root_directory \path\to\files\dir --target_directory C:\super\secret\directory folder_structure.json ```

Now let's say that some files are now not required and some have been updated, to re-organize the taget directory to contain only the wanted files:

### new_folder_structure.json

```json
{
    "root_directory":{
        "sub_directory":{
            "content":[
                "file1",
                "file3"
            ],
            "sub_sub_directory":{
                    "content":[
                    "file4"
                ]
            }
        }
    }
}
```

1. Download all the updated required files
2. Run ``` file_organizer.exe --clean_start --root_directory \path\to\files\dir --target_directory C:\super\secret\directory new_folder_structure.json ```

**🚫(CARE) if you pass the ```--clean_start``` flag, before running the logic to move all the files ``` file_organizer.exe ``` will delete the directory ``` \path\to\files\dir\root_directory ``` and all of it's content.**
