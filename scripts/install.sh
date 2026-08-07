#!/usr/bin/env bash
# Installs the prerequisites for a manual Consortium install on Debian based Linux
# (apt) and macOS (Homebrew). Checks what is already present, reports what is missing,
# asks for permission, then installs the missing pieces with the system package manager.
# See docs/scripts/install-sh.md for the full description.

set -u

# minimum python the framework supports, kept in step with
# docs/getting-started/installation.md
MIN_PYTHON_MAJOR=3
MIN_PYTHON_MINOR=14

ASSUME_YES=0
CHECK_ONLY=0
SKIP_SYNC=0

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(dirname -- "$SCRIPT_DIR")

# the ordered list of things this script knows how to check for, filled in by
# detect_platform since Homebrew only applies to macOS
REQUIREMENTS=""

# apt package names collected while planning, installed in a single apt-get call
APT_PACKAGES=""
# homebrew formulae collected while planning, installed in a single brew call
BREW_FORMULAE=""

# planned actions, kept as two parallel indexed arrays of action ids and the command
# line each one runs, so the plan can be printed before anything is executed. the count
# is tracked separately because expanding an empty array under 'set -u' is an error in
# the bash 3.2 that ships with macOS
PLAN_IDS=()
PLAN_CMDS=()
PLAN_COUNT=0

# ---------------------------------------------------------------------------
# output helpers
# ---------------------------------------------------------------------------

if [ -t 1 ]; then
    C_RESET=$(printf '\033[0m')
    C_DIM=$(printf '\033[90m')
    C_RED=$(printf '\033[31m')
    C_GREEN=$(printf '\033[32m')
    C_YELLOW=$(printf '\033[33m')
    C_CYAN=$(printf '\033[36m')
else
    C_RESET=''
    C_DIM=''
    C_RED=''
    C_GREEN=''
    C_YELLOW=''
    C_CYAN=''
fi

heading() {
    printf '\n%s%s%s\n' "$C_CYAN" "$1" "$C_RESET"
    printf '%s%s%s\n' "$C_DIM" "$(printf '%*s' "${#1}" '' | tr ' ' '-')" "$C_RESET"
}

ok() { printf '  %s[ ok ]%s %s\n' "$C_GREEN" "$C_RESET" "$1"; }
miss() { printf '  %s[miss]%s %s\n' "$C_YELLOW" "$C_RESET" "$1"; }
fail() { printf '  %s[fail]%s %s\n' "$C_RED" "$C_RESET" "$1"; }
note() { printf '  %s%s%s\n' "$C_DIM" "$1" "$C_RESET"; }
run_echo() { printf '  %s> %s%s\n' "$C_DIM" "$1" "$C_RESET"; }

die() {
    printf '\n%s%s%s\n' "$C_RED" "$1" "$C_RESET" >&2
    exit 1
}

confirm() {
    if [ "$ASSUME_YES" -eq 1 ]; then
        printf '%s [Y/n] y (assumed)\n' "$1"
        return 0
    fi
    if [ ! -t 0 ]; then
        printf '%s [Y/n] n (not interactive, re-run with --yes to proceed)\n' "$1"
        return 1
    fi
    while true; do
        printf '%s [Y/n] ' "$1"
        read -r reply || return 1
        case "$reply" in
            '' | y | Y | yes | Yes | YES) return 0 ;;
            n | N | no | No | NO) return 1 ;;
            *) printf "Please answer 'y' or 'n'.\n" ;;
        esac
    done
}

usage() {
    cat <<'EOF'
Usage: install.sh [options]

Installs the prerequisites for a manual Consortium install: Python 3.14+, Git, uv and
Docker. Uses apt on Debian based Linux and Homebrew on macOS, installing Homebrew first
when it is not present.

Options:
  -y, --yes         Answer yes to every prompt (unattended run).
  -c, --check-only  Only report what is found and missing, then exit.
      --skip-sync   Do not offer to run 'uv sync --all-packages' afterwards.
  -h, --help        Show this help and exit.
EOF
}

# ---------------------------------------------------------------------------
# state helpers
# ---------------------------------------------------------------------------

# per requirement state is held in STATUS_<key> (ok or missing) and DETAIL_<key> (the
# version string or the reason it is considered missing), addressed indirectly so the
# requirement list can be iterated
set_state() {
    eval "STATUS_$1=\$2"
    eval "DETAIL_$1=\$3"
}

status_of() {
    eval "printf '%s' \"\${STATUS_$1:-missing}\""
}

detail_of() {
    eval "printf '%s' \"\${DETAIL_$1:-unknown}\""
}

label_of() {
    case "$1" in
        brew) printf 'Homebrew' ;;
        git) printf 'Git' ;;
        python) printf 'Python 3.14+' ;;
        uv) printf 'uv' ;;
        docker) printf 'Docker' ;;
        dockerd) printf 'Docker engine' ;;
        *) printf '%s' "$1" ;;
    esac
}

add_plan() {
    PLAN_IDS+=("$1")
    PLAN_CMDS+=("$2")
    PLAN_COUNT=$((PLAN_COUNT + 1))
}

# ---------------------------------------------------------------------------
# platform detection
# ---------------------------------------------------------------------------

detect_platform() {
    case "$(uname -s)" in
        Linux)
            PLATFORM=linux
            command -v apt-get >/dev/null 2>&1 ||
                die "No apt-get found. This script only supports Debian based distributions; install Python 3.14+, Git, uv and Docker with your distribution's package manager instead."
            PACKAGE_MANAGER="apt"
            REQUIREMENTS="git python uv docker dockerd"
            ;;
        Darwin)
            PLATFORM=macos
            PACKAGE_MANAGER="brew"
            REQUIREMENTS="brew git python uv docker dockerd"
            ;;
        *)
            die "Unsupported operating system '$(uname -s)'. This script supports Debian based Linux and macOS; on Windows use scripts/install.ps1."
            ;;
    esac
}

# root is not needed for Homebrew, which refuses to run under sudo anyway. a missing sudo
# is not fatal here because only the apt actions need it, so checking (and macOS) still
# works without it
setup_sudo() {
    SUDO=""
    SUDO_AVAILABLE=1
    [ "$PLATFORM" = "linux" ] || return 0
    [ "$(id -u)" -eq 0 ] && return 0
    if command -v sudo >/dev/null 2>&1; then
        SUDO="sudo"
    else
        SUDO_AVAILABLE=0
    fi
}

require_root() {
    [ "$SUDO_AVAILABLE" -eq 1 ] && return 0
    die "This script needs root to install packages with apt, but sudo was not found. Re-run it as root."
}

# homebrew does not add itself to PATH for an already running shell, so pick it up from
# its usual prefixes (apple silicon first, then intel) after installing it
load_brew() {
    command -v brew >/dev/null 2>&1 && return 0
    for candidate in /opt/homebrew/bin/brew /usr/local/bin/brew; do
        if [ -x "$candidate" ]; then
            eval "$("$candidate" shellenv)"
            return 0
        fi
    done
    return 1
}

# the uv installer writes to ~/.local/bin, which is often not on PATH in the shell that
# ran this script
load_uv_path() {
    uv_bin="${XDG_BIN_HOME:-$HOME/.local/bin}"
    case ":$PATH:" in
        *":$uv_bin:"*) ;;
        *) PATH="$uv_bin:$PATH" ;;
    esac
    export PATH
}

# ---------------------------------------------------------------------------
# requirement detection
# ---------------------------------------------------------------------------

version_ge_min() {
    candidate_major=${1%%.*}
    candidate_rest=${1#*.}
    candidate_minor=${candidate_rest%%.*}
    case "$candidate_major" in '' | *[!0-9]*) return 1 ;; esac
    case "$candidate_minor" in '' | *[!0-9]*) return 1 ;; esac
    [ "$candidate_major" -gt "$MIN_PYTHON_MAJOR" ] && return 0
    [ "$candidate_major" -eq "$MIN_PYTHON_MAJOR" ] && [ "$candidate_minor" -ge "$MIN_PYTHON_MINOR" ] && return 0
    return 1
}

first_line() {
    "$@" 2>&1 | head -n 1
}

detect_brew() {
    if load_brew; then
        set_state brew ok "$(first_line brew --version)"
    else
        set_state brew missing "not found"
    fi
}

detect_simple() {
    # $1 is the requirement key, $2 the executable to look for
    if command -v "$2" >/dev/null 2>&1; then
        set_state "$1" ok "$(first_line "$2" --version)"
    else
        set_state "$1" missing "not found"
    fi
}

detect_python() {
    older=""
    for candidate in python3.14 python3 python; do
        command -v "$candidate" >/dev/null 2>&1 || continue
        version=$("$candidate" --version 2>&1 | awk 'NR==1 {print $2}')
        [ -n "$version" ] || continue
        if version_ge_min "$version"; then
            set_state python ok "$candidate ($version)"
            return 0
        fi
        [ -n "$older" ] || older="$candidate ($version)"
    done

    # uv can manage interpreters itself, and uv run/uv sync pick a managed one up
    # automatically, so a uv managed 3.14 satisfies the requirement just as well
    if command -v uv >/dev/null 2>&1; then
        managed=$(uv python find '>=3.14' 2>/dev/null)
        if [ -n "$managed" ]; then
            set_state python ok "uv managed ($managed)"
            return 0
        fi
    fi

    if [ -n "$older" ]; then
        set_state python missing "found $older, older than 3.14"
    else
        set_state python missing "not found"
    fi
}

detect_dockerd() {
    if ! command -v docker >/dev/null 2>&1; then
        set_state dockerd missing "not running (docker is not installed)"
        return 0
    fi
    # docker info only succeeds when the client can reach a running engine
    if docker info --format '{{.ServerVersion}}' >/dev/null 2>&1; then
        set_state dockerd ok "running"
    elif [ "$PLATFORM" = "linux" ] && ! id -nG 2>/dev/null | tr ' ' '\n' | grep -qx docker && [ "$(id -u)" -ne 0 ]; then
        set_state dockerd missing "not reachable (this user is not in the 'docker' group)"
    else
        set_state dockerd missing "not running"
    fi
}

detect_all() {
    for key in $REQUIREMENTS; do
        case "$key" in
            brew) detect_brew ;;
            git) detect_simple git git ;;
            uv) detect_simple uv uv ;;
            python) detect_python ;;
            docker) detect_simple docker docker ;;
            dockerd) detect_dockerd ;;
        esac
    done
}

report() {
    heading 'Found'
    reported=0
    for key in $REQUIREMENTS; do
        if [ "$(status_of "$key")" = "ok" ]; then
            printf '  %s[ ok ]%s %-16s %s\n' "$C_GREEN" "$C_RESET" "$(label_of "$key")" "$(detail_of "$key")"
            reported=1
        fi
    done
    [ "$reported" -eq 1 ] || note 'nothing'

    heading 'Missing'
    reported=0
    for key in $REQUIREMENTS; do
        if [ "$(status_of "$key")" != "ok" ]; then
            printf '  %s[miss]%s %-16s %s\n' "$C_YELLOW" "$C_RESET" "$(label_of "$key")" "$(detail_of "$key")"
            reported=1
        fi
    done
    [ "$reported" -eq 1 ] || note 'nothing'
}

missing_count() {
    count=0
    for key in $REQUIREMENTS; do
        [ "$(status_of "$key")" = "ok" ] || count=$((count + 1))
    done
    printf '%s' "$count"
}

# ---------------------------------------------------------------------------
# planning
# ---------------------------------------------------------------------------

# apt does not carry python3.14 on every release, and pulling in a third party archive
# to get it is a bigger commitment than this script should make on its own, so fall back
# to letting uv provide the interpreter
apt_has_python314() {
    apt-cache policy python3.14 2>/dev/null | grep -q 'Candidate: [0-9]'
}

plan_linux() {
    [ "$(status_of git)" = "ok" ] || APT_PACKAGES="$APT_PACKAGES git"
    [ "$(status_of docker)" = "ok" ] || APT_PACKAGES="$APT_PACKAGES docker.io"

    python_from_uv=0
    if [ "$(status_of python)" != "ok" ]; then
        if apt_has_python314; then
            APT_PACKAGES="$APT_PACKAGES python3.14"
        else
            python_from_uv=1
        fi
    fi

    # the uv installer is fetched over https, so curl has to be there for it
    if [ "$(status_of uv)" != "ok" ] && ! command -v curl >/dev/null 2>&1; then
        APT_PACKAGES="$APT_PACKAGES curl"
    fi

    APT_PACKAGES=${APT_PACKAGES# }
    if [ -n "$APT_PACKAGES" ]; then
        require_root
        add_plan apt-update "${SUDO:+$SUDO }apt-get update"
        add_plan apt-install "${SUDO:+$SUDO }apt-get install -y $APT_PACKAGES"
    fi

    if [ "$(status_of uv)" != "ok" ]; then
        add_plan uv-install "curl -LsSf https://astral.sh/uv/install.sh | sh"
    fi
    if [ "$python_from_uv" -eq 1 ]; then
        add_plan uv-python "uv python install 3.14"
    fi
    if [ "$(status_of dockerd)" != "ok" ] && command -v systemctl >/dev/null 2>&1 &&
        [ "$SUDO_AVAILABLE" -eq 1 ]; then
        add_plan docker-service "${SUDO:+$SUDO }systemctl enable --now docker"
    fi
}

plan_macos() {
    if [ "$(status_of brew)" != "ok" ]; then
        add_plan brew-install 'curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh | bash'
    fi

    [ "$(status_of git)" = "ok" ] || BREW_FORMULAE="$BREW_FORMULAE git"
    [ "$(status_of python)" = "ok" ] || BREW_FORMULAE="$BREW_FORMULAE python@3.14"
    [ "$(status_of uv)" = "ok" ] || BREW_FORMULAE="$BREW_FORMULAE uv"

    BREW_FORMULAE=${BREW_FORMULAE# }
    [ -z "$BREW_FORMULAE" ] || add_plan brew-formulae "brew install $BREW_FORMULAE"

    if [ "$(status_of docker)" != "ok" ]; then
        add_plan brew-docker "brew install --cask docker-desktop"
    fi
    if [ "$(status_of dockerd)" != "ok" ]; then
        add_plan docker-start "open -a Docker"
    fi
}

# ---------------------------------------------------------------------------
# execution
# ---------------------------------------------------------------------------

run_action() {
    case "$1" in
        apt-update)
            $SUDO apt-get update
            ;;
        apt-install)
            $SUDO apt-get install -y $APT_PACKAGES
            ;;
        uv-install)
            curl -LsSf https://astral.sh/uv/install.sh | sh && load_uv_path
            ;;
        uv-python)
            load_uv_path
            uv python install 3.14
            ;;
        docker-service)
            $SUDO systemctl enable --now docker
            ;;
        brew-install)
            if [ "$ASSUME_YES" -eq 1 ]; then
                NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            else
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            fi
            load_brew
            ;;
        brew-formulae)
            load_brew || return 1
            brew install $BREW_FORMULAE
            ;;
        brew-docker)
            load_brew || return 1
            # the cask was renamed from 'docker' to 'docker-desktop', so accept either
            brew install --cask docker-desktop || brew install --cask docker
            ;;
        docker-start)
            open -a Docker || open -a 'Docker Desktop'
            ;;
        *)
            return 1
            ;;
    esac
}

run_plan() {
    index=0
    failed=0
    while [ "$index" -lt "$PLAN_COUNT" ]; do
        action=${PLAN_IDS[$index]}
        command_line=${PLAN_CMDS[$index]}
        heading "Action: $action"
        run_echo "$command_line"
        if run_action "$action"; then
            ok "$action finished"
        else
            fail "$action failed (exit code $?)"
            failed=$((failed + 1))
        fi
        index=$((index + 1))
    done
    return "$failed"
}

sync_dependencies() {
    heading 'Installing Consortium dependencies'
    load_uv_path
    if ! command -v uv >/dev/null 2>&1; then
        fail 'uv is not available on PATH, skipping dependency install'
        return 1
    fi
    run_echo "uv sync --all-packages"
    if (cd "$REPO_ROOT" && uv sync --all-packages); then
        ok 'dependencies installed'
        return 0
    fi
    fail 'uv sync failed'
    return 1
}

# ---------------------------------------------------------------------------
# entry point
# ---------------------------------------------------------------------------

while [ "$#" -gt 0 ]; do
    case "$1" in
        -y | --yes) ASSUME_YES=1 ;;
        -c | --check-only) CHECK_ONLY=1 ;;
        --skip-sync) SKIP_SYNC=1 ;;
        -h | --help)
            usage
            exit 0
            ;;
        *)
            usage >&2
            die "Unknown option '$1'."
            ;;
    esac
    shift
done

printf '\n%sConsortium install (%s)%s\n' "$C_RESET" "$(uname -s)" "$C_RESET"
detect_platform
setup_sudo
note "repository root: $REPO_ROOT"
note "package manager: $PACKAGE_MANAGER"

detect_all
if [ "$PLATFORM" = "macos" ] && [ "$(status_of brew)" != "ok" ]; then
    note 'Homebrew is not bundled with macOS, so it is installed first'
fi
report

if [ "$CHECK_ONLY" -eq 1 ]; then
    printf '\n'
    if [ "$(missing_count)" -eq 0 ]; then
        printf '%sAll prerequisites are present.%s\n' "$C_GREEN" "$C_RESET"
        exit 0
    fi
    printf '%sPrerequisites are missing, re-run without --check-only to install them.%s\n' "$C_YELLOW" "$C_RESET"
    exit 1
fi

if [ "$(missing_count)" -gt 0 ]; then
    if [ "$PLATFORM" = "linux" ]; then
        plan_linux
    else
        plan_macos
    fi

    heading 'Planned actions'
    if [ "$PLAN_COUNT" -eq 0 ]; then
        note 'nothing to do'
    else
        for command_line in "${PLAN_CMDS[@]}"; do
            note "$command_line"
        done
    fi

    if [ "$PLAN_COUNT" -gt 0 ]; then
        printf '\n'
        if ! confirm 'Install the missing prerequisites?'; then
            printf '\n%sNothing was installed.%s\n' "$C_YELLOW" "$C_RESET"
            exit 1
        fi
        run_plan
    fi

    load_uv_path
    detect_all
    heading 'Re-checking'
    for key in $REQUIREMENTS; do
        if [ "$(status_of "$key")" = "ok" ]; then
            printf '  %s[ ok ]%s %-16s %s\n' "$C_GREEN" "$C_RESET" "$(label_of "$key")" "$(detail_of "$key")"
        else
            printf '  %s[miss]%s %-16s %s\n' "$C_YELLOW" "$C_RESET" "$(label_of "$key")" "$(detail_of "$key")"
        fi
    done
fi

still_missing=""
for key in $REQUIREMENTS; do
    [ "$key" = "dockerd" ] && continue
    [ "$(status_of "$key")" = "ok" ] || still_missing="$still_missing $key"
done
still_missing=${still_missing# }

if [ -n "$still_missing" ]; then
    heading 'Result'
    fail 'some prerequisites are still missing:'
    for key in $still_missing; do
        note "- $(label_of "$key"): $(detail_of "$key")"
    done
    note 'A tool installed just now may only appear on PATH in a new shell. Open a new'
    note 'shell and run this script again to confirm before installing by hand.'
    exit 1
fi

if [ "$SKIP_SYNC" -eq 0 ]; then
    printf '\n'
    if confirm "Run 'uv sync --all-packages' in $REPO_ROOT now?"; then
        sync_dependencies || exit 1
    else
        note "skipped, run 'uv sync --all-packages' before starting the server"
    fi
fi

heading 'Result'
ok 'all prerequisites are present'
if [ "$(status_of dockerd)" != "ok" ]; then
    miss "the Docker engine is $(detail_of dockerd)"
    if [ "$PLATFORM" = "macos" ]; then
        note 'Start Docker Desktop (open -a Docker) before using an agent generator that'
        note 'compiles its payload in a container. Everything else runs without it.'
    else
        note 'Start it with: sudo systemctl start docker'
        note "To use Docker without sudo: sudo usermod -aG docker ${USER:-$(id -un)}, then log out and"
        note 'back in. Only agent generators that compile their payload in a container need'
        note 'the engine, everything else runs without it.'
    fi
fi
note 'Start the server with: uv run consortium.py server'
note 'Connect the client with: uv run consortium.py client'
exit 0
