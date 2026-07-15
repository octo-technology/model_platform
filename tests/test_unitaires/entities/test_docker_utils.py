from unittest.mock import MagicMock, patch

from backend.domain.entities.docker.utils import (
    build_docker_image_from_context_path,
    build_image_from_context,
    ensure_agent_base_image,
)


def _mock_build_process(returncode: int = 0):
    process = MagicMock()
    process.stdout = iter(["Step 1/5 : FROM agent-base:latest\n"])
    process.wait.return_value = None
    process.returncode = returncode
    return process


class TestBuildImageFromContext:
    def test_includes_dockerfile_flag_when_given(self, tmp_path):
        with (
            patch("backend.domain.entities.docker.utils.subprocess.check_output", return_value="24.0.0"),
            patch("backend.domain.entities.docker.utils.get_build_platform", return_value="linux/amd64"),
            patch("backend.domain.entities.docker.utils.subprocess.Popen") as mock_popen,
        ):
            mock_popen.return_value = _mock_build_process(0)
            build_image_from_context(str(tmp_path), "agent-base:latest", dockerfile_path="/some/agent-base.Dockerfile")

        cmd = mock_popen.call_args[0][0]
        assert cmd[:4] == ["docker", "build", "-t", "agent-base:latest"]
        assert "-f" in cmd
        assert cmd[cmd.index("-f") + 1] == "/some/agent-base.Dockerfile"

    def test_omits_dockerfile_flag_by_default(self, tmp_path):
        with (
            patch("backend.domain.entities.docker.utils.subprocess.check_output", return_value="24.0.0"),
            patch("backend.domain.entities.docker.utils.get_build_platform", return_value="linux/amd64"),
            patch("backend.domain.entities.docker.utils.subprocess.Popen") as mock_popen,
        ):
            mock_popen.return_value = _mock_build_process(0)
            build_image_from_context(str(tmp_path), "some-image:latest")

        cmd = mock_popen.call_args[0][0]
        assert "-f" not in cmd


class TestEnsureAgentBaseImage:
    def test_returns_true_without_building_when_already_present(self):
        with (
            patch("backend.domain.entities.docker.utils._local_docker_image_exists", return_value=True),
            patch("backend.domain.entities.docker.utils.build_image_from_context") as mock_build,
        ):
            assert ensure_agent_base_image() is True

        mock_build.assert_not_called()

    def test_builds_and_returns_true_when_missing(self, tmp_path):
        infra_dir = tmp_path / "infrastructure" / "docker"
        infra_dir.mkdir(parents=True)
        dockerfile = infra_dir / "agent-base.Dockerfile"
        dockerfile.write_text("FROM python:3.9-slim\n")

        with (
            patch("backend.domain.entities.docker.utils._local_docker_image_exists", return_value=False),
            patch("backend.domain.entities.docker.utils.PROJECT_DIR", str(tmp_path)),
            patch("backend.domain.entities.docker.utils.build_image_from_context", return_value=1) as mock_build,
        ):
            assert ensure_agent_base_image() is True

        args, kwargs = mock_build.call_args
        assert args[1] == "agent-base:latest"
        assert kwargs["dockerfile_path"] == str(dockerfile)

    def test_falls_back_when_dockerfile_missing(self, tmp_path):
        with (
            patch("backend.domain.entities.docker.utils._local_docker_image_exists", return_value=False),
            patch("backend.domain.entities.docker.utils.PROJECT_DIR", str(tmp_path)),
            patch("backend.domain.entities.docker.utils.build_image_from_context") as mock_build,
        ):
            assert ensure_agent_base_image() is False

        mock_build.assert_not_called()

    def test_falls_back_when_build_fails(self, tmp_path):
        infra_dir = tmp_path / "infrastructure" / "docker"
        infra_dir.mkdir(parents=True)
        (infra_dir / "agent-base.Dockerfile").write_text("FROM python:3.9-slim\n")

        with (
            patch("backend.domain.entities.docker.utils._local_docker_image_exists", return_value=False),
            patch("backend.domain.entities.docker.utils.PROJECT_DIR", str(tmp_path)),
            patch("backend.domain.entities.docker.utils.build_image_from_context", return_value=0),
        ):
            assert ensure_agent_base_image() is False


class TestBuildDockerImageFromContextPathAgentWiring:
    def test_agent_build_uses_base_image_when_available(self, tmp_path):
        with (
            patch("backend.domain.entities.docker.utils.ensure_agent_base_image", return_value=True) as mock_ensure,
            patch("backend.domain.entities.docker.utils.DockerfileTemplate") as mock_template_cls,
            patch("backend.domain.entities.docker.utils.build_image_from_context", return_value=1),
        ):
            mock_template_cls.return_value = MagicMock()
            build_docker_image_from_context_path(str(tmp_path), "img", "proj", "agent", "1", is_agent=True)

        mock_ensure.assert_called_once()
        mock_template_cls.assert_called_once_with(python_version="3.9", use_agent_base_image=True)

    def test_agent_build_falls_back_when_base_image_unavailable(self, tmp_path):
        with (
            patch("backend.domain.entities.docker.utils.ensure_agent_base_image", return_value=False),
            patch("backend.domain.entities.docker.utils.DockerfileTemplate") as mock_template_cls,
            patch("backend.domain.entities.docker.utils.build_image_from_context", return_value=1),
        ):
            mock_template_cls.return_value = MagicMock()
            build_docker_image_from_context_path(str(tmp_path), "img", "proj", "agent", "1", is_agent=True)

        mock_template_cls.assert_called_once_with(python_version="3.9", use_agent_base_image=False)

    def test_model_build_never_checks_base_image(self, tmp_path):
        with (
            patch("backend.domain.entities.docker.utils.ensure_agent_base_image") as mock_ensure,
            patch("backend.domain.entities.docker.utils.DockerfileTemplate") as mock_template_cls,
            patch("backend.domain.entities.docker.utils.build_image_from_context", return_value=1),
        ):
            mock_template_cls.return_value = MagicMock()
            build_docker_image_from_context_path(str(tmp_path), "img", "proj", "model", "1", is_agent=False)

        mock_ensure.assert_not_called()
        mock_template_cls.assert_called_once_with(python_version="3.9", use_agent_base_image=False)
