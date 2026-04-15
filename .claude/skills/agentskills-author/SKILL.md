---
name: agentskills-author
description: Guide for creating Agent Skills for Claude Code, Claude.ai, and OpenCode. Use when the user wants to create a new skill, needs help with SKILL.md format, skill structure, best practices, or validation. Covers YAML frontmatter, directory structure, examples, and troubleshooting.
license: MIT
metadata:
  author: Assistant
  version: "1.0"
  tags: [agentskills, claude-code, skills, skill-creation, claude-ai]
---

# Agent Skills Author Guide

This skill helps you create **Agent Skills** — reusable capability packages for AI agents like Claude Code, Claude.ai, and OpenCode.

## What are Agent Skills?

Agent Skills are folders containing instructions, scripts, and resources that agents can discover and use to perform tasks more accurately and efficiently. They provide:

- **Domain expertise**: Specialized knowledge for specific tasks
- **New capabilities**: Extended functionality beyond base training
- **Repeatable workflows**: Consistent, auditable processes
- **Portability**: Use the same skill across different agent products

## Official Resources

- **Specification**: https://agentskills.io/specification
- **Quickstart**: https://agentskills.io/skill-creation/quickstart
- **Best Practices**: https://agentskills.io/skill-creation/best-practices
- **GitHub**: https://github.com/agentskills/agentskills

## Skill Directory Structure

```
skill-name/
├── SKILL.md              # REQUIRED: Metadata + instructions
├── scripts/              # Optional: Executable code
│   ├── setup.sh
│   └── validate.py
├── references/           # Optional: Documentation
│   └── api-docs.pdf
├── assets/               # Optional: Templates, resources
│   └── template.json
└── README.md             # Optional: Human-readable info
```

## SKILL.md Format

The `SKILL.md` file is the heart of every skill. It contains:

1. **YAML Frontmatter** (required metadata)
2. **Markdown Body** (instructions and examples)

### Minimal SKILL.md Template

```markdown
---
name: my-skill
description: What this skill does and when to use it.
---

# My Skill

Instructions for the agent go here...
```

### Complete SKILL.md Template

```markdown
---
name: my-awesome-skill
description: |
  A detailed description of what this skill does.
  Include specific keywords to help agents identify
  when to use this skill (e.g., "Use when working with X").
license: MIT
compatibility: |
  Requires Python 3.8+, Node.js 16+, or Docker.
  Tested on macOS, Linux, and Windows.
metadata:
  author: your-name
  version: "1.0.0"
  tags: [tag1, tag2, tag3]
allowed-tools: Read Edit Bash
---

# My Awesome Skill

## Overview

Brief explanation of what this skill enables.

## When to Use

- Use case 1: Description
- Use case 2: Description
- Use case 3: Description

## Installation

```bash
# Installation commands
pip install my-package
```

## Basic Usage

### Example 1: Simple Task

```python
# Code example
print("Hello, World!")
```

### Example 2: Advanced Task

```python
# More complex example
import my_package
result = my_package.do_something()
```

## Common Patterns

### Pattern Name

Description of when and how to use this pattern.

```python
# Example code
```

## Troubleshooting

### Problem: Description

**Solution**: Steps to resolve

## Resources

- Documentation: https://example.com/docs
- GitHub: https://github.com/example/repo
```

## Frontmatter Fields Reference

| Field | Required | Description | Constraints |
|-------|----------|-------------|-------------|
| `name` | Yes | Skill identifier | 1-64 chars, lowercase a-z, numbers, hyphens only |
| `description` | Yes | What the skill does | 1-1024 chars, include use case keywords |
| `license` | No | License name or file | Any SPDX identifier or filename |
| `compatibility` | No | Environment requirements | Max 500 chars |
| `metadata` | No | Arbitrary key-value pairs | Any valid YAML mapping |
| `allowed-tools` | No | Pre-approved tools | Space-separated list (experimental) |

### Name Field Rules

✅ **Valid:**
- `pdf-processing`
- `data-analysis`
- `code-review`
- `my-skill-v2`

❌ **Invalid:**
- `PDF-Processing` (uppercase not allowed)
- `-pdf` (cannot start with hyphen)
- `pdf--processing` (no consecutive hyphens)
- `my skill` (spaces not allowed)

### Description Best Practices

**Good description:**
```yaml
description: |
  Extracts text and tables from PDF files, fills PDF forms,
  and merges multiple PDFs. Use when working with PDF documents
  or when the user mentions PDFs, forms, or document extraction.
```

**Poor description:**
```yaml
description: PDF tools  # Too vague, no use case keywords
```

## Writing Effective Skill Instructions

### 1. Start with Context

Explain what the skill enables before diving into details.

```markdown
## What is X?

X is a library that does Y. This skill helps you:
- Do A efficiently
- Handle B correctly
- Avoid common pitfalls with C
```

### 2. Provide Clear Examples

Include working code examples for common tasks:

```markdown
### Reading a File

```python
with open('file.txt', 'r') as f:
    content = f.read()
```
```

### 3. Show Common Patterns

Document patterns agents will use repeatedly:

```markdown
## Common Patterns

### Pattern: Batch Processing

Use when processing multiple items:

```python
for item in items:
    process(item)
```
```

### 4. Include Error Handling

Show how to handle common errors:

```markdown
### Handling Missing Files

```python
import os

if not os.path.exists(path):
    print(f"File not found: {path}")
    return
```
```

### 5. Add Troubleshooting Section

Help agents recover from common issues:

```markdown
## Troubleshooting

### Error: "Module not found"

**Cause**: Package not installed
**Solution**: Run `pip install package-name`
```

## Skill Categories & Examples

### 1. Library Integration Skills

For working with specific libraries:

```markdown
---
name: pandas-guide
description: |
  Data manipulation with pandas. Use for DataFrame operations,
  data cleaning, filtering, grouping, merging, and analysis.
---

## Reading Data

```python
import pandas as pd

# From CSV
df = pd.read_csv('data.csv')

# From JSON
df = pd.read_json('data.json')
```

## Common Operations

### Filtering

```python
df_filtered = df[df['age'] > 18]
```

### Grouping

```python
df.groupby('category')['value'].sum()
```
```

### 2. Domain Expertise Skills

For specialized knowledge:

```markdown
---
name: regex-patterns
description: |
  Common regular expression patterns. Use when extracting data,
  validating input, or performing text transformations with regex.
---

## Common Patterns

### Email Validation

```python
import re

pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
re.match(pattern, email)
```

### Extract URLs

```python
pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
urls = re.findall(pattern, text)
```
```

### 3. Workflow Skills

For multi-step processes:

```markdown
---
name: git-workflow
description: |
  Standard Git workflows for feature branches, PRs, and releases.
  Use when creating branches, making commits, or managing releases.
---

## Feature Branch Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/my-feature
```

### 2. Make Changes and Commit

```bash
git add .
git commit -m "feat: add new feature"
```

### 3. Push and Create PR

```bash
git push -u origin feature/my-feature
```
```

## Installation Methods

### Claude Code

```bash
# Option 1: Direct folder
mkdir -p ~/.claude/skills/my-skill
cp SKILL.md ~/.claude/skills/my-skill/

# Option 2: Zip upload
zip -r my-skill.zip my-skill/
# Then upload via Settings > Capabilities > Skills
```

### Claude.ai (Web)

1. Create folder with `SKILL.md`
2. Zip the folder: `zip -r my-skill.zip my-skill/`
3. Go to Settings > Capabilities > Skills
4. Upload the zip file

### OpenCode

```bash
mkdir -p ~/.config/opencode/skills/my-skill
cp SKILL.md ~/.config/opencode/skills/my-skill/
```

## Testing Your Skill

### 1. Validate YAML Frontmatter

```bash
# Check YAML syntax
python3 -c "import yaml; yaml.safe_load(open('SKILL.md'))"
```

### 2. Test with Sample Queries

Ask the agent questions that should trigger your skill:

- "How do I do X with Y?" (should use your skill)
- "Help me set up Z" (should reference your skill)

### 3. Check Description Matching

Ensure your description includes keywords users might use:

| User Might Say | Include in Description |
|----------------|------------------------|
| "work with PDFs" | "Use when working with PDF files" |
| "database stuff" | "Use for database operations" |
| "clean data" | "Use for data cleaning and preprocessing" |

## Common Mistakes to Avoid

### ❌ Vague Descriptions

```yaml
# Bad - too generic
description: A skill for Python

# Good - specific with keywords
description: |
  Data validation with Pydantic models. Use when defining
  data schemas, validating API requests, or serializing data.
```

### ❌ Missing Use Case Keywords

```yaml
# Bad - no trigger words
description: This skill helps with SQLite

# Good - clear when to use
description: |
  SQLite database operations. Use when creating tables,
  running queries, or managing SQLite databases.
```

### ❌ Overly Long Instructions

Keep instructions focused. Use progressive disclosure:
- Start with basics
- Link to advanced topics
- Use collapsible sections if needed

### ❌ No Code Examples

Always include working examples:

```markdown
## Usage

```python
# Good: Complete, runnable example
import requests

response = requests.get('https://api.example.com')
data = response.json()
```
```

## Advanced Features

### Using Scripts Directory

For complex skills, add executable scripts:

```
my-skill/
├── SKILL.md
└── scripts/
    ├── setup.py      # One-time setup
    ├── validate.py   # Validation script
    └── helper.sh     # Shell helper
```

Reference in SKILL.md:

```markdown
## Setup

Run the setup script:

```bash
python scripts/setup.py
```
```

### Using References Directory

Include external documentation:

```
my-skill/
├── SKILL.md
└── references/
    └── api-reference.pdf
```

### Using Assets Directory

Include templates or resources:

```
my-skill/
├── SKILL.md
└── assets/
    └── config-template.json
```

## Skill Validation Checklist

Before publishing your skill, verify:

- [ ] `name` follows naming conventions (lowercase, hyphens)
- [ ] `description` is 1-1024 characters
- [ ] `description` includes use case keywords
- [ ] YAML frontmatter is valid
- [ ] Markdown body has clear instructions
- [ ] Code examples are tested and working
- [ ] Installation steps are included
- [ ] Troubleshooting section covers common issues
- [ ] Skill folder name matches `name` field

## Quick Reference Card

```markdown
---
name: {lowercase-with-hyphens}
description: |
  {What it does}. Use when {trigger condition 1},
  {trigger condition 2}, or {trigger condition 3}.
license: MIT
metadata:
  author: {your-name}
  version: "1.0.0"
---

# {Skill Name}

## Overview

{What this skill enables}

## Installation

```bash
{install commands}
```

## Basic Usage

```python
{simple example}
```

## Common Patterns

### {Pattern Name}

```python
{pattern example}
```

## Resources

- Docs: {url}
- Repo: {url}
```

## Example Skills Library

### sqlite-vec

```markdown
---
name: sqlite-vec
description: |
  Vector search with SQLite. Use when storing embeddings,
  performing similarity search, or building RAG applications.
---

# sqlite-vec

## Installation

```bash
pip install sqlite-vec
```

## Basic Usage

```python
import sqlite_vec
from sqlite_vec import serialize_float32

# Create virtual table
db.execute('''
    CREATE VIRTUAL TABLE vec_items USING vec0(
        item_id INTEGER PRIMARY KEY,
        embedding FLOAT[768]
    )
''')

# Insert vector
db.execute(
    "INSERT INTO vec_items VALUES (?, ?)",
    [1, serialize_float32(embedding)]
)

# KNN search
results = db.execute('''
    SELECT item_id, distance
    FROM vec_items
    WHERE embedding MATCH ? AND k = 10
    ORDER BY distance
''', [serialize_float32(query)]).fetchall()
```
```

### http-requests

```markdown
---
name: http-requests
description: |
  Making HTTP requests with requests/httpx. Use when calling APIs,
  fetching data, or working with web services.
---

# HTTP Requests

## GET Request

```python
import requests

response = requests.get('https://api.example.com/data')
data = response.json()
```

## POST Request

```python
response = requests.post(
    'https://api.example.com/users',
    json={'name': 'John', 'email': 'john@example.com'}
)
```

## With Authentication

```python
headers = {'Authorization': f'Bearer {token}'}
response = requests.get(url, headers=headers)
```
```

## Resources

- **Official Spec**: https://agentskills.io/specification
- **Best Practices**: https://agentskills.io/skill-creation/best-practices
- **Example Skills**: https://github.com/agentskills/agentskills/tree/main/examples
- **Community Discord**: https://discord.gg/MKPE9g8aUy
