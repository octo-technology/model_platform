from backend.domain.entities.docker.dockerfile_template import AGENT_BASE_IMAGE, DockerfileTemplate


class TestDockerfileTemplate:
    def test_default_uses_plain_python_image(self, tmp_path):
        template = DockerfileTemplate(python_version="3.9")
        template.generate_dockerfile(str(tmp_path), "my-image", "proj", "model", "1")

        content = (tmp_path / "Dockerfile").read_text()
        assert "FROM python:3.9-slim" in content
        assert f"FROM {AGENT_BASE_IMAGE}" not in content
        assert "apt-get install" in content

    def test_agent_base_image_used_when_flagged(self, tmp_path):
        template = DockerfileTemplate(python_version="3.9", use_agent_base_image=True)
        template.generate_dockerfile(str(tmp_path), "my-agent-image", "proj", "agent", "1")

        content = (tmp_path / "Dockerfile").read_text()
        assert f"FROM {AGENT_BASE_IMAGE}" in content
        assert "FROM python:3.9-slim" not in content
        # System packages are already baked into the base image, so no apt-get needed here.
        assert "apt-get install" not in content

    def test_agent_base_image_still_recreates_venv_for_the_agents_pinned_python(self, tmp_path):
        # Each agent's conda.yaml can pin a different Python minor version than the base image
        # was built with, so the venv must always be recreated (see comment in the template).
        template = DockerfileTemplate(python_version="3.9", use_agent_base_image=True)
        template.generate_dockerfile(str(tmp_path), "my-agent-image", "proj", "agent", "1")

        content = (tmp_path / "Dockerfile").read_text()
        assert "uv venv --clear" in content
