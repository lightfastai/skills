#!/usr/bin/env python3
"""Validate public skill packaging, documentation, and release safety."""

import argparse
import ast
import html
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


REQUIRED_PUBLICATION_CHECKS = {
    "metadata",
    "installability",
    "documentation",
    "provider-independence",
    "sensitive-content",
    "single-high-level-seam",
}
SECURITY_PATTERNS: Tuple[Tuple[str, re.Pattern], ...] = (
    (
        "credential",
        re.compile(
            r"(?i)\b(?:api[_-]?key|access[_-]?token|client[_-]?secret|"
            r"password|private[_-]?key)\s*[:=]\s*[\"']?[^\s\"'<>]{8,}"
        ),
    ),
    (
        "credential",
        re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    ),
    (
        "credential",
        re.compile(r"(?i)\bauthorization\s*:\s*bearer\s+\S+"),
    ),
    (
        "credential",
        re.compile(
            r"\b(?:gh[pousr]_[A-Za-z0-9]{12,}|glpat-[A-Za-z0-9_-]{12,}|"
            r"github_pat_[A-Za-z0-9_]{20,}|"
            r"AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9_-]{12,}|"
            r"xox[baprs]-[A-Za-z0-9-]{12,}|AIza[A-Za-z0-9_-]{20,}|"
            r"npm_[A-Za-z0-9_-]{12,})\b"
        ),
    ),
    (
        "credential",
        re.compile(
            r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\."
            r"[A-Za-z0-9_-]{8,}\b"
        ),
    ),
    (
        "credential",
        re.compile(
            r"(?i)\b[A-Z0-9_]*(?:SECRET|TOKEN|PASSWORD|PRIVATE_KEY|API_KEY)"
            r"[A-Z0-9_]*\s*[:=]\s*[\"']?[^\s\"'<>]{8,}"
        ),
    ),
    (
        "private-identifier",
        re.compile(
            r"(?<![0-9a-fA-F])[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-"
            r"[0-9a-fA-F]{4}-[89abAB][0-9a-fA-F]{3}-"
            r"[0-9a-fA-F]{12}(?![0-9a-fA-F])"
        ),
    ),
    (
        "private-identifier",
        re.compile(
            r"(?i)(?<![A-Za-z0-9._/-])/"
            r"(?:mnt/[a-z]|cygdrive/[a-z]|[a-z])/"
            r"(?:Users|Documents and Settings|DOCUME~[1-9][0-9]*)/"
            r"[^/\s<>()[\]{}\"'`]+"
        ),
    ),
    (
        "private-identifier",
        re.compile(
            r"(?<![A-Za-z0-9._/-])(?:/Users/|/home/)[^\s\"']+"
        ),
    ),
    (
        "private-identifier",
        re.compile(r"(?i)file:///(?:Users|home)/[^/\s\"']+"),
    ),
    (
        "private-identifier",
        re.compile(
            r"(?i)(?<![a-z0-9_])(?:"
            r"(?:file|smb)://[^/\s]+/(?:[^/\s]+/)?|"
            r"(?:\\\\|(?<!:)//(?![^/\s]+\.))\?[\\/]+UNC[\\/]+"
            r"[^\\/\s<>()[\]{}\"'`]+[\\/]+"
            r"[^\\/\s<>()[\]{}\"'`]+[\\/]+|"
            r"(?:\\\\|(?<!:)//(?![^/\s]+\.))"
            r"[^\\/\s<>()[\]{}\"'`]+[\\/]+"
            r"(?:(?:[a-z]\$|[^\\/\s<>()[\]{}\"'`]+)[\\/]+)?|"
            r"(?:(?:\\\\|//)\?[\\/]+)?[a-z]:[\\/]+"
            r")(?:Users|Documents and Settings|DOCUME~[1-9][0-9]*)[\\/]+"
            r"[^\\/\s<>()[\]{}\"'`]+"
        ),
    ),
    (
        "private-identifier",
        re.compile(
            r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b"
        ),
    ),
    (
        "internal-url",
        re.compile(
            r"(?i)https?://(?:localhost|127\.0\.0\.1|10(?:\.\d{1,3}){3}|"
            r"172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2}|"
            r"192\.168(?:\.\d{1,3}){2}|\[?::1\]?|"
            r"\[(?:f[cd][0-9a-f]{2}|fe[89ab])[0-9a-f:]*\]|"
            r"[^/\s]+\.(?:internal|local|corp|lan|intranet)|"
            r"[a-z0-9-]+(?::\d+)?/)"
        ),
    ),
    (
        "copied-provider-response",
        re.compile(r"(?i)\b(?:provider_response|raw_provider_response)\b"),
    ),
    (
        "copied-provider-response",
        re.compile(
            r"(?i)[\"'](?:request_id|response_headers|provider_request_id)"
            r"[\"']\s*:"
        ),
    ),
    (
        "copied-provider-response",
        re.compile(r"(?i)[\"']object[\"']\s*:\s*[\"'][^\"']+[\"']"),
    ),
    (
        "project-specific",
        re.compile(r"(?i)\b(?:quasar|pq-1)\b"),
    ),
)
PROVIDER_IMPLEMENTATION = re.compile(
    r"(?i)(?:"
    r"\b(?:import|from)\s+(?:github|gitlab|boto3|google\.cloud|azure|"
    r"huggingface_hub|openai|anthropic)\b|"
    r"https?://(?:api\.github\.com|gitlab\.com/api|api\.linear\.app|"
    r"api\.vercel\.com|huggingface\.co/api|api\.atlassian\.com|"
    r"[^/\s]+\.amazonaws\.com|[^/\s]+\.googleapis\.com|"
    r"api\.openai\.com|api\.anthropic\.com)(?:/|\b)"
    r")"
)
COMMAND_ASSIGNMENT = re.compile(
    r"(?im)[\"']?(?:command|cmd|argv|script)[\"']?\s*[:=]\s*"
    r"(?:\"([^\"\r\n]+)\"|'([^'\r\n]+)'|"
    r"(\[[^\]\r\n]+\])|([^,}\r\n]+))"
)
MARKDOWN_FENCE_OPEN = re.compile(
    r"^ {0,3}(?P<fence>`{3,}|~{3,})(?P<info>.*)$"
)
COMMAND_PROMPT_PATTERN = (
    r"(?:PS>|PS\s+[^>\r\n]+>|[A-Z]:\\[^>\r\n]*>|"
    r"[^\s@]+@[^\s:]+:[^$\r\n]*\$|\([^)\r\n]+\)\s+\$|"
    r"\$|%|❯)"
)
COMMAND_PROMPT = re.compile(rf"(?i)^{COMMAND_PROMPT_PATTERN}\s+")
STRONG_COMMAND_LINE = re.compile(
    rf"(?im)^\s*(?:{COMMAND_PROMPT_PATTERN}\s+|run:\s+|\t+)"
    r"([^\r\n]+)$"
)
RUN_INLINE_COMMAND = re.compile(r"(?i)\b(?:run|execute)\s+`([^`\r\n]+)`")
YAML_COMMAND_FIELD = re.compile(
    r"^(?P<indent>[ \t]*)(?P<sequence>-\s+)?"
    r"(?P<name>\"(?:\\.|[^\"])*\"|'(?:''|[^'])*'|"
    r"[A-Za-z_][A-Za-z0-9_-]*)[ \t]*:"
    r"\s*(?P<value>.*?)\s*$"
)
YAML_MAPPING_FIELD = re.compile(r"^(?P<indent>[ \t]*)(?:-\s+)?[^#\s][^:]*:")
DECLARATIVE_KERNEL_INSTRUCTION = re.compile(
    r"(?i)^(?:delegate|resolve) (?:through|via|using) "
    r"(?:an? )?(?:installed skill|declared capability)$"
)
COMMAND_FIELD_NAMES = {"argv", "cmd", "command", "script", "uses"}
YAML_COMMAND_FIELD_NAMES = COMMAND_FIELD_NAMES | {"args", "executable"}
ALLOWED_LOCAL_SCRIPTS = {
    "scripts/trace.py",
    "skills/orchestrate/scripts/trace.py",
}
ALLOWED_PYTHON_IMPORT_ROOTS = {
    "datetime",
    "json",
    "math",
    "re",
    "subprocess",
    "sys",
    "typing",
}
DECLARATIVE_TEXT_SUFFIXES = {
    ".json",
    ".markdown",
    ".md",
    ".txt",
    ".yaml",
    ".yml",
}
SHELL_FENCE_LANGUAGES = {
    "bash",
    "bat",
    "cmd",
    "console",
    "fish",
    "powershell",
    "ps1",
    "pwsh",
    "sh",
    "shell",
    "zsh",
}


def command_tokens(value: object) -> Optional[List[str]]:
    """Return normalized tokens for literal command content."""
    if isinstance(value, str):
        try:
            return shlex.split(value)
        except ValueError:
            return None
    if isinstance(value, (list, tuple)) and all(
        isinstance(item, str) for item in value
    ):
        return list(value)
    return None


def command_line_tokens(
    value: str,
    root_prompt: bool = False,
    inline_comments: bool = False,
    language: str = "",
) -> Optional[List[str]]:
    """Remove a recognized transcript prompt before tokenizing a command."""
    command = value.strip()
    cmd_context = bool(
        language in {"bat", "cmd"}
        or (
            not command.lower().startswith("ps ")
            and re.match(r"(?i)^[A-Z]:\\[^>\r\n]*>\s+", command)
        )
    )
    if root_prompt and command.startswith("# "):
        command = command[2:]
    command = COMMAND_PROMPT.sub("", command, count=1)
    if inline_comments:
        quote = None
        for index, character in enumerate(command):
            if quote:
                if (
                    character == quote
                    and (index == 0 or command[index - 1] != "\\")
                ):
                    quote = None
                continue
            if character in {"'", '"'}:
                quote = character
            elif (
                character == "#"
                and (index == 0 or command[index - 1].isspace())
            ):
                command = command[:index].rstrip()
                break
    if has_unquoted_shell_syntax(command, language, cmd_context):
        return None
    return command_tokens(command)


def supports_inline_hash_comments(language: str, command: str) -> bool:
    """Return whether `#` is comment syntax for this transcript context."""
    if language in {"bat", "cmd"}:
        return False
    if re.match(
        r"(?i)^\s*[A-Z]:\\[^>\r\n]*>\s+",
        command,
    ):
        return False
    return True


def has_unquoted_shell_syntax(
    command: str,
    language: str,
    cmd_context: bool,
) -> bool:
    """Reject executable shell syntax while preserving quoted literal data."""
    quote = None
    for index, character in enumerate(command):
        if quote:
            if character == quote and (index == 0 or command[index - 1] != "\\"):
                quote = None
            elif quote == '"' and character in {"$", "`"} and not cmd_context:
                return True
            continue
        if character in {"'", '"'}:
            quote = character
        elif character in ";&|`$<>":
            return True
        elif character in "()" and language not in {"powershell", "ps1", "pwsh"}:
            return True
    return bool(
        cmd_context
        and (
            re.search(r"%[^%]+%", command)
            or re.search(r"![^!]+!", command)
        )
    )


def structured_command_tokens(value: object) -> Optional[List[str]]:
    """Tokenize command strings as shell syntax and argv as literal data."""
    if isinstance(value, str):
        return command_line_tokens(value, language="shell")
    return command_tokens(value)


def is_allowed_generic_command(tokens: Optional[List[str]]) -> bool:
    """Allow only declared delegation prose and the packaged local tracer."""
    if not tokens:
        return False
    normalized = " ".join(tokens)
    if DECLARATIVE_KERNEL_INSTRUCTION.fullmatch(normalized):
        return True
    runtime = tokens[0].lower()
    if runtime == "git":
        return bool(
            len(tokens) >= 2
            and tokens[1] == "status"
            and all(token.startswith("-") for token in tokens[2:])
        )
    if runtime == "printf":
        return len(tokens) >= 2
    if not re.fullmatch(r"python(?:3(?:\.\d+)*)?", runtime):
        return False
    if len(tokens) != 2:
        return False
    script = tokens[1].replace("\\", "/")
    while script.startswith("./"):
        script = script[2:]
    return script in ALLOWED_LOCAL_SCRIPTS


def literal_value(node: ast.AST) -> object:
    try:
        return ast.literal_eval(node)
    except (TypeError, ValueError):
        return None


def command_mapping_violation(mapping: Dict[str, object]) -> bool:
    """Check structured command fields without guessing provider names."""
    for name in COMMAND_FIELD_NAMES:
        if name in mapping:
            tokens = structured_command_tokens(mapping[name])
            if not is_allowed_generic_command(tokens):
                return True
    if "executable" in mapping:
        executable = mapping["executable"]
        if not isinstance(executable, str):
            return True
        arguments = mapping.get("args", [])
        argument_tokens = command_tokens(arguments)
        if argument_tokens is None:
            return True
        if not is_allowed_generic_command([executable, *argument_tokens]):
            return True
    return False


def is_generic_execution_name(name: str) -> bool:
    normalized = name.lower()
    return bool(
        normalized in {"call", "invoke", "popen", "run", "system"}
        or normalized.startswith("exec")
        or "command" in normalized
        or "spawn" in normalized
        or normalized.endswith(("_call", "_output"))
    )


def python_call_tokens(node: ast.Call) -> Optional[List[str]]:
    """Read a literal positional or args= command from a Python call."""
    command_node = node.args[0] if node.args else None
    for keyword in node.keywords:
        if keyword.arg == "args":
            command_node = keyword.value
            break
    if command_node is None:
        return None
    return structured_command_tokens(literal_value(command_node))


def has_dangerous_python_lookup(tree: ast.AST) -> bool:
    """Reject dynamic namespace access that can recover executable modules."""
    dangerous_builtins = {
        "__builtins__",
        "__import__",
        "eval",
        "exec",
        "getattr",
        "globals",
        "locals",
        "vars",
    }
    return any(
        (
            isinstance(node, ast.Name)
            and isinstance(node.ctx, ast.Load)
            and node.id in dangerous_builtins
        )
        or (
            isinstance(node, ast.Attribute)
            and node.attr in dangerous_builtins
        )
        for node in ast.walk(tree)
    )


def allowed_python_imports(
    tree: ast.AST,
) -> Optional[
    Tuple[Dict[str, str], Dict[str, str], Dict[str, Tuple[str, str]]]
]:
    """Resolve approved imports, or reject unsafe roots and module access."""
    module_aliases = {"subprocess": "subprocess", "os": "os"}
    allowed_module_aliases: Dict[str, str] = {}
    imported_calls: Dict[str, Tuple[str, str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for imported in node.names:
                root = imported.name.split(".", 1)[0]
                if root not in ALLOWED_PYTHON_IMPORT_ROOTS:
                    return None
                alias = imported.asname or root
                allowed_module_aliases[alias] = root
                if root in {"os", "subprocess"}:
                    module_aliases[imported.asname or imported.name] = (
                        imported.name
                    )
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".", 1)[0]
            if node.level > 0 or root not in ALLOWED_PYTHON_IMPORT_ROOTS:
                return None
            if any(imported.name == "*" for imported in node.names):
                return None
            if node.module == "sys" and any(
                imported.name not in {"stderr", "stdin", "stdout"}
                for imported in node.names
            ):
                return None
            if node.module in {"os", "subprocess"}:
                for imported in node.names:
                    imported_calls[imported.asname or imported.name] = (
                        node.module,
                        imported.name,
                    )

    parents = {
        child: parent
        for parent in ast.walk(tree)
        for child in ast.iter_child_nodes(parent)
    }
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and allowed_module_aliases.get(node.value.id) == "sys"
            and node.attr not in {"stderr", "stdin", "stdout"}
        ):
            return None
        if not (
            isinstance(node, ast.Name)
            and isinstance(node.ctx, ast.Load)
            and node.id in module_aliases
        ):
            continue
        parent = parents.get(node)
        if not (isinstance(parent, ast.Attribute) and parent.value is node):
            return None
    return module_aliases, allowed_module_aliases, imported_calls


def has_compound_executable_reference(
    tree: ast.AST,
    module_aliases: Dict[str, str],
    imported_calls: Dict[str, Tuple[str, str]],
) -> bool:
    """Reject executable callables hidden inside compound expressions."""
    parents = {
        child: parent
        for parent in ast.walk(tree)
        for child in ast.iter_child_nodes(parent)
    }
    for node in ast.walk(tree):
        executable_reference = False
        if (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
        ):
            module = module_aliases.get(node.value.id)
            executable_reference = bool(
                module == "subprocess"
                or (
                    module == "os"
                    and is_generic_execution_name(node.attr)
                )
                or node.attr == "startfile"
            )
        elif (
            isinstance(node, ast.Name)
            and isinstance(node.ctx, ast.Load)
            and node.id in imported_calls
        ):
            executable_reference = True
        if not executable_reference:
            continue
        parent = parents.get(node)
        if isinstance(parent, ast.Call) and parent.func is node:
            continue
        if isinstance(parent, (ast.Assign, ast.AnnAssign)):
            if parent.value is node:
                continue
        return True
    return False


def python_implementation_violation(text: str) -> Optional[bool]:
    """Parse Python implementation and default-deny executable call sites."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return None

    if has_dangerous_python_lookup(tree):
        return True

    approved_imports = allowed_python_imports(tree)
    if approved_imports is None:
        return True
    module_aliases, allowed_module_aliases, imported_calls = approved_imports
    if has_compound_executable_reference(
        tree,
        module_aliases,
        imported_calls,
    ):
        return True
    client_instances = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        value = node.value
        if not isinstance(value, ast.Call):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        for target in targets:
            if not isinstance(target, ast.Name):
                continue
            named_client = "client" in target.id.lower()
            constructed_client = bool(
                isinstance(value.func, ast.Name)
                and value.func.id[:1].isupper()
            )
            factory_client = bool(
                isinstance(value.func, ast.Name)
                and "client" in value.func.id.lower()
            )
            qualified_client = bool(
                isinstance(value.func, ast.Attribute)
                and (
                    value.func.attr[:1].isupper()
                    or "client" in value.func.attr.lower()
                )
            )
            if (
                named_client
                or constructed_client
                or factory_client
                or qualified_client
            ):
                client_instances.add(target.id)

    def call_target(function: ast.AST) -> Tuple[Optional[str], Optional[str]]:
        if isinstance(function, ast.Attribute):
            if isinstance(function.value, ast.Name):
                module = module_aliases.get(function.value.id)
                if module is not None:
                    return module, function.attr
            if function.attr in imported_calls:
                return imported_calls[function.attr]
            return None, function.attr
        if isinstance(function, ast.Name) and function.id in imported_calls:
            return imported_calls[function.id]
        if (
            isinstance(function, ast.Call)
            and isinstance(function.func, ast.Name)
            and function.func.id == "getattr"
            and len(function.args) >= 2
            and isinstance(function.args[0], ast.Name)
        ):
            module = module_aliases.get(function.args[0].id)
            name = literal_value(function.args[1])
            return module, name if isinstance(name, str) else None
        return None, None

    changed = True
    while changed:
        changed = False
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Assign, ast.AnnAssign)):
                continue
            targets = (
                node.targets if isinstance(node, ast.Assign) else [node.target]
            )
            module, name = call_target(node.value)
            if module is None or name is None:
                continue
            for target in targets:
                target_name = None
                if isinstance(target, ast.Name):
                    target_name = target.id
                elif isinstance(target, ast.Attribute):
                    target_name = target.attr
                if (
                    target_name is not None
                    and imported_calls.get(target_name) != (module, name)
                ):
                    imported_calls[target_name] = (module, name)
                    changed = True

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                root = node.func.value
                depth = 1
                while isinstance(root, ast.Attribute):
                    depth += 1
                    root = root.value
                constructed_client = bool(
                    isinstance(root, ast.Call)
                    and isinstance(root.func, ast.Name)
                    and root.func.id[:1].isupper()
                )
                named_client = bool(
                    isinstance(root, ast.Name)
                    and root.id in client_instances
                )
                unapproved_chain = bool(
                    depth >= 2
                    and (
                        not isinstance(root, ast.Name)
                        or root.id not in allowed_module_aliases
                    )
                )
                if constructed_client or named_client or unapproved_chain:
                    return True
            module, resolved_name = call_target(node.func)
            name = resolved_name
            if name is None:
                if not isinstance(node.func, ast.Name):
                    continue
                name = node.func.id
            tokens = python_call_tokens(node)
            if module == "subprocess":
                if not is_allowed_generic_command(tokens):
                    return True
                continue
            if module == "os":
                if not is_allowed_generic_command(tokens):
                    return True
                continue
            if (
                is_generic_execution_name(name)
                and tokens is not None
                and (node.args or node.keywords)
            ):
                if not is_allowed_generic_command(tokens):
                    return True
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            value = literal_value(node.value)
            for target in targets:
                if isinstance(target, ast.Name) and target.id in COMMAND_FIELD_NAMES:
                    tokens = command_tokens(value)
                    if not is_allowed_generic_command(tokens):
                        return True
        elif isinstance(node, ast.Dict):
            mapping = {
                key.value: literal_value(value)
                for key, value in zip(node.keys, node.values)
                if isinstance(key, ast.Constant) and isinstance(key.value, str)
            }
            if command_mapping_violation(mapping):
                return True
    return False


def command_assignment_tokens(raw_value: str) -> Optional[List[str]]:
    """Normalize string and argument-array command fields."""
    try:
        value = ast.literal_eval(raw_value)
    except (SyntaxError, ValueError):
        value = raw_value.strip(" \t,{}[]\"'")
    return structured_command_tokens(value)


def contains_serialized_command(text: str) -> bool:
    """Recognize structured command objects while allowing the local tracer."""
    try:
        value = json.loads(text)
    except (TypeError, ValueError):
        return False

    def visit(item: object) -> bool:
        if isinstance(item, dict):
            if command_mapping_violation(item):
                return True
            return any(visit(child) for child in item.values())
        if isinstance(item, list):
            return any(visit(child) for child in item)
        return False

    return visit(value)


def split_yaml_flow_items(text: str) -> List[str]:
    """Split a YAML flow mapping without splitting nested sequences."""
    items = []
    start = 0
    depth = 0
    quote = None
    for index, character in enumerate(text):
        if quote:
            if character == quote and (index == 0 or text[index - 1] != "\\"):
                quote = None
            continue
        if character in {"'", '"'}:
            quote = character
        elif character in "[({":
            depth += 1
        elif character in "])}":
            depth = max(0, depth - 1)
        elif character == "," and depth == 0:
            items.append(text[start:index])
            start = index + 1
    items.append(text[start:])
    return items


def yaml_command_value(name: str, raw_value: str) -> object:
    """Parse the scalar and sequence forms used by command mappings."""
    try:
        return ast.literal_eval(raw_value)
    except (SyntaxError, ValueError):
        value = raw_value.strip(" \t\"'")
        if name == "args" and raw_value.startswith("["):
            return [
                item.strip(" \t\"'")
                for item in split_yaml_flow_items(raw_value.strip("[]"))
            ]
        return value


def yaml_key_name(raw_name: str) -> str:
    """Decode quoted YAML keys before comparing structural field names."""
    name = raw_name.strip()
    if name.startswith(('"', "'")):
        try:
            decoded = ast.literal_eval(name)
        except (SyntaxError, ValueError):
            return ""
        if not isinstance(decoded, str):
            return ""
        name = decoded
    return name.lower()


def normalize_yaml_explicit_keys(text: str) -> str:
    """Convert YAML's explicit `? key` / `: value` form for scanning."""
    lines = text.splitlines()
    normalized = []
    index = 0
    while index < len(lines):
        key = re.match(r"^(?P<indent>[ \t]*)\?\s+(.+?)\s*$", lines[index])
        if key and index + 1 < len(lines):
            value_index = index + 1
            while (
                value_index < len(lines)
                and (
                    not lines[value_index].strip()
                    or lines[value_index].lstrip().startswith("#")
                )
            ):
                value_index += 1
            value = re.match(
                r"^[ \t]*:\s*(.*?)\s*$",
                lines[value_index],
            ) if value_index < len(lines) else None
            if value:
                normalized.append(
                    f"{key.group('indent')}{key.group(2)}: {value.group(1)}"
                )
                index = value_index + 1
                continue
        normalized.append(lines[index])
        index += 1
    return "\n".join(normalized)


def yaml_flow_command_violation(text: str) -> bool:
    """Check explicit command mappings written in YAML flow style."""
    for match in re.finditer(r"\{([^{}\r\n]*)\}", text):
        mapping: Dict[str, object] = {}
        for item in split_yaml_flow_items(match.group(1)):
            if ":" not in item:
                continue
            raw_name, raw_value = item.split(":", 1)
            name = yaml_key_name(raw_name)
            if name in YAML_COMMAND_FIELD_NAMES:
                mapping[name] = yaml_command_value(name, raw_value.strip())
        if command_mapping_violation(mapping):
            return True
    return False


def contains_yaml_command(text: str) -> bool:
    """Recognize executable/args pairs in dependency-free YAML mappings."""
    text = normalize_yaml_explicit_keys(text)
    if yaml_flow_command_violation(text):
        return True
    fields_by_indent: Dict[int, Dict[str, object]] = {}
    lines = text.splitlines()
    for index, line in enumerate(lines):
        match = YAML_COMMAND_FIELD.match(line)
        if not match:
            mapping = YAML_MAPPING_FIELD.match(line)
            if mapping:
                boundary = len(mapping.group("indent").expandtabs(8))
                if any(
                    command_mapping_violation(fields)
                    for level, fields in fields_by_indent.items()
                    if level >= boundary
                ):
                    return True
                fields_by_indent = {
                    level: fields
                    for level, fields in fields_by_indent.items()
                    if level < boundary
                }
            continue
        indent = len(match.group("indent").expandtabs(8)) + len(
            (match.group("sequence") or "").expandtabs(8)
        )
        name = yaml_key_name(match.group("name"))
        if name not in YAML_COMMAND_FIELD_NAMES:
            boundary = len(match.group("indent").expandtabs(8))
            if any(
                command_mapping_violation(fields)
                for level, fields in fields_by_indent.items()
                if level >= boundary
            ):
                return True
            fields_by_indent = {
                level: fields
                for level, fields in fields_by_indent.items()
                if level < boundary
            }
            continue
        raw_value = match.group("value")
        value = yaml_command_value(name, raw_value)
        if name == "args" and re.fullmatch(r"[>|][+-]?\d*", raw_value):
            folded = []
            for child in lines[index + 1 :]:
                if not child.strip() or child.lstrip().startswith("#"):
                    continue
                child_indent = len(child) - len(child.lstrip(" \t"))
                if child_indent <= indent:
                    break
                folded.append(child.strip())
            value = " ".join(folded)
        if name == "args" and not raw_value:
            value = []
            for child in lines[index + 1 :]:
                if not child.strip() or child.lstrip().startswith("#"):
                    continue
                child_indent = len(child) - len(child.lstrip(" \t"))
                if child_indent <= indent:
                    break
                sequence_item = re.match(r"^[ \t]*-\s+(.+?)\s*$", child)
                if sequence_item:
                    value.append(sequence_item.group(1).strip(" \t\"'"))
        fields = fields_by_indent.setdefault(indent, {})
        if name == "executable" and "executable" in fields:
            if command_mapping_violation(fields):
                return True
            fields = {}
            fields_by_indent[indent] = fields
        fields[name] = value
        if "args" in fields and command_mapping_violation(fields):
            return True
    return any(
        command_mapping_violation(fields)
        for fields in fields_by_indent.values()
    )


def markdown_fenced_blocks(text: str) -> Iterable[Tuple[str, str]]:
    """Yield CommonMark fenced blocks with normalized info-string language."""
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        opening = MARKDOWN_FENCE_OPEN.match(lines[index])
        if not opening:
            index += 1
            continue
        fence = opening.group("fence")
        if fence[0] == "`" and "`" in opening.group("info"):
            index += 1
            continue
        info = opening.group("info").strip()
        language = info.split(None, 1)[0] if info else ""
        language = language.strip("{}").lstrip(".").lower()
        closing = re.compile(
            rf"^ {{0,3}}{re.escape(fence[0])}{{{len(fence)},}}[ \t]*$"
        )
        body = []
        index += 1
        while index < len(lines) and not closing.match(lines[index]):
            body.append(lines[index])
            index += 1
        yield language, "\n".join(body)
        if index < len(lines):
            index += 1


def normalize_markdown_containers(text: str) -> str:
    """Remove CommonMark quote/list containers before structural scanning."""
    normalized = []
    active_list_indent = 0
    quote = re.compile(r"^ {0,3}>[ \t]?")
    list_item = re.compile(r"^ {0,3}(?:[-+*]|\d+[.)])[ \t]+")
    for raw_line in text.splitlines():
        line = raw_line
        while quote.match(line):
            line = line[quote.match(line).end():]
        consumed_indent = 0
        if (
            active_list_indent
            and line.startswith(" " * active_list_indent)
        ):
            line = line[active_list_indent:]
            consumed_indent = active_list_indent
        matched_list = False
        while True:
            match = list_item.match(line)
            if not match:
                break
            matched_list = True
            consumed_indent += match.end()
            line = line[match.end():]
        if matched_list:
            active_list_indent = consumed_indent
        elif line.strip() and not raw_line[:1].isspace():
            active_list_indent = 0
        normalized.append(line)
    return "\n".join(normalized)


def markdown_indented_command_violation(text: str) -> bool:
    """Check CommonMark indented code while ignoring fenced block bodies."""
    closing = None
    for line in text.splitlines():
        if closing is not None:
            if closing.match(line):
                closing = None
            continue
        opening = MARKDOWN_FENCE_OPEN.match(line)
        if opening:
            fence = opening.group("fence")
            closing = re.compile(
                rf"^ {{0,3}}{re.escape(fence[0])}{{{len(fence)},}}[ \t]*$"
            )
            continue
        match = re.match(r"^(?: {4}|\t)(.*)$", line)
        if not match:
            continue
        stripped = match.group(1).strip()
        if (
            stripped
            and not stripped.startswith("#")
            and not is_allowed_generic_command(
                command_line_tokens(
                    stripped,
                    inline_comments=True,
                    language="bash",
                )
            )
        ):
            return True
    return False


def executable_code_block_violation(language: str, body: str) -> bool:
    """Apply the language-aware policy shared by Markdown code blocks."""
    if language == "json":
        return contains_serialized_command(body)
    if language in {"yaml", "yml"}:
        return contains_yaml_command(body)
    if language in {"markdown", "md", "text", "txt"}:
        return False
    if language in {"py", "python", "python3"}:
        parsed = python_implementation_violation(body)
        return has_unparseable_source(body) if parsed is None else parsed
    if language and language not in SHELL_FENCE_LANGUAGES:
        return has_unparseable_source(body)
    for line in body.splitlines():
        stripped = line.strip()
        root_prompt = language == "console" and stripped.startswith("# ")
        if (
            stripped
            and (root_prompt or not stripped.startswith("#"))
            and not is_allowed_generic_command(
                command_line_tokens(
                    stripped,
                    root_prompt=root_prompt,
                    inline_comments=supports_inline_hash_comments(
                        language,
                        stripped,
                    ),
                    language=language,
                )
            )
        ):
            return True
    return False


def markdown_html_code_violation(text: str) -> bool:
    """Scan CommonMark raw-HTML pre/code blocks as executable structures."""
    for script in re.finditer(
        r"(?is)<script\b[^>]*>(.*?)</script\s*>",
        text,
    ):
        if has_unparseable_source(html.unescape(script.group(1))):
            return True
    blocks = re.compile(
        r"(?is)<pre\b[^>]*>\s*(?:"
        r"<code\b(?P<attrs>[^>]*)>(?P<code_body>.*?)</code>|"
        r"(?P<pre_body>.*?))\s*</pre\s*>"
    )
    for match in blocks.finditer(text):
        attributes = match.group("attrs") or ""
        language_match = re.search(
            r"(?i)\blanguage-([a-z0-9_+.-]+)",
            attributes,
        )
        language = language_match.group(1).lower() if language_match else ""
        body = html.unescape(
            match.group("code_body")
            if match.group("code_body") is not None
            else match.group("pre_body") or ""
        )
        if executable_code_block_violation(language, body):
            return True
    return False


def structured_command_violation(text: str, path: Path) -> bool:
    """Check explicit command-bearing structures in public non-Python files."""
    if contains_serialized_command(text) or contains_yaml_command(text):
        return True
    for match in COMMAND_ASSIGNMENT.finditer(text):
        raw_assignment = next(
            group for group in match.groups() if group is not None
        )
        if not is_allowed_generic_command(
            command_assignment_tokens(raw_assignment)
        ):
            return True
    markdown_text = None
    if path.suffix.lower() in {".markdown", ".md"}:
        markdown_text = normalize_markdown_containers(text)
        for language, body in markdown_fenced_blocks(markdown_text):
            if executable_code_block_violation(language, body):
                return True
        if markdown_html_code_violation(markdown_text):
            return True
        if markdown_indented_command_violation(markdown_text):
            return True
    pattern_text = markdown_text if markdown_text is not None else text
    for pattern in (STRONG_COMMAND_LINE, RUN_INLINE_COMMAND):
        for match in pattern.finditer(pattern_text):
            if not is_allowed_generic_command(
                command_line_tokens(
                    match.group(1),
                    inline_comments=supports_inline_hash_comments(
                        "console",
                        match.group(0).strip(),
                    ),
                    language="console",
                )
            ):
                return True
    if path.suffix in {".bash", ".sh"}:
        for line in text.splitlines():
            stripped = line.strip()
            if (
                stripped
                and not stripped.startswith("#")
                and not is_allowed_generic_command(
                    command_line_tokens(
                        stripped,
                        inline_comments=True,
                        language=path.suffix.lower().lstrip("."),
                    )
                )
            ):
                return True
    return False


def has_unparseable_source(text: str) -> bool:
    return any(
        line.strip() and not line.lstrip().startswith("#")
        for line in text.splitlines()
    )


def bundled_provider_violation(path: Path, text: str) -> bool:
    """Apply file-aware provider-independence policy to orchestrate content."""
    if PROVIDER_IMPLEMENTATION.search(text):
        return True
    first_line = text.splitlines()[0] if text.splitlines() else ""
    python_source = path.suffix.lower() in {".py", ".pyw"} or bool(
        re.match(r"^#!.*\bpython(?:3(?:\.\d+)*)?\b", first_line)
    )
    shell_source = (
        path.suffix.lower() in {".bash", ".fish", ".sh", ".zsh"}
        or bool(
            re.match(
                r"^#!.*(?:\b(?:ba|z|k)?sh\b|/bin/env sh\b)",
                first_line,
            )
        )
    )
    if python_source:
        parsed = python_implementation_violation(text)
        return has_unparseable_source(text) if parsed is None else parsed
    if shell_source:
        for line in text.splitlines():
            stripped = line.strip()
            if (
                stripped
                and not stripped.startswith("#")
                and not is_allowed_generic_command(
                    command_line_tokens(
                        stripped,
                        inline_comments=True,
                        language=path.suffix.lower().lstrip("."),
                    )
                )
            ):
                return True
        return False
    if first_line.startswith("#!"):
        return has_unparseable_source("\n".join(text.splitlines()[1:]))
    if path.suffix.lower() in DECLARATIVE_TEXT_SUFFIXES:
        return structured_command_violation(text, path)
    return has_unparseable_source(text)


def violation(rule: str, path: Path) -> Dict[str, str]:
    return {"rule": rule, "path": path.as_posix()}


def scan_text(path: Path, text: str) -> List[Dict[str, str]]:
    """Return sanitized rule identifiers for unsafe public content."""
    violations = []
    for rule, pattern in SECURITY_PATTERNS:
        if pattern.search(text):
            violations.append(violation(rule, path))
    if (
        len(path.parts) >= 2
        and path.parts[0:2] == ("skills", "orchestrate")
        and bundled_provider_violation(path, text)
    ):
        violations.append(violation("bundled-provider-integration", path))
    return violations


def text_files(skill: Path) -> Iterable[Tuple[Path, Optional[str]]]:
    for path in sorted(skill.rglob("*")):
        if (
            path.is_file() and "__pycache__" not in path.parts
        ):
            content = path.read_bytes()
            if b"\x00" in content:
                yield path, None
                continue
            try:
                text = content.decode("utf-8")
            except UnicodeDecodeError:
                yield path, None
                continue
            yield path, text


def frontmatter(path: Path) -> Optional[Dict[str, str]]:
    if not path.is_file():
        return None
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        return None
    try:
        end = lines.index("---", 1)
    except ValueError:
        return None
    values = {}
    for line in lines[1:end]:
        match = re.match(r"^(name|description):\s*(.+?)\s*$", line)
        if match:
            values[match.group(1)] = match.group(2).strip("\"'")
    return values


def validate_skill(root: Path, skill: Path) -> List[Dict[str, str]]:
    relative_skill = skill.relative_to(root)
    violations = []
    entrypoint = skill / "SKILL.md"
    metadata = skill / "agents" / "openai.yaml"
    if not entrypoint.is_file():
        return [violation("metadata", relative_skill / "SKILL.md")]

    values = frontmatter(entrypoint)
    if not values or values.get("name") != skill.name:
        violations.append(violation("metadata", entrypoint.relative_to(root)))
    elif not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", skill.name):
        violations.append(violation("metadata", entrypoint.relative_to(root)))
    if not values or not values.get("description"):
        violations.append(violation("metadata", entrypoint.relative_to(root)))

    if not metadata.is_file():
        violations.append(violation("metadata", metadata.relative_to(root)))
    else:
        metadata_text = metadata.read_text(encoding="utf-8")
        for required in (
            "interface:",
            "display_name:",
            "short_description:",
            "default_prompt:",
        ):
            if required not in metadata_text:
                violations.append(violation("metadata", metadata.relative_to(root)))
                break

    for path, text in text_files(skill):
        relative_path = path.relative_to(root)
        if text is None:
            violations.append(violation("unscannable-binary", relative_path))
        else:
            violations.extend(scan_text(relative_path, text))
    return violations


def validate_documentation(root: Path) -> List[Dict[str, str]]:
    readme = root / "README.md"
    orchestrate = root / "skills" / "orchestrate" / "SKILL.md"
    if not readme.is_file() or not orchestrate.is_file():
        return [violation("documentation", Path("README.md"))]
    public_docs = readme.read_text(encoding="utf-8").lower()
    skill_docs = orchestrate.read_text(encoding="utf-8").lower()
    concepts = (
        "first run",
        "coordination boundary",
        "durable",
        "registry",
        "approval",
    )
    violations = [
        violation("documentation", Path("README.md"))
        for concept in concepts
        if concept not in public_docs
    ]
    normalized_skill_docs = " ".join(skill_docs.split())
    if not (
        "authority home's instructions" in normalized_skill_docs
        and "orchestration registry" in skill_docs
    ):
        violations.append(
            violation(
                "configured-integration-resolution",
                Path("skills/orchestrate/SKILL.md"),
            )
        )
    return violations


def validate_coverage(
    root: Path, coverage_path: Path
) -> Tuple[List[int], List[Dict[str, str]]]:
    violations = []
    try:
        coverage = json.loads(coverage_path.read_text(encoding="utf-8"))
        areas = coverage["areas"]
    except (KeyError, OSError, TypeError, ValueError):
        return [], [violation("prd-coverage", coverage_path.relative_to(root))]

    stories = [story for area in areas for story in area.get("user_stories", [])]
    if sorted(stories) != list(range(1, 76)) or len(stories) != len(set(stories)):
        violations.append(violation("prd-coverage", coverage_path.relative_to(root)))

    scenario_source = (root / "tests" / "test_orchestrate_scenarios.py").read_text(
        encoding="utf-8"
    )
    scenario_names = set(
        re.findall(
            r"^\s+def (test_[a-z0-9_]+)\(",
            scenario_source,
            re.MULTILINE,
        )
    )
    referenced_scenarios = {
        name for area in areas for name in area.get("scenario_tests", [])
    }
    if not referenced_scenarios or not referenced_scenarios.issubset(scenario_names):
        violations.append(violation("prd-coverage", coverage_path.relative_to(root)))

    publication_checks = {
        name for area in areas for name in area.get("publication_checks", [])
    }
    if publication_checks != REQUIRED_PUBLICATION_CHECKS:
        violations.append(violation("prd-coverage", coverage_path.relative_to(root)))

    publication_source = (
        root / "tests" / "test_orchestrate_publication.py"
    ).read_text(encoding="utf-8")
    publication_names = set(
        re.findall(
            r"^\s+def (test_[a-z0-9_]+)\(",
            publication_source,
            re.MULTILINE,
        )
    )
    referenced_publication_tests = {
        name for area in areas for name in area.get("publication_tests", [])
    }
    if (
        not referenced_publication_tests
        or not referenced_publication_tests.issubset(publication_names)
    ):
        violations.append(violation("prd-coverage", coverage_path.relative_to(root)))

    if (
        "subprocess.run" not in scenario_source
        or "TRACER = ROOT" not in scenario_source
    ):
        violations.append(
            violation(
                "single-high-level-seam",
                Path("tests/test_orchestrate_scenarios.py"),
            )
        )
    return sorted(stories), violations


def cleanliness_violations(root: Path) -> List[Dict[str, str]]:
    completed = subprocess.run(
        ["git", "-C", str(root), "status", "--porcelain", "--untracked-files=all"],
        capture_output=True,
        check=False,
        text=True,
    )
    if completed.returncode != 0 or completed.stdout.strip():
        return [violation("repository-cleanliness", Path("."))]
    return []


def validate(
    root: Path,
    coverage_path: Optional[Path],
    require_clean: bool = False,
) -> Dict[str, object]:
    skills_root = root / "skills"
    skills = (
        sorted(path for path in skills_root.iterdir() if path.is_dir())
        if skills_root.is_dir()
        else []
    )
    violations = []
    for skill in skills:
        violations.extend(validate_skill(root, skill))
    violations.extend(validate_documentation(root))

    stories = []
    if coverage_path is not None:
        stories, coverage_violations = validate_coverage(root, coverage_path)
        violations.extend(coverage_violations)
    if require_clean:
        violations.extend(cleanliness_violations(root))

    unique_violations = sorted(
        {json.dumps(item, sort_keys=True) for item in violations}
    )
    return {
        "skills": [skill.name for skill in skills],
        "installable_names": [
            skill.name
            for skill in skills
            if (frontmatter(skill / "SKILL.md") or {}).get("name") == skill.name
        ],
        "prd_user_stories": stories,
        "violations": [json.loads(item) for item in unique_violations],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--coverage", type=Path)
    parser.add_argument("--require-clean", action="store_true")
    arguments = parser.parse_args()

    root = arguments.root.resolve()
    coverage = arguments.coverage.resolve() if arguments.coverage else None
    report = validate(root, coverage, require_clean=arguments.require_clean)
    json.dump(report, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    raise SystemExit(1 if report["violations"] else 0)


if __name__ == "__main__":
    main()
