import os
import shutil
import time

from loguru import logger


def recreate_directory(directory_path: str):
    """
    Recreates a directory at the specified path.

    If the directory already exists, it is removed and then recreated.

    Args:
        directory_path (str): The path of the directory to recreate.
    """
    if os.path.exists(directory_path):
        shutil.rmtree(directory_path)
    os.makedirs(directory_path)


def remove_directory(directory_path: str):
    """
    Removes a directory at the specified path if it exists.

    Logs the removal action.

    Args:
        directory_path (str): The path of the directory to remove.
    """
    if os.path.exists(directory_path):
        logger.info("Removing {directory_path}")
        shutil.rmtree(directory_path)


def create_tmp_artefacts_folder(model_name, project_name, version, path):
    timestamp_id: int = int(time.time())
    dest_model_files = f"{timestamp_id}_{project_name}_{model_name}_{version}"
    path_dest = os.path.join(path, dest_model_files)
    recreate_directory(path_dest)
    return path_dest
