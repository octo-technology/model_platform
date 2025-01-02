class DockerfileTemplate:
    def __init__(self, base_image: str, env_file: str, workdir: str):
        self.base_image = base_image
        self.env_file = env_file
        self.workdir = workdir

    def generate(self) -> str:
        return f"""
        # Use the specified base image
        FROM {self.base_image}

        # Set the working directory
        WORKDIR {self.workdir}

        # Copy the environment file into the container
        COPY {self.env_file} {self.workdir}/{self.env_file}

        # Create the environment and set up Conda
        RUN conda update -n base -c defaults conda -y && \\
            conda env create -f {self.workdir}/{self.env_file}

        CMD ["/bin/bash"]
        """.strip()
