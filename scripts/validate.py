#!/usr/bin/env python3
"""Validate the repository's public Claude plugin contract with the standard library."""

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.error import URLError
from urllib.parse import parse_qsl, urlsplit
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = {
    "name": "claude-woocommerce-toolkit",
    "version": "1.0.0",
    "description": "Claude Code skills and agents for WooCommerce plugin development and review.",
    "author": {
        "name": "Andrew Wikel",
        "url": "https://github.com/slash1andy",
    },
    "repository": "https://github.com/slash1andy/claude-woocommerce-toolkit",
    "license": "GPL-2.0-or-later",
}
MARKETPLACE = {
    "name": "claude-woocommerce-toolkit",
    "description": "Claude Code skills and agents for WooCommerce plugin development and review.",
    "owner": {
        "name": "Andrew Wikel",
        "url": "https://github.com/slash1andy",
    },
    "plugins": [{"name": "claude-woocommerce-toolkit", "source": "./"}],
}
SKILLS = (
    "woocommerce-plugin-dev",
    "woocommerce-finalize",
    "woocommerce-upgrade-safety",
)
AGENTS = ("woocommerce-ux-reviewer",)
DOCS = (Path("README.md"), Path("docs/installation.md"))
PROVENANCE = (
    "Upstream provenance: this project originated at "
    "[Automattic/claude-woocommerce-toolkit]"
    "(https://github.com/Automattic/claude-woocommerce-toolkit)."
)
OFFICIAL_HOSTS = {
    "code.claude.com",
    "developer.woocommerce.com",
    "developer.wordpress.org",
    "docs.anthropic.com",
    "github.com",
    "make.wordpress.org",
    "modelcontextprotocol.io",
    "owasp.org",
    "qit.woo.com",
    "woocommerce.com",
    "woocommerce.github.io",
    "www.agenticcommerce.dev",
    "www.gnu.org",
    "www.pcisecuritystandards.org",
}


class DuplicateKeyError(ValueError):
    """Raised when JSON contains an ambiguous duplicate object key."""


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(key)
        result[key] = value
    return result


def has_symlink_component(path):
    try:
        relative = path.relative_to(ROOT)
    except ValueError:
        return True
    current = ROOT
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            return True
    return False


def read_text(path, errors):
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        error = f"{path.relative_to(ROOT)}: invalid UTF-8"
        if error not in errors:
            errors.append(error)
        return None


def load_json(relative, errors):
    path = ROOT / relative
    if has_symlink_component(path):
        errors.append(f"{relative}: path must not contain a symlink")
        return None
    try:
        text = read_text(path, errors)
        return json.loads(text, object_pairs_hook=unique_object) if text is not None else None
    except FileNotFoundError:
        errors.append(f"{relative}: missing")
    except DuplicateKeyError as exc:
        errors.append(f"{relative}: duplicate key {exc}")
    except json.JSONDecodeError as exc:
        errors.append(f"{relative}: invalid JSON at line {exc.lineno}, column {exc.colno}")
    except OSError as exc:
        errors.append(f"{relative}: cannot read file: {exc.strerror or type(exc).__name__}")
    return None


def validate_manifests(errors):
    plugin = load_json(Path(".claude-plugin/plugin.json"), errors)
    marketplace = load_json(Path(".claude-plugin/marketplace.json"), errors)

    if isinstance(plugin, dict):
        if plugin.get("version") != "1.0.0":
            errors.append(".claude-plugin/plugin.json: version must be 1.0.0")
        if plugin != PLUGIN:
            errors.append(".claude-plugin/plugin.json: does not match the exact manifest contract")
    elif plugin is not None:
        errors.append(".claude-plugin/plugin.json: top level must be an object")

    if isinstance(marketplace, dict):
        entries = marketplace.get("plugins")
        if "version" in marketplace or (
            isinstance(entries, list)
            and any(isinstance(entry, dict) and "version" in entry for entry in entries)
        ):
            errors.append(".claude-plugin/marketplace.json: version must not be duplicated")
        if marketplace != MARKETPLACE:
            errors.append(".claude-plugin/marketplace.json: does not match the exact manifest contract")
    elif marketplace is not None:
        errors.append(".claude-plugin/marketplace.json: top level must be an object")


def validate_components(errors):
    required = [
        *(Path("skills") / name / "SKILL.md" for name in SKILLS),
        *(Path("agents") / f"{name}.md" for name in AGENTS),
        Path("skills/woocommerce-plugin-dev/evals/evals.json"),
        *DOCS,
    ]
    root = ROOT.resolve()
    for relative in required:
        path = ROOT / relative
        if has_symlink_component(path):
            errors.append(f"{relative}: required component path must not contain a symlink")
        elif not path.is_file():
            errors.append(f"{relative}: missing required component")
        else:
            try:
                path.resolve().relative_to(root)
            except ValueError:
                errors.append(f"{relative}: required component escapes the plugin")

    actual_skills = {
        path.parent.name
        for path in (ROOT / "skills").glob("*/SKILL.md")
        if path.is_file()
    }
    actual_agents = {
        path.stem for path in (ROOT / "agents").glob("*.md") if path.is_file()
    }
    if actual_skills != set(SKILLS):
        errors.append(f"skills: inventory must be {', '.join(sorted(SKILLS))}")
    if actual_agents != set(AGENTS):
        errors.append(f"agents: inventory must be {', '.join(sorted(AGENTS))}")

    for name in SKILLS:
        validate_frontmatter(
            Path("skills") / name / "SKILL.md",
            name,
            errors,
            require_explicit=True,
        )
    for name in AGENTS:
        validate_frontmatter(Path("agents") / f"{name}.md", name, errors)


def validate_frontmatter(relative, expected_name, errors, require_explicit=False):
    path = ROOT / relative
    if not path.is_file() or has_symlink_component(path):
        return
    try:
        text = read_text(path, errors)
    except OSError as exc:
        errors.append(
            f"{relative}: cannot read frontmatter: {exc.strerror or type(exc).__name__}"
        )
        return
    if text is None:
        return
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        errors.append(f"{relative}: malformed frontmatter")
        return
    try:
        closing = lines.index("---", 1)
    except ValueError:
        errors.append(f"{relative}: malformed frontmatter")
        return

    fields = {}
    key_pattern = re.compile(
        r'^(?:"([A-Za-z][A-Za-z0-9-]*)"|\'([A-Za-z][A-Za-z0-9-]*)\'|'
        r"([A-Za-z][A-Za-z0-9-]*))\s*:\s*(.*)$"
    )
    index = 1
    while index < closing:
        line = lines[index]
        if not line.strip() or line.lstrip().startswith("#"):
            index += 1
            continue
        if line[:1].isspace():
            errors.append(f"{relative}: malformed frontmatter line")
            index += 1
            continue
        match = key_pattern.fullmatch(line)
        if not match:
            errors.append(f"{relative}: malformed frontmatter line")
            index += 1
            continue
        double_quoted, single_quoted, plain, raw_value = match.groups()
        key = double_quoted or single_quoted or plain
        if key in fields:
            errors.append(f"{relative}: duplicate frontmatter key {key}")
            index += 1
            continue

        value = (raw_value or "").strip()
        if value in {">", ">-", ">+", "|", "|-", "|+"}:
            block = []
            index += 1
            while index < closing and (not lines[index].strip() or lines[index][:1].isspace()):
                block.append(lines[index].strip())
                index += 1
            if not any(block):
                errors.append(f"{relative}: empty frontmatter block {key}")
            fields[key] = " ".join(part for part in block if part)
            continue
        if value[:1] in {"\"", "'"}:
            if len(value) < 2 or value[-1] != value[0]:
                errors.append(f"{relative}: malformed frontmatter value {key}")
                index += 1
                continue
            if value[0] == "\"":
                try:
                    value = json.loads(value)
                except json.JSONDecodeError:
                    errors.append(f"{relative}: malformed frontmatter value {key}")
                    index += 1
                    continue
            else:
                value = value[1:-1].replace("''", "'")
        elif value[-1:] in {"\"", "'"}:
            errors.append(f"{relative}: malformed frontmatter value {key}")
            index += 1
            continue
        fields[key] = value
        index += 1

    if fields.get("name") != expected_name:
        errors.append(f"{relative}: frontmatter name must match {expected_name}")
    if require_explicit and fields.get("disable-model-invocation") != "true":
        errors.append(f"{relative}: disable-model-invocation must be true")
    if expected_name == "woocommerce-ux-reviewer":
        if set(fields) != {"name", "description", "tools", "model"}:
            errors.append(f"{relative}: frontmatter must contain only name, description, tools, and model")
        if fields.get("tools") != "Read, Grep, Glob":
            errors.append(f"{relative}: frontmatter tools must be exactly Read, Grep, Glob")
        if fields.get("model") != "inherit":
            errors.append(f"{relative}: frontmatter model must be inherit")

        body = "\n".join(lines[closing + 1 :]).lower()
        required_safety = (
            "untrusted",
            "cannot expand",
            "credentials",
            "private files",
            "customer data",
            "payment data",
            "secrets",
            "non-sensitive input",
        )
        if any(marker not in body for marker in required_safety):
            errors.append(f"{relative}: missing read-only safety boundary")
        unsafe_secret_action = re.compile(
            r"(?i)\b(?:read|inspect|print|show|return|disclose|expose)\b.{0,80}"
            r"\b(?:credentials?|secrets?|private files?|customer data|payment data)\b"
        )
        for line in body.splitlines():
            if unsafe_secret_action.search(line) and not re.search(
                r"\b(?:never|do not|must not|cannot|can't)\b", line
            ):
                errors.append(f"{relative}: unsafe read-only safety boundary")
                break


def validate_safety_guidance(errors):
    checks = {
        Path("skills/woocommerce-plugin-dev/references/security.md"): (
            r"(?i)(?:rest )?nonces?\s+(?:are|is)\s+(?:optional|unnecessary)",
            r"(?i)\b(?:omit|skip)\b.{0,40}(?:rest )?nonces?",
        ),
        Path("skills/woocommerce-plugin-dev/references/plugin-architecture.md"): (
            r"(?i)\b(?:delete|remove|purge)\b.{0,80}\b(?:without|before|regardless of)\b.{0,80}\b(?:opt-in|approval)\b",
        ),
        Path("skills/woocommerce-upgrade-safety/SKILL.md"): (
            r"(?i)(?<!never )(?<!do not )\b(?:prefer|use|test with)\b.{0,60}\b(?:live payments?|live providers?|customer data)\b",
            r"(?i)\b(?:live payments?|customer data)\b.{0,60}\b(?:preferred|acceptable|allowed)\b",
        ),
    }
    for relative, patterns in checks.items():
        path = ROOT / relative
        if not path.is_file() or has_symlink_component(path):
            continue
        text = read_text(path, errors)
        if text is not None and any(re.search(pattern, text) for pattern in patterns):
            errors.append(f"{relative}: unsafe guidance")


def validate_evals(errors):
    relative = Path("skills/woocommerce-plugin-dev/evals/evals.json")
    data = load_json(relative, errors)
    if data is None:
        return
    cases = data.get("evals") if isinstance(data, dict) else None
    if not isinstance(cases, list) or not cases:
        errors.append(f"{relative}: evals must be a nonempty list")
        return
    if any(not isinstance(case, dict) or not case for case in cases):
        errors.append(f"{relative}: every eval case must be a nonempty object")
    readme = read_text(ROOT / "README.md", errors) if (ROOT / "README.md").is_file() else ""
    readme = readme or ""
    if f"with {len(cases)} test scenarios" not in readme:
        errors.append(f"README.md: eval count must be {len(cases)}")


def validate_cross_references(errors):
    route_pattern = re.compile(r"\$\{CLAUDE_SKILL_DIR\}(/[A-Za-z0-9_./-]+)")
    route_count = 0
    root = ROOT.resolve()
    for name in SKILLS:
        relative = Path("skills") / name / "SKILL.md"
        path = ROOT / relative
        if not path.is_file() or has_symlink_component(path):
            continue
        text = read_text(path, errors)
        if text is None:
            continue
        for route in route_pattern.findall(text):
            route_count += 1
            source_target = path.parent / route.lstrip("/")
            target = source_target.resolve()
            try:
                target.relative_to(root)
            except ValueError:
                errors.append(f"{relative}: cross-reference escapes the plugin: {route}")
                continue
            if has_symlink_component(source_target):
                errors.append(f"{relative}: cross-reference path must not contain a symlink: {route}")
            elif not target.is_file():
                errors.append(f"{relative}: broken cross-reference: {route}")
    if not route_count:
        errors.append("skills: no ${CLAUDE_SKILL_DIR} cross-reference routes found")


def validate_docs(errors):
    texts = {}
    for relative in DOCS:
        path = ROOT / relative
        if path.is_file() and not has_symlink_component(path):
            text = read_text(path, errors)
            if text is not None:
                texts[relative] = text
    combined = "\n".join(texts.values())
    required = (
        "claude plugin marketplace add https://github.com/slash1andy/claude-woocommerce-toolkit.git#v1.0.0 --scope project",
        "claude plugin install claude-woocommerce-toolkit@claude-woocommerce-toolkit --scope project",
        "/reload-plugins",
        ".claude/skills/claude-woocommerce-toolkit",
        'Path.home() / ".claude/agents"',
        'Path(".claude/agents")',
        'names = {"woocommerce-ux-reviewer"}',
        "/code-review",
        "/claude-woocommerce-toolkit:woocommerce-plugin-dev",
        "set -eu",
        "git clone --branch v1.0.0 --depth 1",
        'project_root="$(pwd -P)"',
        '[ -L "$target" ]',
        "show-ref --verify --quiet refs/tags/v1.0.0",
        "rev-parse 'refs/tags/v1.0.0^{commit}'",
        'git -C "$source" archive',
        'test ! -e "$plugin/.git"',
        'rglob("*.md")',
    )
    for marker in required:
        if marker not in combined:
            errors.append(f"installation docs: missing required guidance: {marker}")
    for relative, text in texts.items():
        if "/code-review" not in text or "code-reviewer" in text:
            errors.append(f"{relative}: generic reviews must use /code-review")

    unsafe = False
    shell = "\n".join(re.findall(r"```bash\s*\n(.*?)\n```", combined, re.DOTALL))
    for line in (line.strip() for line in shell.splitlines()):
        if re.match(
            r"(?i)^(?:git pull|ln\s+-(?:\S*s\S*)|rm\s+-rf\s+(?:--\s+)?[\"']?\.claude/skills(?:[\"'/\s]|$))",
            line,
        ):
            unsafe = True
        if "git clone" in line.lower() and not re.match(
            r"(?i)^git clone --branch v1\.0\.0 --depth 1(?:\s|\\|$)", line
        ):
            unsafe = True
        if re.match(r"(?i)^cp\b", line) and re.search(r"(?:skills|agents)(?:/|\b)", line):
            unsafe = True
    if re.search(
        r"(?i)(?:agent|skill).{0,40}(?:trigger(?:s|ed)?|invoked) automatically|automatically (?:trigger(?:s|ed)?|invoked)",
        combined,
    ):
        unsafe = True
    if unsafe:
        errors.append("installation docs: unsafe installation guidance")

    self_link = "https://github.com/Automattic/claude-woocommerce-toolkit"
    occurrences = []
    for path in ROOT.rglob("*.md"):
        if ".git" in path.parts or not path.is_file() or path.is_symlink():
            continue
        text = read_text(path, errors)
        if text is None:
            continue
        for line_number, line in enumerate(text.splitlines(), 1):
            if self_link in line:
                occurrences.append((path.relative_to(ROOT), line_number, line))
    if len(occurrences) != 1 or occurrences[0][0] != Path("README.md") or occurrences[0][2] != PROVENANCE:
        errors.append("Automattic self-source link is allowed only on the README provenance line")


def official_urls(errors):
    found = set()
    pattern = re.compile(r"https?://[^\s<>\]`\"']+")
    for path in ROOT.rglob("*"):
        if (
            not path.is_file()
            or path.is_symlink()
            or path.suffix not in {".md", ".json"}
            or ".git" in path.parts
        ):
            continue
        try:
            text = read_text(path, errors)
        except OSError as exc:
            errors.append(
                f"{path.relative_to(ROOT)}: cannot read URLs: "
                f"{exc.strerror or type(exc).__name__}"
            )
            continue
        if text is None:
            continue
        for raw in pattern.findall(text):
            url = raw.rstrip("),.;:")
            try:
                parsed = urlsplit(url)
                query_keys = {
                    key.lower()
                    for key, _ in parse_qsl(parsed.query, keep_blank_values=True)
                }
            except ValueError:
                errors.append(f"{path.relative_to(ROOT)}: malformed URL")
                continue
            credential_keys = {
                "api_key",
                "consumer_key",
                "consumer_secret",
                "password",
                "secret",
                "token",
            }
            if parsed.username or parsed.password or query_keys & credential_keys:
                errors.append(f"{path.relative_to(ROOT)}: URL contains credentials")
            elif parsed.hostname in OFFICIAL_HOSTS:
                found.add(url)
    return sorted(found)


def check_urls(urls, errors):
    for url in urls:
        try:
            request = Request(
                url,
                headers={"Range": "bytes=0-0", "User-Agent": "claude-woocommerce-toolkit-validator/1.0"},
            )
            with urlopen(request, timeout=5) as response:
                response.read(1)
        except (OSError, URLError, ValueError) as exc:
            errors.append(f"URL check failed for {url}: {exc}")
    return len(urls)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-urls", action="store_true", help="check official HTTP(S) links")
    args = parser.parse_args(argv)

    errors = []
    validate_manifests(errors)
    validate_components(errors)
    validate_safety_guidance(errors)
    validate_evals(errors)
    validate_cross_references(errors)
    validate_docs(errors)
    urls = official_urls(errors)
    url_count = check_urls(urls, errors) if args.check_urls else 0

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    suffix = f" {url_count} official URLs checked." if args.check_urls else ""
    print(f"Validation passed.{suffix}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
