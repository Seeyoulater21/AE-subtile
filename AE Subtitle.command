#!/bin/bash

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON_DIR="$ROOT_DIR/python"
PYTHON_EXTRAS_DIR="$ROOT_DIR/python[transcribe]"
VENV_DIR="$ROOT_DIR/.venv"
PYTHON_BIN="$VENV_DIR/bin/python"
SERVER_HOST="${AESUBTITLE_HOST:-127.0.0.1}"
SERVER_PORT="${AESUBTITLE_PORT:-8765}"
TRANSCRIBE_MODEL="${AESUBTITLE_MODEL:-large-v3}"
TRANSCRIBE_DEVICE="${AESUBTITLE_DEVICE:-auto}"
TRANSCRIBE_COMPUTE_TYPE="${AESUBTITLE_COMPUTE_TYPE:-int8}"
LOG_DIR="$ROOT_DIR/.aesubtitle/logs"
SERVER_LOG="$LOG_DIR/server.log"

NC='\033[0m'
FG_BLOCK='\033[38;2;238;238;238m'
SHADOW_MID='\033[38;2;96;96;96m'
SHADOW_DARK='\033[38;2;42;42;42m'
DIM='\033[38;2;140;140;140m'
WHITE='\033[38;2;238;238;238m'
GREEN='\033[38;2;80;220;100m'
RED='\033[38;2;220;60;60m'
YELLOW='\033[38;2;230;190;80m'

DOT_ALIVE='\033[38;2;80;220;100m●\033[0m'
DOT_DEAD='\033[38;2;220;60;60m●\033[0m'

SELECTED=0
MENU_START=13
SERVER_PID=""
SERVER_MODE="stopped"
SERVER_START_TIME=""
LAST_STATUS="Starting..."

MENU_ITEMS=(
    "Status"
    "Check / Install Dependencies"
    "Restart Server"
    "Logs: Server"
    "Quit"
)
MENU_COUNT=${#MENU_ITEMS[@]}

port_is_free() {
    ! lsof -ti:"$1" >/dev/null 2>&1
}

get_pid_on_port() {
    lsof -ti:"$1" 2>/dev/null | head -1
}

is_alive() {
    local pid="$1"
    [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null
}

health_dot() {
    if is_alive "$1"; then
        printf "%b" "$DOT_ALIVE"
    else
        printf "%b" "$DOT_DEAD"
    fi
}

wait_for_enter() {
    printf "\nPress Enter to continue..."
    IFS= read -r _
}

ensure_model_cache() {
    printf "Checking transcription model: %s (%s, %s)\n" "$TRANSCRIBE_MODEL" "$TRANSCRIBE_DEVICE" "$TRANSCRIBE_COMPUTE_TYPE"
    "$PYTHON_BIN" - "$TRANSCRIBE_MODEL" "$TRANSCRIBE_DEVICE" "$TRANSCRIBE_COMPUTE_TYPE" <<'PY'
import sys

from faster_whisper import WhisperModel

model, device, compute_type = sys.argv[1:4]
WhisperModel(model, device=device, compute_type=compute_type)
PY
}

ensure_dependencies() {
    mkdir -p "$LOG_DIR"
    printf "AE Subtitle dependency check\n"

    if ! command -v python3 >/dev/null 2>&1; then
        printf "Missing python3. Install Python 3.10+ first.\n"
        return 1
    fi

    if [[ ! -x "$PYTHON_BIN" ]]; then
        printf "Creating virtualenv: %s\n" "$VENV_DIR"
        python3 -m venv "$VENV_DIR" || return 1
    else
        printf "Python virtualenv exists.\n"
    fi

    local need_python_deps=0
    "$PYTHON_BIN" -c "import aesubtitle" >/dev/null 2>&1 || need_python_deps=1
    "$PYTHON_BIN" -c "import faster_whisper" >/dev/null 2>&1 || need_python_deps=1

    if [[ "$need_python_deps" -eq 1 ]]; then
        printf "Installing missing Python dependencies...\n"
        "$PYTHON_BIN" -m pip install -e "$PYTHON_EXTRAS_DIR" || return 1
    else
        printf "Python dependencies already installed.\n"
    fi

    if command -v ffmpeg >/dev/null 2>&1; then
        printf "ffmpeg exists.\n"
    elif command -v brew >/dev/null 2>&1; then
        if brew list ffmpeg >/dev/null 2>&1; then
            printf "ffmpeg exists in Homebrew.\n"
        else
            printf "Installing ffmpeg with Homebrew...\n"
            brew install ffmpeg || return 1
        fi
    else
        printf "Missing ffmpeg and Homebrew not found. Install ffmpeg, then relaunch.\n"
        return 1
    fi

    if ensure_model_cache; then
        printf "Transcription model ready.\n"
    else
        printf "Could not prepare transcription model. Check internet connection or set AESUBTITLE_MODEL to an installed model.\n"
        return 1
    fi

    printf "Dependency check complete.\n"
    return 0
}

start_server() {
    mkdir -p "$LOG_DIR"
    : >"$SERVER_LOG"
    "$PYTHON_BIN" -m aesubtitle.server \
        --host "$SERVER_HOST" \
        --port "$SERVER_PORT" \
        --model "$TRANSCRIBE_MODEL" \
        --device "$TRANSCRIBE_DEVICE" \
        --compute-type "$TRANSCRIBE_COMPUTE_TYPE" >>"$SERVER_LOG" 2>&1 &
    SERVER_PID=$!
    SERVER_START_TIME=$(date +%s)
    SERVER_MODE="started"
    sleep 1
    if is_alive "$SERVER_PID"; then
        LAST_STATUS="Server started on $SERVER_HOST:$SERVER_PORT"
    else
        LAST_STATUS="Server failed. Open logs."
    fi
}

stop_server() {
    if is_alive "$SERVER_PID"; then
        pkill -P "$SERVER_PID" 2>/dev/null
        kill "$SERVER_PID" 2>/dev/null
        wait "$SERVER_PID" 2>/dev/null
    fi
}

adopt_or_start_server() {
    if port_is_free "$SERVER_PORT"; then
        start_server
    else
        SERVER_PID=$(get_pid_on_port "$SERVER_PORT")
        SERVER_START_TIME=$(date +%s)
        SERVER_MODE="adopted"
        LAST_STATUS="Server adopted on $SERVER_HOST:$SERVER_PORT"
    fi
}

restart_server() {
    if [[ "$SERVER_MODE" == "adopted" ]]; then
        lsof -ti:"$SERVER_PORT" | xargs kill 2>/dev/null
        sleep 1
    else
        stop_server
    fi
    start_server
}

cleanup() {
    printf '\033[0m'
    printf '\033[?2026l'
    printf '\033[?25h'
    printf '\033[?1049l'
    stty sane 2>/dev/null

    if [[ "$SERVER_MODE" == "started" ]]; then
        stop_server
    fi

    printf "\nAE Subtitle launcher closed.\n"
}
trap cleanup EXIT
trap 'exit 0' INT TERM HUP

draw_banner_text() {
    local row="$1"
    local col="$2"
    local color="$3"

    printf '\033[%d;%dH%b  AE SUBTITLE%b' "$row" "$col" "$color" "$NC"
    printf '\033[%d;%dH%b  LOCAL SERVER%b' $((row + 1)) "$col" "$color" "$NC"
}

draw_banner() {
    draw_banner_text 4 6 "$SHADOW_DARK"
    draw_banner_text 3 5 "$SHADOW_MID"
    draw_banner_text 2 3 "$FG_BLOCK"
}

uptime_label() {
    if [[ -z "$SERVER_START_TIME" ]]; then
        printf "-"
        return
    fi
    local now
    now=$(date +%s)
    local seconds=$((now - SERVER_START_TIME))
    if [[ "$SERVER_MODE" == "adopted" ]]; then
        printf "~%ss" "$seconds"
    else
        printf "%ss" "$seconds"
    fi
}

menu_label() {
    local index="$1"
    local label="${MENU_ITEMS[$index]}"
    case "$index" in
        0|2|3) printf "%s  " "$label"; health_dot "$SERVER_PID" ;;
        *) printf "%s" "$label" ;;
    esac
}

draw_menu_row() {
    local index="$1"
    local row=$((MENU_START + index))
    local marker=" "
    local style="$DIM"

    if [[ "$index" -eq "$SELECTED" ]]; then
        marker=">"
        style="$WHITE"
    fi

    printf '\033[%d;1H\033[2K' "$row"
    printf "%b %s " "$style" "$marker"
    menu_label "$index"
    printf "%b" "$NC"
}

draw_dynamic() {
    local mode_label="$SERVER_MODE"
    local mode_color="$YELLOW"
    if [[ "$SERVER_MODE" == "started" ]]; then
        mode_color="$GREEN"
    elif [[ "$SERVER_MODE" == "stopped" ]]; then
        mode_color="$RED"
    fi

    printf '\033[8;1H%bServer:%b http://%s:%s  %b[%s]%b  PID=%s  uptime=%s' "$WHITE" "$NC" "$SERVER_HOST" "$SERVER_PORT" "$mode_color" "$mode_label" "$NC" "${SERVER_PID:-none}" "$(uptime_label)"
    printf '\033[9;1H%bModel:%b  %s  device=%s  compute=%s' "$WHITE" "$NC" "$TRANSCRIBE_MODEL" "$TRANSCRIBE_DEVICE" "$TRANSCRIBE_COMPUTE_TYPE"
    printf '\033[10;1H%b%s%b' "$DIM" "$LAST_STATUS" "$NC"

    local i
    for ((i = 0; i < MENU_COUNT; i += 1)); do
        draw_menu_row "$i"
    done

    printf '\033[%d;1H%b↑/↓ move  Enter select  q quit%b' $((MENU_START + MENU_COUNT + 2)) "$DIM" "$NC"
}

draw_full() {
    printf '\033[?2026h'
    printf '\033[1;1H\033[J'
    draw_banner
    draw_dynamic
    printf '\033[?2026l'
}

draw_partial() {
    local old="$1"
    local new="$2"
    printf '\033[?2026h'
    draw_menu_row "$old"
    draw_menu_row "$new"
    printf '\033[?2026l'
}

view_status() {
    printf '\033[?2026h'
    printf '\033[1;1H\033[J'
    printf '%bAE Subtitle Server Status%b\n\n' "$WHITE" "$NC"
    printf 'URL:    http://%s:%s\n' "$SERVER_HOST" "$SERVER_PORT"
    printf 'PID:    %s\n' "${SERVER_PID:-none}"
    printf 'Mode:   %s\n' "$SERVER_MODE"
    printf 'Model:  %s\n' "$TRANSCRIBE_MODEL"
    printf 'Device: %s\n' "$TRANSCRIBE_DEVICE"
    printf 'Compute:%s\n' "$TRANSCRIBE_COMPUTE_TYPE"
    printf 'Alive:  '
    if is_alive "$SERVER_PID"; then
        printf '%balive%b\n' "$GREEN" "$NC"
    else
        printf '%bdead%b\n' "$RED" "$NC"
    fi
    printf 'Uptime: %s\n' "$(uptime_label)"
    printf '\n%bEnter/b back  r refresh  q quit%b' "$DIM" "$NC"
    printf '\033[?2026l'

    while true; do
        IFS= read -rsn1 KEY
        if [[ "$KEY" == "" ]] || [[ "$KEY" == "b" ]]; then
            return
        elif [[ "$KEY" == "q" ]]; then
            exit 0
        elif [[ "$KEY" == "r" ]]; then
            view_status
            return
        fi
    done
}

view_logs() {
    printf '\033[?2026h'
    printf '\033[1;1H\033[J'
    printf '%bAE Subtitle Server Logs%b\n\n' "$WHITE" "$NC"
    if [[ -f "$SERVER_LOG" ]]; then
        tail -30 "$SERVER_LOG"
    else
        printf 'No log file yet: %s\n' "$SERVER_LOG"
    fi
    printf '\n%bEnter/b back  r refresh  q quit%b' "$DIM" "$NC"
    printf '\033[?2026l'

    while true; do
        IFS= read -rsn1 KEY
        if [[ "$KEY" == "" ]] || [[ "$KEY" == "b" ]]; then
            return
        elif [[ "$KEY" == "q" ]]; then
            exit 0
        elif [[ "$KEY" == "r" ]]; then
            view_logs
            return
        fi
    done
}

view_dependency_check() {
    printf '\033[?2026h'
    printf '\033[1;1H\033[J'
    printf '\033[?2026l'
    ensure_dependencies
    wait_for_enter
}

execute_action() {
    case "$SELECTED" in
        0) view_status ;;
        1) view_dependency_check ;;
        2) restart_server ;;
        3) view_logs ;;
        4) exit 0 ;;
    esac
}

printf "Preparing AE Subtitle launcher...\n"
if ! ensure_dependencies; then
    wait_for_enter
    exit 1
fi

printf '\033[?1049h'
printf '\033[?25l'
stty -echo 2>/dev/null
adopt_or_start_server
draw_full

while true; do
    IFS= read -rsn1 KEY
    if [[ "$KEY" == $'\x1b' ]]; then
        IFS= read -rsn2 ARROW
        case "$ARROW" in
            "[A")
                OLD_SELECTED="$SELECTED"
                SELECTED=$(( (SELECTED - 1 + MENU_COUNT) % MENU_COUNT ))
                draw_partial "$OLD_SELECTED" "$SELECTED"
                ;;
            "[B")
                OLD_SELECTED="$SELECTED"
                SELECTED=$(( (SELECTED + 1) % MENU_COUNT ))
                draw_partial "$OLD_SELECTED" "$SELECTED"
                ;;
        esac
    elif [[ "$KEY" == "" ]]; then
        execute_action
        draw_full
    elif [[ "$KEY" == "q" ]]; then
        exit 0
    fi
done
