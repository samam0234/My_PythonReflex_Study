"""Docker daemon 없이 compose 해석·CI 구조·배포 셸 문법을 검사."""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def main():
    compose = yaml.safe_load((ROOT / "deploy/compose.yml").read_text(encoding="utf-8"))
    assert compose["services"]["app"]["expose"] == ["3000"]
    assert "ports" not in compose["services"]["app"]
    workflow = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8"))
    assert workflow["jobs"]["deploy"]["needs"] == "browser"
    assert "DEPLOY_ENABLED" in workflow["jobs"]["deploy"]["if"]
    with tempfile.TemporaryDirectory(prefix="reflex-compose-check-") as tmp:
        runtime = Path(tmp) / "runtime.env"
        runtime.write_text("# no credentials\n", encoding="utf-8")
        compose["services"]["app"]["env_file"] = str(runtime)
        config = Path(tmp) / "compose.yml"
        config.write_text(yaml.safe_dump(compose), encoding="utf-8")
        env = dict(
            os.environ,
            APP_IMAGE="ghcr.io/example/reflex-board:" + "a" * 40,
            APP_DOMAIN="board.example.com",
        )
        if shutil.which("docker"):
            subprocess.run(
                [
                    "docker",
                    "compose",
                    "--project-directory",
                    str(ROOT / "deploy"),
                    "-f",
                    str(config),
                    "config",
                    "--quiet",
                ],
                env=env,
                check=True,
            )
            print("Compose config: PASS")
        else:
            print("Compose CLI: unavailable (YAML structure passed)")
    git_bash = Path("C:/Program Files/Git/bin/bash.exe")
    bash = str(git_bash) if os.name == "nt" and git_bash.exists() else shutil.which("bash")
    if bash:
        for name in ("deploy.sh", "rollback.sh"):
            subprocess.run(
                [bash, "--noprofile", "--norc", "-n", f"deploy/{name}"], cwd=ROOT, check=True
            )
        print("Deployment shell syntax: PASS")
    print("CI gates and YAML: PASS")


if __name__ == "__main__":
    main()
