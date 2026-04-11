# Installation Guide

This guide covers how to install the skills and agents from this toolkit into your Claude Code environment.

## Directory Structure

Claude Code looks for skills and agents in two locations:

| Scope | Skills Path | Agents Path |
|-------|------------|-------------|
| **Global** (all projects) | `~/.claude/skills/` | `~/.claude/agents/` |
| **Project** (single project) | `<project>/.claude/skills/` | `<project>/.claude/agents/` |

Use global installation if you work on multiple WooCommerce projects. Use project-level if you want the tools scoped to a specific plugin repo.

## Step 1: Clone the Repository

```bash
git clone https://github.com/Automattic/claude-woocommerce-toolkit.git
cd claude-woocommerce-toolkit
```

## Step 2: Install the Skill

The WooCommerce Plugin Dev skill is a directory containing `SKILL.md`, reference docs, and evals. Copy the entire directory:

```bash
# Global
mkdir -p ~/.claude/skills
cp -r skills/woocommerce-plugin-dev ~/.claude/skills/

# OR project-level
mkdir -p /path/to/your/project/.claude/skills
cp -r skills/woocommerce-plugin-dev /path/to/your/project/.claude/skills/
```

### Verify the Skill

Start a Claude Code session and try a trigger phrase:

```
> I want to build a WooCommerce shipping plugin
```

Claude should begin the Project Discovery interview from Phase 1 of the skill, asking about your target market, plugin scope, technical requirements, etc.

## Step 3: Install the Agents

Copy the agent definition files:

```bash
# Global
mkdir -p ~/.claude/agents
cp agents/woocommerce-ux-reviewer.md ~/.claude/agents/
cp agents/code-reviewer.md ~/.claude/agents/

# OR project-level
mkdir -p /path/to/your/project/.claude/agents
cp agents/*.md /path/to/your/project/.claude/agents/
```

### Verify the Agents

The **UX reviewer** agent triggers when you complete UX-critical work or explicitly request a review:

```
> Can you review the payment settings page I just built?
```

The **code reviewer** agent triggers after completing a chunk of code:

```
> I've finished the REST API endpoint, please review it
```

Both agents should announce themselves and follow their structured review methodology.

## Step 4: Agent Memory (Optional)

Both agents support persistent memory — they remember patterns, conventions, and feedback across conversations. The memory directories are created automatically on first use:

- `~/.claude/agent-memory/woocommerce-ux-reviewer/`
- `~/.claude/agent-memory/code-reviewer/`

No setup required. The agents will create these directories when they first need to save a memory.

## Updating

To update to the latest version:

```bash
cd claude-woocommerce-toolkit
git pull origin main
```

Then re-copy the files to your installation location. Your agent memory is stored separately and won't be affected by updates.

## Symlink Alternative

If you prefer to stay in sync with the repo without re-copying, use symlinks:

```bash
# Skill (symlink the directory)
ln -sf "$(pwd)/skills/woocommerce-plugin-dev" ~/.claude/skills/woocommerce-plugin-dev

# Agents (symlink individual files)
ln -sf "$(pwd)/agents/woocommerce-ux-reviewer.md" ~/.claude/agents/woocommerce-ux-reviewer.md
ln -sf "$(pwd)/agents/code-reviewer.md" ~/.claude/agents/code-reviewer.md
```

Then a `git pull` automatically updates your installation.

## Troubleshooting

**Skill not triggering?**
- Ensure the file is at `~/.claude/skills/woocommerce-plugin-dev/SKILL.md` (the `SKILL.md` filename is required)
- Check that the `references/` directory is alongside `SKILL.md`

**Agent not available?**
- Agent files must have a `.md` extension
- Check that the YAML frontmatter at the top of each agent file is valid
- Restart your Claude Code session after adding new agents

**Memory not persisting?**
- Ensure `~/.claude/agent-memory/` is writable
- The agents create their subdirectories on first use
