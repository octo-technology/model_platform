import hashlib
import os
import re


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


def sanitize_ressource_name(project_name: str) -> str:
    """Nettoie et format le nom pour être valid dans Kubernetes."""
    sanitized_name = re.sub(r"[^a-z0-9-]", "-", project_name.lower())
    sanitized_name = re.sub(r"^-+", "", sanitized_name)  # Supprimer tirets au début
    sanitized_name = re.sub(r"-+$", "", sanitized_name)  # Supprimer tirets à la fin
    # make sure len is < 63 and unique
    sanitized_name = sanitized_name[:56] + "-" + hashlib.shake_256(bytes(sanitized_name, "utf-8")).hexdigest(3)
    return sanitized_name


def sanitize_project_name(project_name: str) -> str:
    """Nettoie et format le nom pour être valid dans Kubernetes."""
    sanitized_name = re.sub(r"[^a-z0-9-]", "-", project_name.lower())
    sanitized_name = re.sub(r"^-+", "", sanitized_name)  # Supprimer tirets au début
    sanitized_name = re.sub(r"-+$", "", sanitized_name)  # Supprimer tirets à la fin
    return sanitized_name


def hash_directory(directory, hash_algo="sha256"):
    hasher = hashlib.new(hash_algo)
    for root, _, files in sorted(os.walk(directory)):
        for file in sorted(files):
            file_path = os.path.join(root, file)

            rel_path = os.path.relpath(file_path, directory).encode()
            hasher.update(rel_path)

            with open(file_path, "rb") as f:
                while chunk := f.read(4096):
                    hasher.update(chunk)

    return hasher.hexdigest()


if __name__ == "__main__":
    print(hash_directory("../tmp/1740239973_test_test_model_2"))
# b97e3ffba719ebbd5c9b125ecd79a3d8436b3e50e28bfd6f9df3d9c9b0dfa895
