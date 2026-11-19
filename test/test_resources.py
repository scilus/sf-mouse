import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

RESOURCES = {
    "DEFAULT": (1, 6, 4),
    "SINGLE": (1, 6, 4),
    "LOW": (2, 8, 4),
    "MEDIUM": (4, 8, 8),
    "HIGH": (10, 14, 16),
    "LONG": (1, 6, 20),
    "HIGH_MEMORY": (1, 14, 4),
    "TRACKING": (1, 15.5, 18),
    "RETRY": (1, 6, 4),
    "OVERRIDE": (1, 6, 4),
}


class ResourceConfigurationTests(unittest.TestCase):
    def run_workflow(self, slurm):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            script = root / "resources.nf"
            definitions = []
            calls = []
            for name in RESOURCES:
                label = f"label 'process_{name.lower()}'" if name not in ("DEFAULT", "RETRY", "OVERRIDE") else ""
                retry = 'if [ "${task.attempt}" -eq 1 ]; then exit 104; fi' if name == "RETRY" else ""
                definitions.append(
                    f"""process {name} {{
    {label}
    output:
    stdout
    script:
    \"\"\"
    {retry}
    echo 'RESOURCE {name} ${{task.executor}} ${{task.attempt}} ${{task.cpus}} ${{task.memory.toBytes()}} ${{task.time.toMillis()}}'
    \"\"\"
}}"""
                )
                calls.append(f"    {name}().view()")
            script.write_text("\n".join(definitions) + "\nworkflow {\n" + "\n".join(calls) + "\n}\n")

            config = root / "test.config"
            config.write_text(
                "executor.cpus = 128\n"
                "executor.memory = '512 GB'\n"
                "executor.queueStatInterval = '1 sec'\n"
                "executor.pollInterval = '1 sec'\n"
                + ("executor.name = 'slurm'\nprocess { withName: OVERRIDE { executor = 'local' } }\n" if slurm else "")
            )
            env = {**os.environ, "NXF_ANSI_LOG": "false"}
            if slurm:
                commands = root / "commands"
                commands.mkdir()
                sbatch = commands / "sbatch"
                sbatch.write_text("#!/bin/sh\nbash .command.run >/dev/null 2>&1\nprintf 'Submitted batch job %s\\n' \"$$\"\n")
                sbatch.chmod(0o755)
                squeue = commands / "squeue"
                squeue.write_text("#!/bin/sh\nexit 0\n")
                squeue.chmod(0o755)
                env["PATH"] = str(commands) + os.pathsep + env["PATH"]
            result = subprocess.run(
                ["nextflow", "-C", f"{ROOT / 'conf/base.config'},{config}",
                 "-log", str(root / "nextflow.log"), "run", str(script),
                 "-work-dir", str(root / "work")],
                cwd=root, env=env, capture_output=True, text=True, timeout=180,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            records = {}
            for line in result.stdout.splitlines():
                if line.startswith("RESOURCE "):
                    _, name, executor, attempt, cpus, memory, duration = line.split()
                    records[name] = (executor, int(attempt), int(cpus), int(memory), int(duration))
            self.assertEqual(set(records), set(RESOURCES), result.stdout)
            for name, (cpus, memory, hours) in RESOURCES.items():
                executor = "slurm" if slurm and name != "OVERRIDE" else "local"
                factor = (2 if executor == "slurm" else 1) * (2 if name == "RETRY" else 1)
                self.assertEqual(
                    records[name],
                    (executor, 2 if name == "RETRY" else 1, cpus * factor,
                     int(memory * 1024**3 * factor), hours * 3600 * 1000 * factor),
                    name,
                )

    def test_local_resources(self):
        self.run_workflow(False)

    def test_slurm_resources_and_local_override(self):
        self.run_workflow(True)


if __name__ == "__main__":
    unittest.main()
