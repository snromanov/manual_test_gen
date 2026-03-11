#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

STATE_FILE = "agent_state.json"

def get_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    return get_default_state()
                return json.loads(content)
        except (json.JSONDecodeError, Exception):
            return get_default_state()
    return get_default_state()

def get_default_state():
    return {
        "current_step": "init",
        "completed_steps": [],
        "testcases_generated": 0,
        "total_requirements": 0,
        "project_name": None,
        "history": []
    }

def save_state(state):
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def update_step(step_name, status="completed"):
    state = get_state()
    state["current_step"] = step_name
    if status == "completed" and step_name not in state["completed_steps"]:
        state["completed_steps"].append(step_name)

    entry = f"Step {step_name} marked as {status}"
    if not state.get("history") or state["history"][-1] != entry:
        if "history" not in state:
            state["history"] = []
        state["history"].append(entry)

    save_state(state)
    print(f"Состояние обновлено: {step_name} ({status})")

def set_requirement(total, project_name):
    state = get_state()
    state["total_requirements"] = total
    state["project_name"] = project_name
    save_state(state)
    print(f"Установлено: {total} требований для проекта {project_name}")

def increment_testcases(count):
    state = get_state()
    state["testcases_generated"] += count
    save_state(state)
    print(f"Прогресс: {state['testcases_generated']} тест-кейсов сгенерировано")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Управление чекпоинтами агента")
    parser.add_argument("--get", action="store_true", help="Показать текущее состояние")
    parser.add_argument("--can-cleanup", action="store_true", help="Можно ли безопасно очистить проект")
    parser.add_argument("--update", type=str, help="Обновить текущий шаг")
    parser.add_argument("--status", type=str, default="completed", help="Статус шага")
    parser.add_argument("--set-req", nargs=2, metavar=("TOTAL", "PROJECT"), help="Установить требования")
    parser.add_argument("--inc", type=int, help="Увеличить счетчик тест-кейсов")
    parser.add_argument("--set-count", type=int, help="Установить точное количество тест-кейсов")
    parser.add_argument("--reset", action="store_true", help="Сбросить состояние")

    args = parser.parse_args()

    if args.reset:
        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)
        print("Состояние сброшено")
        sys.exit(0)

    if args.get:
        state = get_state()
        print(json.dumps(state, indent=2, ensure_ascii=False))
        sys.exit(0)

    if args.can_cleanup:
        state = get_state()
        if state["current_step"] == "init" or "testcases_finalized" in state["completed_steps"]:
            print("true")
            sys.exit(0)
        else:
            print("false")
            sys.exit(0)

    if args.update:
        update_step(args.update, args.status)

    if args.set_req:
        set_requirement(int(args.set_req[0]), args.set_req[1])

    if args.inc:
        increment_testcases(args.inc)

    if args.set_count is not None:
        state = get_state()
        state["testcases_generated"] = args.set_count
        save_state(state)
        print(f"Прогресс установлен: {args.set_count}")
