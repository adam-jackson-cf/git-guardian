#!/usr/bin/env bash
# Guardian Installer
# Installs git-guardian CLI tool with optional harness configuration

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Flags
EASY_MODE=false
DRY_RUN=false
NON_INTERACTIVE=false
MINIMAL=false
UNINSTALL=false
SKIP_INIT=false
SKIP_HARNESS=false
INSTALL_DIR="${HOME}/.local/bin"
SHOW_HELP=false

# Script directory (when run from repo)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${SCRIPT_DIR}"

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ${NC} $1" >&2
}

log_success() {
    echo -e "${GREEN}✓${NC} $1" >&2
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1" >&2
}

log_error() {
    echo -e "${RED}✗${NC} $1" >&2
}

# Confirmation prompt
confirm() {
    local prompt="$1"
    local default="${2:-n}"

    if [[ "${NON_INTERACTIVE}" == "true" ]]; then
        return 1
    fi

    if [[ "${EASY_MODE}" == "true" ]]; then
        return 0
    fi

    if [[ "${DRY_RUN}" == "true" ]]; then
        echo "[DRY RUN] Would prompt: ${prompt}"
        return 0
    fi

    local response
    if [[ "${default}" == "y" ]]; then
        read -p "${prompt} [Y/n]: " response
        response="${response:-y}"
    else
        read -p "${prompt} [y/N]: " response
        response="${response:-n}"
    fi

    [[ "${response}" =~ ^[Yy]$ ]]
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Detect Python version
detect_python() {
    local python_cmd=""
    local version=""

    if command_exists python3; then
        python_cmd="python3"
    elif command_exists python; then
        python_cmd="python"
    else
        return 1
    fi

    version=$(${python_cmd} -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "")

    if [[ -z "${version}" ]]; then
        return 1
    fi

    # Check if version >= 3.11
    local major minor
    IFS='.' read -r major minor <<< "${version}"

    if [[ "${major}" -gt 3 ]] || [[ "${major}" -eq 3 && "${minor}" -ge 11 ]]; then
        echo "${python_cmd}"
        return 0
    fi

    return 1
}

# Detect package manager
detect_package_manager() {
    if command_exists uv; then
        echo "uv"
        return 0
    elif command_exists pip; then
        echo "pip"
        return 0
    elif command_exists pip3; then
        echo "pip3"
        return 0
    fi

    return 1
}

# Check if in git repository
is_git_repo() {
    git rev-parse --git-dir >/dev/null 2>&1
}

# Check if guardian is already installed
is_guardian_installed() {
    command_exists guardian
}

# Install guardian
install_guardian() {
    local python_cmd="$1"
    local pkg_mgr="$2"

    if [[ "${DRY_RUN}" == "true" ]]; then
        log_info "Would install git-guardian using ${pkg_mgr}"
        if [[ "${pkg_mgr}" == "uv" ]]; then
            echo "  cd ${REPO_ROOT}"
            echo "  uv sync"
            echo "  uv pip install -e ."
        else
            echo "  cd ${REPO_ROOT}"
            echo "  ${python_cmd} -m pip install -e ."
        fi
        return 0
    fi

    log_info "Installing git-guardian using ${pkg_mgr}..."

    cd "${REPO_ROOT}"

    if [[ "${pkg_mgr}" == "uv" ]]; then
        if ! uv sync; then
            log_error "Failed to sync dependencies with uv"
            return 1
        fi

        if ! uv pip install -e .; then
            log_error "Failed to install git-guardian with uv"
            return 1
        fi
    else
        if ! ${python_cmd} -m pip install -e .; then
            log_error "Failed to install git-guardian with ${pkg_mgr}"
            return 1
        fi
    fi

    log_success "git-guardian installed successfully"
}

# Run guardian init
run_guardian_init() {
    if [[ "${SKIP_INIT}" == "true" ]] || [[ "${MINIMAL}" == "true" ]]; then
        return 0
    fi

    if [[ "${DRY_RUN}" == "true" ]]; then
        if is_git_repo; then
            log_info "Would run: guardian init"
        else
            log_warning "Not in git repository, skipping guardian init"
        fi
        return 0
    fi

    if ! is_git_repo; then
        log_warning "Not in git repository, skipping guardian init"
        return 0
    fi

    if ! command_exists guardian; then
        log_warning "guardian command not found, skipping init"
        return 0
    fi

    log_info "Initializing Guardian..."
    if guardian init; then
        log_success "Guardian initialized"
    else
        log_warning "Failed to initialize Guardian (may already be initialized)"
    fi
}

# Install harness configurations
install_harnesses() {
    if [[ "${SKIP_HARNESS}" == "true" ]] || [[ "${MINIMAL}" == "true" ]]; then
        return 0
    fi

    if [[ "${DRY_RUN}" == "true" ]]; then
        if is_git_repo; then
            log_info "Would run: guardian harness install --all"
        else
            log_warning "Not in git repository, skipping harness installation"
        fi
        return 0
    fi

    if ! is_git_repo; then
        log_warning "Not in git repository, skipping harness installation"
        return 0
    fi

    if ! command_exists guardian; then
        log_warning "guardian command not found, skipping harness installation"
        return 0
    fi

    log_info "Installing harness configurations..."
    if guardian harness install --all; then
        log_success "Harness configurations installed"
    else
        log_warning "Failed to install some harness configurations"
    fi
}

# Verify installation
verify_installation() {
    if [[ "${DRY_RUN}" == "true" ]]; then
        log_info "Would verify installation: guardian --version"
        return 0
    fi

    if ! command_exists guardian; then
        log_error "guardian command not found in PATH"
        return 1
    fi

    log_info "Verifying installation..."
    if guardian --version >/dev/null 2>&1; then
        log_success "Installation verified"
        guardian --version
        return 0
    else
        log_error "Installation verification failed"
        return 1
    fi
}

# Show next steps
show_next_steps() {
    echo ""
    log_success "Installation complete!"
    echo ""

    if [[ "${MINIMAL}" == "true" ]] || [[ "${SKIP_INIT}" == "true" ]]; then
        echo "Next steps:"
        echo "  1. Navigate to your git repository"
        echo "  2. Run: guardian init"
        echo "  3. Run: guardian harness install --all"
        echo "  4. Run: guardian verify"
    elif [[ "${SKIP_HARNESS}" == "true" ]]; then
        echo "Next steps:"
        echo "  1. Run: guardian harness install --all"
        echo "  2. Run: guardian verify"
    else
        echo "Next steps:"
        echo "  1. Run: guardian verify"
        echo "  2. Use: guardian push origin main (instead of git push)"
    fi
    echo ""
}

# Uninstall guardian
uninstall_guardian() {
    if [[ "${DRY_RUN}" == "true" ]]; then
        log_info "Would uninstall git-guardian"
        echo "  - Remove guardian command (if installed via pip/pipx)"
        echo "  - Remove .guardian/ directory (if exists)"
        echo "  - Remove harness configuration files (with confirmation)"
        return 0
    fi

    log_warning "Uninstalling git-guardian..."

    # Try to uninstall via pip/pipx
    if command_exists pipx; then
        if pipx list | grep -q "git-guardian"; then
            if confirm "Uninstall git-guardian via pipx?" "y"; then
                pipx uninstall git-guardian
                log_success "Uninstalled via pipx"
            fi
        fi
    fi

    if command_exists pip3; then
        if pip3 list | grep -q "git-guardian"; then
            if confirm "Uninstall git-guardian via pip3?" "y"; then
                pip3 uninstall git-guardian -y
                log_success "Uninstalled via pip3"
            fi
        fi
    fi

    # Remove .guardian directory
    if [[ -d ".guardian" ]] && is_git_repo; then
        if confirm "Remove .guardian/ directory?" "y"; then
            rm -rf .guardian
            log_success "Removed .guardian/ directory"
        fi
    fi

    # Remove harness files (ask about each type)
    if is_git_repo; then
        local repo_root="$(pwd)"

        if [[ -f "${repo_root}/.cursorrules" ]] && confirm "Remove .cursorrules?" "n"; then
            rm -f "${repo_root}/.cursorrules"
            log_success "Removed .cursorrules"
        fi

        if [[ -f "${repo_root}/CLAUDE.md" ]] && confirm "Remove CLAUDE.md and .claude/?" "n"; then
            rm -f "${repo_root}/CLAUDE.md"
            [[ -d "${repo_root}/.claude" ]] && rm -rf "${repo_root}/.claude"
            log_success "Removed Claude Code configuration"
        fi

        if [[ -f "${repo_root}/AGENTS.md" ]] && confirm "Remove AGENTS.md and ~/.codex/policy/guardian.codexpolicy?" "n"; then
            rm -f "${repo_root}/AGENTS.md"
            [[ -f "${HOME}/.codex/policy/guardian.codexpolicy" ]] && rm -f "${HOME}/.codex/policy/guardian.codexpolicy"
            log_success "Removed Codex configuration"
        fi

        if [[ -f "${repo_root}/GEMINI.md" ]] && confirm "Remove GEMINI.md and .gemini/?" "n"; then
            rm -f "${repo_root}/GEMINI.md"
            [[ -d "${repo_root}/.gemini" ]] && rm -rf "${repo_root}/.gemini"
            log_success "Removed Gemini configuration"
        fi

        if [[ -f "${repo_root}/.github/copilot-instructions.md" ]] && confirm "Remove Copilot configuration?" "n"; then
            rm -f "${repo_root}/.github/copilot-instructions.md"
            log_success "Removed Copilot configuration"
        fi
    fi

    log_success "Uninstallation complete"
}

# Show help
show_help() {
    cat <<EOF
Guardian Installer

Installs git-guardian CLI tool with optional harness configuration for AI coding agents.

USAGE:
    bash install.sh [OPTIONS]

OPTIONS:
    --easy-mode           Auto-install everything without prompts
    --dry-run             Show what would be installed without making changes
    --non-interactive     Fail if prompts would be required (CI-friendly)
    --minimal             Skip harness installation and init
    --skip-init           Skip running 'guardian init'
    --skip-harness        Skip installing harness configurations
    --uninstall           Uninstall git-guardian and remove configurations
    --help                Show this help message

EXAMPLES:
    # Interactive installation
    curl -fsSL "https://raw.githubusercontent.com/your-org/git-guardian/master/install.sh?$(date +%s)" | bash

    # Easy mode (auto-install everything)
    curl -fsSL "https://raw.githubusercontent.com/your-org/git-guardian/master/install.sh?$(date +%s)" | bash -s -- --easy-mode

    # Dry run to preview changes
    bash install.sh --dry-run

    # Uninstall
    bash install.sh --uninstall

PREREQUISITES:
    - Python 3.11 or higher
    - uv (recommended) or pip
    - Git (optional, for initializing in repositories)

For manual installation, see README.md
EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --easy-mode)
                EASY_MODE=true
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --non-interactive)
                NON_INTERACTIVE=true
                shift
                ;;
            --minimal)
                MINIMAL=true
                shift
                ;;
            --skip-init)
                SKIP_INIT=true
                shift
                ;;
            --skip-harness)
                SKIP_HARNESS=true
                shift
                ;;
            --uninstall)
                UNINSTALL=true
                shift
                ;;
            --help|-h)
                SHOW_HELP=true
                shift
                ;;
            *)
                log_error "Unknown option: $1"
                echo "Run with --help for usage information"
                exit 1
                ;;
        esac
    done
}

# Main installation flow
main() {
    parse_args "$@"

    if [[ "${SHOW_HELP}" == "true" ]]; then
        show_help
        exit 0
    fi

    if [[ "${UNINSTALL}" == "true" ]]; then
        uninstall_guardian
        exit 0
    fi

    log_info "Guardian Installer"
    echo ""

    # Check if we're in the git-guardian repository
    if [[ ! -f "${REPO_ROOT}/pyproject.toml" ]] || ! grep -q "git-guardian" "${REPO_ROOT}/pyproject.toml" 2>/dev/null; then
        log_error "This installer must be run from the git-guardian repository root"
        log_info "Clone the repository first:"
        echo "  git clone https://github.com/your-org/git-guardian.git"
        echo "  cd git-guardian"
        echo "  bash install.sh"
        exit 1
    fi

    # Detect Python
    local python_cmd
    if ! python_cmd=$(detect_python); then
        log_error "Python 3.11+ is required but not found"
        log_info "Please install Python 3.11 or higher"
        exit 1
    fi
    log_success "Found Python: $(${python_cmd} --version)"

    # Detect package manager
    local pkg_mgr
    if ! pkg_mgr=$(detect_package_manager); then
        log_error "No package manager found (uv, pip, or pip3 required)"
        exit 1
    fi
    log_success "Using package manager: ${pkg_mgr}"

    # Check if already installed
    if is_guardian_installed; then
        log_warning "guardian appears to be already installed"
        if [[ "${DRY_RUN}" != "true" ]] && ! confirm "Reinstall git-guardian?" "n"; then
            log_info "Installation cancelled"
            exit 0
        fi
    fi

    # Install guardian
    if ! install_guardian "${python_cmd}" "${pkg_mgr}"; then
        log_error "Installation failed"
        exit 1
    fi

    # Verify installation
    if ! verify_installation; then
        log_error "Installation verification failed"
        exit 1
    fi

    # Initialize and install harnesses if requested
    if [[ "${EASY_MODE}" == "true" ]] || confirm "Initialize Guardian and install harness configurations?" "y"; then
        run_guardian_init
        install_harnesses
    fi

    # Show next steps
    if [[ "${DRY_RUN}" != "true" ]]; then
        show_next_steps
    fi
}

# Run main function
main "$@"
