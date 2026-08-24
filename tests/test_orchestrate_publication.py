import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_orchestrate_scenarios import (
    active_work_snapshot,
    bootstrap_snapshot,
    checkpoint,
    delivered_work_snapshot,
    durable_snapshot,
    local_orchestration_contract,
    prepared_snapshot,
    run_scenario,
)


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_public_release.py"
COVERAGE = ROOT / "tests" / "orchestrate_prd_coverage.json"


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_public_release", VALIDATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError("publication validator is unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CompleteReleaseScenarios(unittest.TestCase):
    def test_every_release_area_runs_through_the_public_orchestration_seam(
        self,
    ) -> None:
        recovery = durable_snapshot(checkpoint())

        scheduling = prepared_snapshot()
        scheduling["programme"]["approved_order"] = [43, 42]
        scheduling["tickets"].append(
            {
                "issue": 43,
                "title": "Release candidate",
                "state": "ready",
                "blocked_by": [],
            }
        )

        delegation = prepared_snapshot(intent="research")

        monitoring = active_work_snapshot(
            {
                "id": "task-8",
                "issue": 8,
                "state": "running",
                "resumable": True,
                "native_wait": {"after_cursor": "event-8"},
                "updated_at": "2026-08-24T10:05:00Z",
            }
        )
        monitoring["observed_at"] = "2026-08-24T10:06:00Z"

        merge = delivered_work_snapshot()

        approvals = prepared_snapshot()
        approvals["tickets"][0]["gates"] = {
            "credentials": {"scope": {"purpose": "release"}}
        }

        capability = prepared_snapshot(intent="coordinate")
        capability["stewardship"] = {
            "capability": {
                "category": "security_scanning",
                "reason": "protect public releases",
                "approved": False,
            }
        }

        research = prepared_snapshot(intent="coordinate")
        research["stewardship"] = {
            "research": {
                "question": "Has the release baseline changed?",
                "roadmap_decision": "release-policy",
                "urgency": "default",
                "approved": False,
            }
        }

        bootstrap = bootstrap_snapshot()

        migration = bootstrap_snapshot()
        migration["bootstrap"]["conventions"]["programme_discovery"] = {
            "satisfies_contract": True
        }
        migration["bootstrap"]["agent_instructions"] = {
            "discovers_contract": True
        }
        migration["bootstrap"]["local_contract"] = (
            local_orchestration_contract()
        )
        migration["bootstrap"]["capability_gaps"] = []
        migration["bootstrap"]["policy"] = {
            "published_version": 2,
            "adopted_version": 1,
            "change_ids": ["public-release-hardening"],
        }

        cases = {
            "recovery": (recovery, "recover"),
            "scheduling": (scheduling, "delegate"),
            "delegation": (delegation, "delegate"),
            "monitoring": (monitoring, "watch"),
            "merge": (merge, "merge"),
            "approvals": (approvals, "stop"),
            "capabilities": (capability, "propose-capability"),
            "research": (research, "record-research-radar"),
            "bootstrap": (bootstrap, "bootstrap-audit"),
            "migrations": (migration, "bootstrap-audit"),
        }

        outcomes = {}
        for area, (snapshot, expected_decision) in cases.items():
            with self.subTest(area=area):
                outcome = run_scenario(snapshot)
                outcomes[area] = outcome
                self.assertEqual(outcome["decision"], expected_decision)
                self.assertFalse(outcome["root_mutation_permitted"])

        self.assertEqual(
            outcomes["migrations"]["policy"]["status"],
            "migration-proposed",
        )


class PublicReleaseChecks(unittest.TestCase):
    def test_repository_publication_gate_passes(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(VALIDATOR),
                "--root",
                str(ROOT),
                "--coverage",
                str(COVERAGE),
            ],
            capture_output=True,
            check=True,
            text=True,
        )
        report = json.loads(completed.stdout)

        self.assertEqual(
            report["skills"], ["manage-public-presence", "orchestrate"]
        )
        self.assertEqual(report["installable_names"], report["skills"])
        self.assertEqual(report["prd_user_stories"], list(range(1, 76)))
        self.assertEqual(report["violations"], [])

    def test_static_gate_rejects_each_sensitive_content_class(self) -> None:
        validator = load_validator()
        unsafe_samples = {
            "credential": "api_key = " + "sk" + "-release-secret-value",
            "bearer-credential": (
                "Authorization: Bearer " + "gh" + "p_releaseSecret123"
            ),
            "slack-credential": (
                "xox" + "b-123456789012-releaseSecretValue"
            ),
            "google-credential": (
                "AI" + "zaSyReleaseSecretValue1234567890"
            ),
            "npm-credential": "np" + "m_releaseSecretValue1234567890",
            "github-fine-grained-credential": (
                "github_" + "pat_releaseSecretValue1234567890"
            ),
            "jwt-credential": (
                "eyJhbGciOiJIUzI1NiJ9."
                + "eyJzdWIiOiIxMjMifQ."
                + "releaseSig123"
            ),
            "generic-secret": "AWS_SECRET_ACCESS_KEY=releaseSecretValue123",
            "private-identifier": "task_id: 123e4567-e89b-12d3-a456-426614174000",
            "private-email": "owner@example.test",
            "internal-url": "https://release-service.internal/status",
            "private-network": "http://172.20.1.4/status",
            "loopback": "http://[::1]/status",
            "private-ipv6": "http://[fd00::42]/status",
            "corp-host": "https://release.corp/status",
            "single-label-host": "https://intranet/status",
            "copied-provider-response": 'provider_response = {"private": true}',
            "copied-provider-output": '{"request_id":"req_private"}',
            "copied-provider-object": (
                '{"id":"evt_private","object":"event",'
                '"data":{"account":"acct_private"}}'
            ),
            "project-specific": "Apply this only to Quasar releases.",
        }

        for expected_rule, sample in unsafe_samples.items():
            with self.subTest(rule=expected_rule):
                violations = validator.scan_text(
                    Path("skills/orchestrate/SKILL.md"), sample
                )
                normalized_rule = {
                    "bearer-credential": "credential",
                    "slack-credential": "credential",
                    "google-credential": "credential",
                    "npm-credential": "credential",
                    "github-fine-grained-credential": "credential",
                    "jwt-credential": "credential",
                    "generic-secret": "credential",
                    "private-email": "private-identifier",
                    "private-network": "internal-url",
                    "loopback": "internal-url",
                    "private-ipv6": "internal-url",
                    "corp-host": "internal-url",
                    "single-label-host": "internal-url",
                    "copied-provider-output": "copied-provider-response",
                    "copied-provider-object": "copied-provider-response",
                }.get(expected_rule, expected_rule)
                self.assertIn(
                    normalized_rule,
                    {item["rule"] for item in violations},
                )

    def test_private_identifiers_include_uuid7_and_windows_user_paths(
        self,
    ) -> None:
        validator = load_validator()
        private_identifiers = (
            "task_id: 01890f4e-e590-7cc3-98c4-dc0c0c07398f",
            r"C:\Users\release-owner\AppData\Local\orchestrate",
            "D:/Users/release-owner/.config/orchestrate",
            r"\\workstation\Users\release-owner\private\orchestrate",
            r"path=C:\Users\release-owner\private\orchestrate",
            r"(C:\Users\release-owner\private\orchestrate)",
            r"<C:\Users\release-owner\private\orchestrate>",
            r"\\?\C:\Users\release-owner\private\orchestrate",
            r"\\server\C$\Users\release-owner\private\orchestrate",
            r"\\server\share\Users\release-owner\private\orchestrate",
            "file://server/share/Users/release-owner/private/orchestrate",
            "smb://server/share/Users/release-owner/private/orchestrate",
            "file:///Users/release-owner/private/orchestrate",
            "file:///home/release-owner/private/orchestrate",
            "//server/Users/release-owner/private/orchestrate",
            r'json: "C:\\Users\\release-owner\\private\\orchestrate"',
            r"\\?\UNC\server\share\Users\release-owner\private",
            r"C:\DOCUME~1\release-owner\private",
            r"C:\DOCUME~2\release-owner\private",
            "/mnt/c/Users/release-owner/private/orchestrate",
            "/c/Users/release-owner/private/orchestrate",
            "/cygdrive/c/Users/release-owner/private/orchestrate",
            "path=/home/release-owner/private/orchestrate",
            "path=/Users/release-owner/private/orchestrate",
            "(/home/release-owner/private/orchestrate)",
            "file:/mnt/c/Users/release-owner/private/orchestrate",
            "task_01890f4e-e590-7cc3-98c4-dc0c0c07398f_private",
        )

        for private_identifier in private_identifiers:
            with self.subTest(private_identifier=private_identifier):
                violations = validator.scan_text(
                    Path("skills/orchestrate/SKILL.md"),
                    private_identifier,
                )
                self.assertIn(
                    "private-identifier",
                    {item["rule"] for item in violations},
                )

    def test_orchestrate_rejects_bundled_provider_commands(self) -> None:
        validator = load_validator()

        violations = validator.scan_text(
            Path("skills/orchestrate/scripts/example.py"),
            'command = "gh issue view 42"',
        )

        self.assertIn(
            "bundled-provider-integration",
            {item["rule"] for item in violations},
        )

        for provider_code in (
            "gh release create v1.0.0",
            "nebula-cloud release publish v1.0.0",
            "Before release:\ngh release create v1.0.0\nThen verify.",
            "- gh release create v1.0.0",
            "run: gh release create v1.0.0",
            "run: gcloud release publish",
            "run: vercel deploy",
            "run: nebula-cloud publish",
            "run: vercel deploy --prod",
            "run: gh release create v1.0.0 --generate-notes",
            'run: gh release create v1 --notes "release notes"',
            "run: gh release create v1 | tee output.txt",
            "release:\n\tgh release create v1.0.0",
            "gcloud release publish",
            "acme deploy to production",
            'acme deploy "production release"',
            "TARGET=prod acme deploy",
            "target=prod acme deploy",
            "gh release create v1;",
            '{"command":"gh release create v1"}',
            '{"command":"gh release create v1","timeout":30}',
            '{"argv":["gh","release","create"],"timeout":30}',
            '{"executable":"gh","args":["release","create"]}',
            'command = ["gh", "release", "create"]',
            "command: gh release create v1",
            "script: gh release create v1",
            "> gh release create v1",
            "1. gh release create v1",
            'command = "gh release create v1.0.0"',
            'command = "nebula-cloud release publish v1.0.0"',
            'command = "gcloud release publish"',
            'execute_command(["nebula-cloud", "release", "publish"])',
            "os.execvp('gh', ['gh', 'release', 'create', 'v1.0.0'])",
            "execFile('nebula-cloud', ['release', 'publish'])",
            'subprocess.run(["gcloud", "release", "publish"])',
            'runner.run(["nebula", "publish"])',
            'invoke(["nebula", "publish"])',
            'if ready: subprocess.run(["gcloud", "deploy"])',
            'wrapper(subprocess.run(["acme", "deploy"]))',
            'calls = [runner.run(["acme", "deploy"])]',
            'subprocess.check_call(["gh", "release", "create"])',
            'subprocess.check_output(["gh", "release", "create"])',
            'subprocess.getoutput("gh release create")',
            'os.posix_spawn("gh", ["gh", "release"])',
            'import subprocess as sp; sp.check_call(["gh", "release"])',
            'wrapper(run(["acme", "deploy"]))',
            'subprocess.run(args=["gh", "release", "create"])',
            'subprocess.run(("gh", "release", "create"))',
            'subprocess.run(f"gh release {version}", shell=True)',
            'subprocess.run(b"gh release")',
            'os.execvp(file="gh", args=["gh", "release"])',
            'subprocess.Popen(args_value, executable="gh")',
            'subprocess.Popen(get_args(), executable="gh")',
            'subprocess.Popen(args=get_args(), executable="gh")',
            'subprocess.Popen(\n    get_args(),\n    executable="gh",\n)',
            'os.execvp(\n    file="gh",\n    args=["gh", "release"],\n)',
            'subprocess.run(\n    ["gh", "release", "create"]\n)',
            "monitor deploy",
            "Run `monitor deploy` after approval.",
            "Run `route publish production` after approval.",
            "```bash\nunknown-provider release publish v1.0.0\n```",
            "Run `another-provider deploy production` after approval.",
            "Run `gcloud release publish` after approval.",
            "./nebula release publish",
            "@scope/cloud release publish",
            "import github",
            'url = "https://api.github.com/repos/example/release"',
            'command = "curl https://api.github.com/repos/example/release"',
        ):
            with self.subTest(provider_code=provider_code):
                violations = validator.scan_text(
                    Path("skills/orchestrate/scripts/example.py"),
                    provider_code,
                )
                self.assertIn(
                    "bundled-provider-integration",
                    {item["rule"] for item in violations},
                )

    def test_orchestrate_rejects_indirect_execution_implementation(
        self,
    ) -> None:
        validator = load_validator()
        source = (
            "import subprocess\n"
            'args = ["gh", "release", "create", "v1"]\n'
            "subprocess.run(args)\n"
        )

        violations = validator.scan_text(
            Path("skills/orchestrate/scripts/example.py"),
            source,
        )

        self.assertIn(
            "bundled-provider-integration",
            {item["rule"] for item in violations},
        )

    def test_orchestrate_rejects_structural_command_gate_bypasses(self) -> None:
        validator = load_validator()
        unsafe_samples = (
            (
                Path("skills/orchestrate/scripts/example.py"),
                "import nebula_sdk\nnebula_sdk.publish(\"release\")\n",
            ),
            (
                Path("skills/orchestrate/scripts/example.py"),
                'Client().release.create("v1")\n',
            ),
            (
                Path("skills/orchestrate/scripts/example.py"),
                'client = Client()\nclient.publish("release")\n',
            ),
            (
                Path("skills/orchestrate/scripts/example.py"),
                "from . import nebula_sdk\n"
                'nebula_sdk.publish("release")\n',
            ),
            (
                Path("skills/orchestrate/scripts/example.py"),
                "client = nebula_sdk.Client()\n"
                'client.publish("release")\n',
            ),
            (
                Path("skills/orchestrate/scripts/example.py"),
                "client = make_client()\n"
                'client.publish("release")\n',
            ),
            (
                Path("skills/orchestrate/scripts/example.py"),
                'import subprocess\ngetattr(subprocess, "run")'
                '(["gh", "release", "create"])\n',
            ),
            (
                Path("skills/orchestrate/scripts/example.py"),
                'import subprocess\nrunner = subprocess.run\n'
                'args = ["gh", "release", "create"]\nrunner(args)\n',
            ),
            (
                Path("skills/orchestrate/scripts/example.py"),
                'import subprocess\nsubprocess.run('
                '"python scripts/trace.py && gh release create", shell=True)\n',
            ),
            (
                Path("skills/orchestrate/scripts/example.py"),
                "import subprocess\n"
                "subprocess.getstatusoutput(command)\n",
            ),
            (
                Path("skills/orchestrate/scripts/example.py"),
                "import os\nos.startfile(\"gh.exe\")\n",
            ),
            (
                Path("skills/orchestrate/scripts/example.py"),
                "import subprocess\n"
                "getattr(subprocess, operation)(args)\n",
            ),
            (
                Path("skills/orchestrate/scripts/example.py"),
                '__import__("subprocess").run(args)\n',
            ),
            (
                Path("skills/orchestrate/scripts/example.py"),
                "import subprocess\n"
                "runner = getattr(subprocess, operation)\nrunner(args)\n",
            ),
            (
                Path("skills/orchestrate/scripts/example.py"),
                "loader = __import__\nmodule = loader(\"subprocess\")\n"
                "module.run(args)\n",
            ),
            (
                Path("skills/orchestrate/scripts/example.py"),
                "lookup = getattr\n"
                "runner = lookup(subprocess, operation)\nrunner(args)\n",
            ),
            (
                Path("skills/orchestrate/scripts/example.py"),
                "loader = (__import__,)[0]\n"
                'module = loader("subprocess")\nmodule.run(args)\n',
            ),
            (
                Path("skills/orchestrate/scripts/example.py"),
                'mapping = {"load": __import__}\n'
                'module = mapping["load"]("subprocess")\nmodule.run(args)\n',
            ),
            (
                Path("skills/orchestrate/scripts/example.py"),
                '(loader := __import__)("subprocess").run(args)\n',
            ),
            (
                Path("skills/orchestrate/scripts/example.py"),
                "lookup = (getattr,)[0]\n"
                "runner = lookup(subprocess, operation)\nrunner(args)\n",
            ),
            (
                Path("skills/orchestrate/scripts/example.py"),
                "loader = __builtins__.__import__\n"
                'module = loader("subprocess")\nmodule.run(args)\n',
            ),
            (
                Path("skills/orchestrate/scripts/example.py"),
                "import subprocess\nsp2 = subprocess\nsp2.run(args)\n",
            ),
            (
                Path("skills/orchestrate/scripts/example.py"),
                "api = make_client()\napi.publish(\"release\")\n",
            ),
            (
                Path("skills/orchestrate/scripts/example.py"),
                'loader = __builtins__.__dict__["__import__"]\n'
                'module = loader("subprocess")\nmodule.run(args)\n',
            ),
            (
                Path("skills/orchestrate/scripts/example.py"),
                "import subprocess\nsp2 = (subprocess,)[0]\nsp2.run(args)\n",
            ),
            (
                Path("skills/orchestrate/scripts/example.py"),
                "import subprocess\n(sp2,) = (subprocess,)\nsp2.run(args)\n",
            ),
            (
                Path("skills/orchestrate/scripts/example.py"),
                'loader = globals()["__builtins__"].__dict__["__import__"]\n'
                'module = loader("subprocess")\nmodule.run(args)\n',
            ),
            (
                Path("skills/orchestrate/scripts/example.py"),
                'import sys\nsp = sys.modules["subprocess"]\nsp.run(args)\n',
            ),
            (
                Path("skills/orchestrate/scripts/example.py"),
                'import sys\nsys.modules["os"].startfile("gh.exe")\n',
            ),
            (
                Path("skills/orchestrate/scripts/example.py"),
                'from sys import modules\n'
                'modules["os"].startfile("gh.exe")\n',
            ),
            (
                Path("skills/orchestrate/scripts/example.py"),
                'from sys import modules as registry\n'
                'registry["subprocess"].run(args)\n',
            ),
            (
                Path("skills/orchestrate/scripts/example.py"),
                "from subprocess import *\nrun(args)\n",
            ),
            (
                Path("skills/orchestrate/scripts/example.py"),
                "from subprocess import *\nPopen(args)\n",
            ),
            (
                Path("skills/orchestrate/scripts/example.py"),
                "import subprocess\nrunners = [subprocess.run]\n"
                "runners[0](args)\n",
            ),
            (
                Path("skills/orchestrate/scripts/example.py"),
                "import subprocess\nrunner = (subprocess.run,)[0]\n"
                "runner(args)\n",
            ),
            (
                Path("skills/orchestrate/scripts/example.py"),
                "from subprocess import run\nrunners = [run]\n"
                "runners[0](args)\n",
            ),
            (
                Path("skills/orchestrate/scripts/example.py"),
                "command = build_provider_command()\ninvoke(command)\n",
            ),
            (
                Path("skills/orchestrate/scripts/example.py"),
                'command = f"gh release {version}"\ninvoke(command)\n',
            ),
            (
                Path("skills/orchestrate/scripts/example.py"),
                'payload = {"command": build_provider_command()}\n'
                "invoke(payload)\n",
            ),
            (
                Path("skills/orchestrate/scripts/example.py"),
                'os.startfile("gh.exe")\n',
            ),
            (
                Path("skills/orchestrate/SKILL.md"),
                "```bash\npython scripts/trace.py && gh release create\n```",
            ),
            (
                Path("skills/orchestrate/SKILL.md"),
                "Run `unknown-provider release publish v1` after approval.",
            ),
            (
                Path("skills/orchestrate/references/command.yaml"),
                "integration:\n  executable: gh\n  args:\n"
                "    - release\n    - create\n",
            ),
            (
                Path("skills/orchestrate/references/command.yaml"),
                "integration:\n  executable: gh\n",
            ),
            (
                Path("skills/orchestrate/references/command.json"),
                '{"executable": "gh"}\n',
            ),
            (
                Path("skills/orchestrate/references/command.json"),
                '{"executable": "gh", "args": "release create"}\n',
            ),
            (
                Path("skills/orchestrate/SKILL.md"),
                "```powershell\ngh release create v1\n```",
            ),
            (
                Path("skills/orchestrate/SKILL.md"),
                "```zsh\nnebula publish release\n```",
            ),
            (
                Path("skills/orchestrate/SKILL.md"),
                "```python\nimport nebula_sdk\n"
                'nebula_sdk.publish("release")\n```',
            ),
            (
                Path("skills/orchestrate/SKILL.md"),
                "~~~python\nimport nebula_sdk\n"
                'nebula_sdk.publish("release")\n~~~',
            ),
            (
                Path("skills/orchestrate/SKILL.md"),
                "``` python\nimport nebula_sdk\n"
                'nebula_sdk.publish("release")\n```',
            ),
            (
                Path("skills/orchestrate/SKILL.md"),
                "```{bash}\ngh release create v1\n```",
            ),
            (
                Path("skills/orchestrate/SKILL.md"),
                "```bash title=\"release\"\n"
                "gh release create v1\n```",
            ),
            (
                Path("skills/orchestrate/SKILL.md"),
                "    gh release create v1\n",
            ),
            (
                Path("skills/orchestrate/SKILL.md"),
                "> ```bash\n> gh release create v1\n> ```",
            ),
            (
                Path("skills/orchestrate/SKILL.md"),
                "- ```bash\n  gh release create v1\n  ```",
            ),
            (
                Path("skills/orchestrate/SKILL.md"),
                "> $ gh release create v1\n",
            ),
            (
                Path("skills/orchestrate/SKILL.md"),
                "PS> gh release create v1\n",
            ),
            (
                Path("skills/orchestrate/SKILL.md"),
                "C:\\> gh release create v1\n",
            ),
            (
                Path("skills/orchestrate/SKILL.md"),
                "% gh release create v1\n",
            ),
            (
                Path("skills/orchestrate/SKILL.md"),
                "❯ gh release create v1\n",
            ),
            (
                Path("skills/orchestrate/SKILL.md"),
                "PS C:\\Temp> gh release create v1\n",
            ),
            (
                Path("skills/orchestrate/SKILL.md"),
                "C:\\Temp> gh release create v1\n",
            ),
            (
                Path("skills/orchestrate/SKILL.md"),
                "user@host:~$ gh release create v1\n",
            ),
            (
                Path("skills/orchestrate/SKILL.md"),
                "(venv) $ gh release create v1\n",
            ),
            (
                Path("skills/orchestrate/SKILL.md"),
                "```console\n# gh release create v1\n```",
            ),
            (
                Path("skills/orchestrate/SKILL.md"),
                "```bash\ngit status --short;nebula-publish\n```",
            ),
            (
                Path("skills/orchestrate/SKILL.md"),
                "```bash\ngit status "
                "--porcelain=$(gh${IFS}release${IFS}create${IFS}v1)\n```",
            ),
            (
                Path("skills/orchestrate/SKILL.md"),
                "```cmd\ngit status # & gh release create v1\n```",
            ),
            (
                Path("skills/orchestrate/SKILL.md"),
                "```bat\ngit status # & gh release create v1\n```",
            ),
            (
                Path("skills/orchestrate/SKILL.md"),
                "```fish\ngit status --porcelain=(nebula-publish)\n```",
            ),
            (
                Path("skills/orchestrate/SKILL.md"),
                "```fish\nprintf '%s\\n' (nebula-publish)\n```",
            ),
            (
                Path("skills/orchestrate/SKILL.md"),
                "```zsh\ngit status --porcelain==(nebula-publish)\n```",
            ),
            (
                Path("skills/orchestrate/SKILL.md"),
                "```zsh\nprintf '%s\\n' =(nebula-publish)\n```",
            ),
            (
                Path("skills/orchestrate/SKILL.md"),
                "```cmd\ngit status --porcelain=%NEBULA_COMMAND%\n```",
            ),
            (
                Path("skills/orchestrate/SKILL.md"),
                '<pre><code class="language-bash">'
                "gh release create v1</code></pre>",
            ),
            (
                Path("skills/orchestrate/SKILL.md"),
                "<pre>\ngh release create v1\n</pre>",
            ),
            (
                Path("skills/orchestrate/SKILL.md"),
                '<script>exec("nebula publish")</script>',
            ),
            (
                Path("skills/orchestrate/SKILL.md"),
                "<pre>C:\\Temp> git status # & gh release create v1</pre>",
            ),
            (
                Path("skills/orchestrate/SKILL.md"),
                "<pre><code>C:\\Temp> git status # & "
                "gh release create v1</code></pre>",
            ),
            (
                Path("skills/orchestrate/references/command.yaml"),
                "{executable: gh, args: [release, create]}\n",
            ),
            (
                Path("skills/orchestrate/references/command.yaml"),
                '\"executable\": gh\n\"args\": [release, create]\n',
            ),
            (
                Path("skills/orchestrate/references/command.yaml"),
                "Executable: gh\nArgs: [release, create]\n",
            ),
            (
                Path("skills/orchestrate/references/command.yaml"),
                '\"executable\" : gh\nargs: [release, create]\n',
            ),
            (
                Path("skills/orchestrate/references/command.yaml"),
                "Executable : gh\nArgs : [release, create]\n",
            ),
            (
                Path("skills/orchestrate/references/command.yaml"),
                "? executable\n: gh\n? args\n: [release, create]\n",
            ),
            (
                Path("skills/orchestrate/references/command.yaml"),
                "? executable\n# selected integration\n: gh\n"
                "? args\n: [release, create]\n",
            ),
            (
                Path("skills/orchestrate/references/command.yaml"),
                '"exec\\u0075table": gh\nargs: [release, create]\n',
            ),
            (
                Path("skills/orchestrate/references/command.yaml"),
                "uses: actions/checkout@v4\n",
            ),
            (
                Path("skills/orchestrate/references/command.yaml"),
                "uses: nebula/release@v1\n",
            ),
            (
                Path("skills/orchestrate/references/command.yaml"),
                "? command\n# selected integration\n"
                ": gh release create v1\n",
            ),
            (
                Path("skills/orchestrate/references/command.yaml"),
                '"com\\u006dand": gh release create v1\n',
            ),
            (
                Path("skills/orchestrate/scripts/example.pyw"),
                'import subprocess\nsubprocess.run(["gh", "release"])\n',
            ),
            (
                Path("skills/orchestrate/scripts/example.zsh"),
                "#!/bin/zsh\ngh release create v1\n",
            ),
            (Path("skills/orchestrate/scripts/example.fish"), "nebula publish\n"),
            (Path("skills/orchestrate/scripts/example.ps1"), "nebula publish\n"),
            (Path("skills/orchestrate/scripts/example.cmd"), "nebula publish\n"),
            (Path("skills/orchestrate/scripts/example.bat"), "nebula publish\n"),
            (
                Path("skills/orchestrate/scripts/example.js"),
                'require("child_process").exec("nebula publish evidence")\n',
            ),
            (
                Path("skills/orchestrate/scripts/example.rb"),
                'system("nebula publish evidence")\n',
            ),
            (
                Path("skills/orchestrate/scripts/example.ts"),
                'new Deno.Command("nebula").output();\n',
            ),
            (
                Path("skills/orchestrate/scripts/example.mjs"),
                'exec("nebula publish evidence");\n',
            ),
            (
                Path("skills/orchestrate/scripts/example.cjs"),
                'exec("nebula publish evidence");\n',
            ),
            (Path("skills/orchestrate/scripts/example.php"), 'system("nebula");\n'),
            (Path("skills/orchestrate/scripts/example.pl"), 'system("nebula");\n'),
            (Path("skills/orchestrate/scripts/example.lua"), 'os.execute("nebula")\n'),
            (Path("skills/orchestrate/scripts/example.vbs"), 'Run "nebula"\n'),
            (Path("skills/orchestrate/scripts/example"), 'run nebula publish\n'),
            (
                Path("skills/orchestrate/scripts/example"),
                "#!/usr/bin/env python3\nimport subprocess\n"
                'subprocess.run(["gh", "release"])\n',
            ),
        )

        for path, source in unsafe_samples:
            with self.subTest(source=source):
                violations = validator.scan_text(path, source)
                self.assertIn(
                    "bundled-provider-integration",
                    {item["rule"] for item in violations},
                )
    def test_orchestrate_command_gate_allows_non_command_content(self) -> None:
        validator = load_validator()

        for safe_content in (
            "New Markdown prose can explain any generic coordination policy.",
            "The `state transition decision` remains observable.",
            "recovery state transition",
            'command = "delegate through installed skill"',
            "```bash\n# Run the configured integration after approval.\n```",
            "# os.execvp('gh', ['gh', 'release', 'create', 'v1'])",
            "The fallback can call spawn() after resolution.",
            "we resolve configured integrations",
            "monitor meaningful transitions",
            "verify completed work",
            "recover durable evidence",
            "checks remain green",
            "reconcile tracker evidence",
            "record durable blockers",
            "pause at approval gates",
            "update existing checkpoint",
            "select executable frontier",
            "enforce one active task",
            "refuse direct implementation",
            "route work through Ask Matt",
            "reconcile tracker evidence;",
            "wait for meaningful transitions",
            "stop without merging",
            "close verified issue",
            "scheduler.run()",
            "The scheduler can call runner.run() after resolution.",
            "git status",
            "```bash\ngit status\n```",
            "```powershell\ngit status\n```",
            "```bash\nprintf '%s\\n' ready\n```",
            "```zsh\nprintf '%s\\n' ready\n```",
            "```python\nengine.run(snapshot)\n```",
            "- ```python\n  engine.run(snapshot)\n  ```",
            "```json\n{\"executable\": \"python\", "
            "\"args\": \"scripts/trace.py\"}\n```",
            "executable: python\nargs: scripts/trace.py",
            "- Parent\n    - Nested ordinary item",
            "- Parent\n    ordinary continuation prose",
            "```console\n$ git status\n```",
            "```console\n$ python scripts/trace.py\n```",
            "```powershell\nPS> git status\n```",
            "```bash\ngit status --short # inspect changes\n```",
            "```powershell\ngit status --short # inspect changes\n```",
            "```console\n$ git status --short # inspect changes\n```",
            "```bash\nprintf '%s: %s\\n' ready complete\n```",
            "```bash\nprintf '%s (%s)\\n' ready complete\n```",
            "```bash\nprintf 'Ready! %s!' complete\n```",
            "```bash\nprintf '%s\\n' 'ready (dry run)'\n```",
            "```bash\nprintf '(%s)\\n' ready\n```",
            "```bash\nprintf '%s %s\\n' ready now\n```",
            "PS C:\\Temp> git status",
            "C:\\work> git status",
            "user@host:~$ git status",
            "(venv) $ python scripts/trace.py",
            '<pre><code class="language-bash">git status</code></pre>',
        ):
            with self.subTest(safe_content=safe_content):
                violations = validator.scan_text(
                    Path("skills/orchestrate/SKILL.md"),
                    safe_content,
                )
                self.assertNotIn(
                    "bundled-provider-integration",
                    {item["rule"] for item in violations},
                )

    def test_orchestrate_allows_public_docs_and_local_runtime_commands(
        self,
    ) -> None:
        validator = load_validator()

        for safe_content in (
            "Read https://example.com/reference for the public format.",
            "Browse https://github.com/lightfastai/skills for public sources.",
            "[public docs](//example.com/Users/public/reference)",
            "notify the user promptly",
            "- notify the user promptly",
            "provider-independent behavior remains portable",
            "provider-independent release coordination remains generic",
            "read-only workflow policy remains explicit",
            "provider-independent release coordination",
            "- provider-independent release coordination",
            "read-only root task",
            "well-scoped delegation",
            "present concise outcomes",
            "record blockers durably",
            "vercel documentation remains public",
            "gh means the provider CLI",
            "> Read https://example.com/reference for the public format.",
            "python scripts/trace.py",
            "```bash\npython scripts/trace.py\n```",
            "$ python scripts/trace.py",
        ):
            with self.subTest(safe_content=safe_content):
                violations = validator.scan_text(
                    Path("skills/orchestrate/SKILL.md"),
                    safe_content,
                )
                self.assertNotIn(
                    "bundled-provider-integration",
                    {item["rule"] for item in violations},
                )

        local_runtime_source = (
            "import subprocess\n"
            'subprocess.run(["python", "scripts/trace.py"], check=True)\n'
        )
        violations = validator.scan_text(
            Path("skills/orchestrate/scripts/example.py"),
            local_runtime_source,
        )
        self.assertNotIn(
            "bundled-provider-integration",
            {item["rule"] for item in violations},
        )

        internal_runtime_source = "engine.run(snapshot)\n"
        violations = validator.scan_text(
            Path("skills/orchestrate/scripts/example.py"),
            internal_runtime_source,
        )
        self.assertNotIn(
            "bundled-provider-integration",
            {item["rule"] for item in violations},
        )

        safe_yaml = (
            "integration:\n  executable: python\n  args:\n"
            "    - scripts/trace.py\n"
        )
        violations = validator.scan_text(
            Path("skills/orchestrate/references/command.yaml"),
            safe_yaml,
        )
        self.assertNotIn(
            "bundled-provider-integration",
            {item["rule"] for item in violations},
        )

        for safe_yaml in (
            "- executable: python\n  args: scripts/trace.py\n",
            "executable: python\nargs: >\n  scripts/trace.py\n",
        ):
            violations = validator.scan_text(
                Path("skills/orchestrate/references/command.yaml"),
                safe_yaml,
            )
            self.assertNotIn(
                "bundled-provider-integration",
                {item["rule"] for item in violations},
            )

    def test_configured_integrations_stay_outside_the_coordination_kernel(
        self,
    ) -> None:
        outcomes = []
        for resolver in ("installed-tracker-a", "installed-tracker-b"):
            snapshot = prepared_snapshot()
            snapshot["repository"]["configured_integrations"] = {
                "tracker": {
                    "resolver": resolver,
                    "source": "installed-skill",
                    "approved": True,
                    "capability": "tracker",
                }
            }
            outcome = run_scenario(snapshot)
            self.assertNotIn(resolver, json.dumps(outcome))
            self.assertEqual(
                outcome["decisive_evidence"]["configured_integrations"],
                ["tracker"],
            )
            outcomes.append(outcome)

        self.assertEqual(outcomes[0], outcomes[1])
        self.assertEqual(outcomes[0]["decision"], "delegate")

    def test_validator_fails_closed_for_an_unsafe_public_skill(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill = root / "skills" / "unsafe-skill"
            (skill / "agents").mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\nname: unsafe-skill\n"
                "description: Demonstrate a public release.\n---\n"
                "Connect to https://release.internal with "
                "api_key = " + "sk" + "-release-secret-value.\n",
                encoding="utf-8",
            )
            (skill / "agents" / "openai.yaml").write_text(
                "interface:\n"
                '  display_name: "Unsafe Skill"\n'
                '  short_description: "Unsafe fixture"\n'
                '  default_prompt: "Use $unsafe-skill."\n',
                encoding="utf-8",
            )

            completed = subprocess.run(
                [sys.executable, str(VALIDATOR), "--root", str(root)],
                capture_output=True,
                check=False,
                text=True,
            )

        self.assertEqual(completed.returncode, 1)
        report = json.loads(completed.stdout)
        self.assertIn(
            "credential", {item["rule"] for item in report["violations"]}
        )
        self.assertIn(
            "internal-url", {item["rule"] for item in report["violations"]}
        )

    def test_validator_reports_malformed_skill_metadata_as_json(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "skills" / "missing-entrypoint").mkdir(parents=True)

            completed = subprocess.run(
                [sys.executable, str(VALIDATOR), "--root", str(root)],
                capture_output=True,
                check=False,
                text=True,
            )

        self.assertEqual(completed.returncode, 1)
        report = json.loads(completed.stdout)
        self.assertIn(
            "metadata", {item["rule"] for item in report["violations"]}
        )

    def test_sensitive_content_in_any_skill_file_type_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill = root / "skills" / "unsafe-skill"
            (skill / "agents").mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\nname: unsafe-skill\n"
                "description: Demonstrate a public release.\n---\nSafe.\n",
                encoding="utf-8",
            )
            (skill / "agents" / "openai.yaml").write_text(
                "interface:\n"
                '  display_name: "Unsafe Skill"\n'
                '  short_description: "Unsafe fixture"\n'
                '  default_prompt: "Use $unsafe-skill."\n',
                encoding="utf-8",
            )
            (skill / "references").mkdir()
            (skill / "references" / "leak.txt").write_text(
                "Authorization: Bearer " + "gh" + "p_releaseSecret123\n",
                encoding="utf-8",
            )
            (skill / "assets").mkdir()
            (skill / "assets" / "opaque.bin").write_bytes(b"\x00private")

            completed = subprocess.run(
                [sys.executable, str(VALIDATOR), "--root", str(root)],
                capture_output=True,
                check=False,
                text=True,
            )

        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn(
            "credential", {item["rule"] for item in report["violations"]}
        )
        self.assertIn(
            "unscannable-binary",
            {item["rule"] for item in report["violations"]},
        )

    def test_every_public_skill_installs_by_name_in_an_isolated_project(
        self,
    ) -> None:
        environment = os.environ.copy()
        environment["NO_COLOR"] = "1"
        for skill_name in ("manage-public-presence", "orchestrate"):
            with self.subTest(skill=skill_name), tempfile.TemporaryDirectory() as (
                directory
            ):
                project = Path(directory)
                subprocess.run(
                    ["git", "init", "-q"],
                    cwd=project,
                    check=True,
                )
                completed = subprocess.run(
                    [
                        "npx",
                        "--yes",
                        "skills",
                        "add",
                        str(ROOT),
                        "--skill",
                        skill_name,
                        "--agent",
                        "codex",
                        "--copy",
                        "--yes",
                    ],
                    cwd=project,
                    capture_output=True,
                    check=True,
                    env=environment,
                    text=True,
                )

                installed = project / ".agents" / "skills" / skill_name
                self.assertTrue((installed / "SKILL.md").is_file())
                self.assertIn("Local path validated", completed.stdout)

    def test_cleanliness_gate_rejects_uncommitted_release_artifacts(self) -> None:
        validator = load_validator()
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            subprocess.run(["git", "init", "-q"], cwd=repository, check=True)
            subprocess.run(
                ["git", "config", "user.email", "release@example.test"],
                cwd=repository,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Release Test"],
                cwd=repository,
                check=True,
            )
            marker = repository / "tracked.txt"
            marker.write_text("tracked\n", encoding="utf-8")
            subprocess.run(["git", "add", "tracked.txt"], cwd=repository, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "fixture"],
                cwd=repository,
                check=True,
            )
            self.assertEqual(validator.cleanliness_violations(repository), [])

            (repository / "release.tmp").write_text("generated\n", encoding="utf-8")
            violations = validator.cleanliness_violations(repository)

        self.assertEqual(
            {item["rule"] for item in violations},
            {"repository-cleanliness"},
        )


if __name__ == "__main__":
    unittest.main()
