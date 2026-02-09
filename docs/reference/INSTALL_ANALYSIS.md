# Installation Pattern Analysis: Ultimate Bug Scanner

## Overview

This document analyzes the installation approach used by `ultimate_bug_scanner`, focusing on their single-curl installation method and the techniques that make it effective.

## Core Installation Pattern

### The Single Curl Command

```bash
curl -fsSL "https://raw.githubusercontent.com/Dicklesworthstone/ultimate_bug_scanner/main/install.sh?$(date +%s)" | bash -s --
```

### Key Components Breakdown

#### 1. **Cache-Busting Query Parameter**
```bash
?$(date +%s)
```
- **Purpose**: Prevents browser/CDN caching of the install script
- **Why it matters**: Ensures users always get the latest version
- **Implementation**: Unix timestamp appended to URL
- **Alternative approaches**: Could use version tags, but timestamp is simpler for "always latest"

#### 2. **Curl Flags Explained**
```bash
curl -fsSL
```
- `-f` (--fail): Fail silently on HTTP errors (don't show HTML error pages)
- `-s` (--silent): Suppress progress meter and errors
- `-S` (--show-error): Show errors even in silent mode (though `-f` handles this)
- `-L` (--location): Follow redirects (important for GitHub raw URLs)

#### 3. **Bash Execution Pattern**
```bash
bash -s --
```
- `-s`: Read commands from stdin (the piped curl output)
- `--`: End of options, allows script to receive additional flags
- This pattern allows: `curl ... | bash -s -- --easy-mode`

## Advanced Installation Features

### 1. **Easy Mode (Zero-Interaction Install)**

```bash
bash -s -- --easy-mode
```

**What it does:**
- Auto-installs all dependencies without prompts
- Auto-detects and configures coding agents
- Accepts all default options
- Perfect for CI/CD and automated setups

**Key insight**: Provide both interactive (default) and non-interactive (flag) modes

### 2. **Dry Run Mode**

```bash
bash install.sh --dry-run
```

**Benefits:**
- Shows exactly what would be installed/modified
- No actual changes made
- Helps users understand impact before committing
- Useful for security audits

### 3. **Self-Test Capability**

```bash
bash install.sh --self-test
```

**Purpose:**
- Validates installation works correctly
- Runs smoke tests after install
- Exits non-zero if validation fails
- Critical for CI/CD validation

### 4. **Uninstall Support**

```bash
curl ... | bash -s -- --uninstall --non-interactive
```

**Key features:**
- Removes all installed components
- Cleans up configuration files
- Removes PATH modifications
- Non-interactive flag for automation

### 5. **Selective Feature Installation**

```bash
--skip-type-narrowing
--skip-typos
--skip-doctor
--skip-hooks
--no-path-modify
```

**Benefits:**
- Allows users to customize installation
- Skips features they don't need
- Reduces installation complexity
- Respects existing tooling

## Security Considerations

### 1. **Verification Options**

They provide multiple installation methods with varying security levels:

**Level 1: Basic (curled directly)**
```bash
curl ... | bash
```
- Fastest but least secure
- No verification

**Level 2: Verified (with checksums)**
```bash
export UBS_MINISIGN_PUBKEY="..."
curl ... verify.sh | bash
```
- Downloads and verifies SHA256SUMS
- Validates with minisign signatures
- More secure, but requires setup

**Level 3: Manual Review**
```bash
curl ... -o install.sh
less install.sh  # Review
bash install.sh
```
- Full transparency
- User can inspect before executing

### 2. **Supply Chain Security**

- Pinned SHA-256 checksums for all modules
- Module validation before execution
- Clear security documentation
- Optional integrity verification

## Installation Patterns to Adopt

### Pattern 1: Progressive Enhancement

```
Basic install (works everywhere)
  ↓
Easy mode (auto-detects and configures)
  ↓
Verified install (with signatures)
  ↓
Manual install (full control)
```

**Benefit**: Users can choose their comfort level

### Pattern 2: Environment Detection

Their installer:
- Detects existing tools (ripgrep, jq, etc.)
- Detects coding agents (Claude, Cursor, etc.)
- Detects system capabilities (Node.js, Python, etc.)
- Adapts installation based on findings

### Pattern 3: Post-Install Validation

```bash
# After install, automatically:
ubs doctor  # Validate environment
# Appends session summary
ubs sessions --entries 1  # View install log
```

**Benefits:**
- Immediate feedback on success/failure
- Diagnostic information stored
- Helps troubleshoot issues

### Pattern 4: Session Logging

- Stores install sessions to `~/.config/ubs/session.md`
- Includes readiness facts
- Allows troubleshooting later
- Can be shared for support

## Design Principles

### 1. **Zero Configuration**
- Works out of the box
- No mandatory config files
- Sensible defaults everywhere

### 2. **Graceful Degradation**
- Works with minimal dependencies
- Optional features enhance experience
- Doesn't fail if optional tools missing

### 3. **User Choice**
- Interactive by default
- Non-interactive mode available
- Selective feature installation
- Multiple installation methods

### 4. **Transparency**
- Dry-run shows all changes
- Clear documentation
- Optional script inspection
- Diagnostic commands

## Application to Guardian

### Current Guardian Installation

Guardian currently uses:
1. Source installation: `uv sync && uv pip install -e .`
2. Future pipx installation: `pipx install git-guardian`

### Potential Improvements

#### Option 1: Single-Curl Install Script

```bash
curl -fsSL "https://raw.githubusercontent.com/your-org/git-guardian/main/install.sh?$(date +%s)" | bash -s --
```

**What it would do:**
1. Detect Python/uv availability
2. Create virtual environment
3. Install Guardian and dependencies
4. Add to PATH (optional)
5. Run `guardian doctor` validation
6. Show next steps

**Benefits:**
- Lowers barrier to entry
- Single command vs. multiple steps
- Works across platforms (with uv installed)

#### Option 2: Easy Mode

```bash
curl ... | bash -s -- --easy-mode
```

**Would:**
- Auto-detect git repository
- Run `guardian init` automatically
- Install all harnesses
- Configure hooks
- Zero interaction

#### Option 3: Installation Modes

```bash
# Interactive (default)
curl ... | bash

# Non-interactive (CI-friendly)
curl ... | bash -s -- --non-interactive

# Dry run (preview changes)
curl ... | bash -s -- --dry-run

# Minimal (no hooks, no PATH changes)
curl ... | bash -s -- --minimal
```

## Implementation Considerations

### What to Install

1. **Guardian CLI** - Main command
2. **Dependencies** - Python packages via uv/pip
3. **Configuration** - Default `.guardian/config.yaml`
4. **Hooks** - Optional git hooks
5. **Harnesses** - Optional LLM tool configurations

### Detection Logic

Install script should detect:
- Python version (3.11+)
- uv availability (preferred) or pip
- Git repository status
- Existing Guardian installation
- LLM tools (Cursor, Claude Code, etc.)

### Post-Install Steps

1. Verify installation: `guardian --version`
2. Run diagnostics: `guardian doctor`
3. Show quick start instructions
4. Optionally run: `guardian init` if in git repo

### Uninstall Support

```bash
guardian uninstall
# or
curl ... | bash -s -- --uninstall
```

Should remove:
- Guardian binary/package
- Configuration files (with confirmation)
- Git hooks (if installed)
- PATH modifications

## Security Recommendations

1. **Provide verification method**
   - SHA256 checksums
   - GPG signatures (optional)
   - Clear documentation

2. **Enable manual review**
   ```bash
   curl ... -o install.sh
   cat install.sh  # Review
   bash install.sh
   ```

3. **Document security model**
   - What the script does
   - What it modifies
   - What permissions it needs

4. **Transparent dry-run**
   - Always show what will change
   - Allow preview before execution

## Example Guardian Install Script Structure

```bash
#!/usr/bin/env bash
set -euo pipefail

# Parse flags
EASY_MODE=false
DRY_RUN=false
NON_INTERACTIVE=false
MINIMAL=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --easy-mode) EASY_MODE=true ;;
        --dry-run) DRY_RUN=true ;;
        --non-interactive) NON_INTERACTIVE=true ;;
        --minimal) MINIMAL=true ;;
        --uninstall) UNINSTALL=true ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
    shift
done

# Detection
detect_python() { ... }
detect_uv() { ... }
detect_git() { ... }

# Installation
install_guardian() {
    if [[ "$DRY_RUN" == true ]]; then
        echo "Would install Guardian..."
        return
    fi
    # Actual installation
}

# Post-install
validate_installation() {
    if command -v guardian &> /dev/null; then
        guardian --version
        guardian doctor
    fi
}

# Main
main() {
    if [[ "${UNINSTALL:-false}" == true ]]; then
        uninstall_guardian
        exit 0
    fi

    install_guardian
    validate_installation
    show_next_steps
}

main "$@"
```

## Key Takeaways

1. **Single curl command** reduces friction significantly
2. **Cache-busting** ensures users get latest version
3. **Multiple modes** (interactive/easy/dry-run) satisfy different needs
4. **Environment detection** makes installation smarter
5. **Post-install validation** catches issues immediately
6. **Uninstall support** is important for trust
7. **Security transparency** builds confidence
8. **Graceful degradation** works everywhere

## References

- [Ultimate Bug Scanner Installation](https://github.com/Dicklesworthstone/ultimate_bug_scanner#installation)
- Common patterns: Homebrew, npm, pip, cargo installers
- Security best practices for install scripts
