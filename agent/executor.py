import json
import sys
import threading
from collections.abc import Callable, Mapping
from pathlib import Path

from config import get_secret
from runtime_paths import resource_root

from mark.safety import (
    DecisionKind,
    SafetyDecision,
    SafetyPolicy,
    SafetyPolicyError,
    UnknownToolError,
    UntrustedSource,
    authorize,
    validate_args,
)


def get_base_dir() -> Path:
    return resource_root()


BASE_DIR = get_base_dir()
API_CONFIG_PATH = BASE_DIR / "config" / "api_keys.json"

_CONFIRM_KINDS = frozenset(
    {
        DecisionKind.CONFIRM,
        DecisionKind.EXACT_CONFIRM,
        DecisionKind.BIOMETRIC,
    }
)


class ToolDeniedError(SafetyPolicyError):
    """authorize returned deny, or required confirmation was not granted."""

    def __init__(self, tool_name: str, reason: str = "") -> None:
        self.tool_name = tool_name
        super().__init__(
            "denied",
            reason or "Tool is refused by policy.",
        )


def _get_api_key() -> str:
    """Lazy helper for leftover translate/summarize paths. Not used for tools."""
    key = get_secret("gemini_api_key")
    if not key:
        raise RuntimeError("Gemini API key is not configured.")
    return key


def _inject_context(params: dict, tool: str, step_results: dict, goal: str = "") -> dict:
    if not step_results:
        return params

    params = dict(params)

    if tool == "file_controller" and params.get("action") in ("write", "create_file"):
        content = params.get("content", "")
        if not content or len(content) < 50:
            all_results = [
                v for v in step_results.values()
                if v and len(v) > 100 and v not in ("Done.", "Completed.")
            ]
            if all_results:
                combined = "\n\n---\n\n".join(all_results)
                translated = _translate_to_goal_language(combined, goal)
                params["content"] = translated
                print("[Executor] 💉 Injected + translated content")

    return params


def _detect_language(text: str) -> str:
    try:
        from google import genai

        client = genai.Client(api_key=_get_api_key())
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=(
                f"What language is this text written in? "
                f"Reply with ONLY the language name in English (e.g. Turkish, English, French).\n\n"
                f"Text: {text[:200]}"
            ),
        )
        return response.text.strip()
    except Exception:
        return "English"


def _translate_to_goal_language(content: str, goal: str) -> str:
    if not goal:
        return content
    try:
        from google import genai

        client = genai.Client(api_key=_get_api_key())

        target_lang = _detect_language(goal)
        print(f"[Executor] 🌐 Translating to: {target_lang}")

        prompt = (
            f"You are a professional translator. "
            f"Translate the following text into {target_lang}.\n"
            f"IMPORTANT:\n"
            f"- Translate EVERYTHING, leave nothing in English\n"
            f"- Keep all facts, numbers, and data intact\n"
            f"- Keep the structure and formatting\n"
            f"- Output ONLY the translated text, nothing else\n\n"
            f"Text to translate:\n{content[:4000]}"
        )
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        translated = response.text.strip()
        print(f"[Executor] ✅ Translation done ({target_lang})")
        return translated
    except Exception as e:
        print(f"[Executor] ⚠️ Translation failed: {e}")
        return content


def _authorize_tool(
    tool: str,
    parameters: Mapping[str, object],
    *,
    policy: SafetyPolicy | None,
    source: UntrustedSource | str,
    intent: str,
) -> SafetyDecision:
    if policy is None:
        return authorize(tool, parameters, source=source, intent=intent)
    return policy.authorize(tool, parameters, source=source, intent=intent)


def _validate_tool_args(
    tool: str,
    parameters: object,
    *,
    policy: SafetyPolicy | None,
) -> dict[str, object]:
    if policy is None:
        return validate_args(tool, parameters)
    return policy.validate_args(tool, parameters)


def _require_confirmation(
    decision: SafetyDecision,
    confirmer: Callable[[SafetyDecision], bool] | None,
) -> None:
    if decision.kind not in _CONFIRM_KINDS:
        return
    if confirmer is None or not confirmer(decision):
        raise ToolDeniedError(decision.tool_name, "Confirmation is required.")


def _dispatch_tool(tool: str, parameters: dict, speak: Callable | None) -> str:
    if tool == "open_app":
        from actions.open_app import open_app
        return open_app(parameters=parameters, player=None) or "Done."

    if tool == "web_search":
        from actions.web_search import web_search
        return web_search(parameters=parameters, player=None) or "Done."

    if tool == "game_updater":
        from actions.game_updater import game_updater
        return game_updater(parameters=parameters, player=None, speak=speak) or "Done."

    if tool == "browser_control":
        from actions.browser_control import browser_control
        return browser_control(parameters=parameters, player=None) or "Done."

    if tool == "file_controller":
        from actions.file_controller import file_controller
        return file_controller(parameters=parameters, player=None) or "Done."

    if tool == "cmd_control":
        from actions.cmd_control import cmd_control
        return cmd_control(parameters=parameters, player=None) or "Done."

    if tool == "code_helper":
        from actions.code_helper import code_helper
        return code_helper(parameters=parameters, player=None, speak=speak) or "Done."

    if tool == "dev_agent":
        from actions.dev_agent import dev_agent
        return dev_agent(parameters=parameters, player=None, speak=speak) or "Done."

    if tool == "screen_process":
        from actions.screen_processor import screen_process
        screen_process(parameters=parameters, player=None)
        return "Screen captured and analyzed."

    if tool == "send_message":
        from actions.send_message import send_message
        return send_message(parameters=parameters, player=None) or "Done."

    if tool == "reminder":
        from actions.reminder import reminder
        return reminder(parameters=parameters, player=None) or "Done."

    if tool == "youtube_video":
        from actions.youtube_video import youtube_video
        return youtube_video(parameters=parameters, player=None) or "Done."

    if tool == "weather_report":
        from actions.weather_report import weather_action
        return weather_action(parameters=parameters, player=None) or "Done."

    if tool == "computer_settings":
        from actions.computer_settings import computer_settings
        return computer_settings(parameters=parameters, player=None) or "Done."

    if tool == "desktop_control":
        from actions.desktop import desktop_control
        return desktop_control(parameters=parameters, player=None) or "Done."

    if tool == "computer_control":
        from actions.computer_control import computer_control
        return computer_control(parameters=parameters, player=None) or "Done."

    if tool == "generated_code":
        raise ToolDeniedError(tool, "generated_code is not an execution path.")

    if tool == "flight_finder":
        from actions.flight_finder import flight_finder
        return flight_finder(parameters=parameters, player=None, speak=speak) or "Done."

    raise UnknownToolError(tool)


def _call_tool(
    tool: str,
    parameters: dict,
    speak: Callable | None,
    *,
    policy: SafetyPolicy | None = None,
    confirmer: Callable[[SafetyDecision], bool] | None = None,
    source: UntrustedSource | str = UntrustedSource.USER,
    intent: str = "",
) -> str:
    decision = _authorize_tool(
        tool,
        parameters,
        policy=policy,
        source=source,
        intent=intent,
    )
    checked = _validate_tool_args(tool, parameters, policy=policy)
    if decision.kind is DecisionKind.DENY:
        raise ToolDeniedError(tool, decision.reason)
    _require_confirmation(decision, confirmer)
    return _dispatch_tool(tool, checked, speak)


class AgentExecutor:

    MAX_REPLAN_ATTEMPTS = 2

    def __init__(
        self,
        policy: SafetyPolicy | None = None,
        confirmer: Callable[[SafetyDecision], bool] | None = None,
        source: UntrustedSource | str = UntrustedSource.USER,
    ) -> None:
        self._policy = policy
        self._confirmer = confirmer
        self._source = source

    def _call_tool(self, tool: str, parameters: dict, speak: Callable | None) -> str:
        return _call_tool(
            tool,
            parameters,
            speak,
            policy=self._policy,
            confirmer=self._confirmer,
            source=self._source,
        )

    def execute(
        self,
        goal: str,
        speak: Callable | None = None,
        cancel_flag: threading.Event | None = None,
    ) -> str:
        from agent.error_handler import ErrorDecision, analyze_error, generate_fix
        from agent.planner import create_plan, replan

        print(f"\n[Executor] 🎯 Goal: {goal}")

        replan_attempts = 0
        completed_steps = []
        step_results = {}
        plan = create_plan(goal)

        while True:
            steps = plan.get("steps", [])

            if not steps:
                msg = "Сэр, мне не удалось составить корректный план для этой задачи."
                if speak:
                    speak(msg)
                return msg

            success = True
            failed_step = None
            failed_error = ""

            for step in steps:
                if cancel_flag and cancel_flag.is_set():
                    if speak:
                        speak("Задача отменена, сэр.")
                    return "Задача отменена."

                step_num = step.get("step", "?")
                tool = step.get("tool") or ""
                desc = step.get("description", "")
                params = step.get("parameters", {})

                params = _inject_context(params, tool, step_results, goal=goal)

                print(f"\n[Executor] ▶️ Step {step_num}: [{tool}] {desc}")

                attempt = 1
                step_ok = False

                while attempt <= 3:
                    if cancel_flag and cancel_flag.is_set():
                        break
                    try:
                        result = self._call_tool(tool, params, speak)
                        step_results[step_num] = result
                        completed_steps.append(step)
                        print(f"[Executor] ✅ Step {step_num} done: {str(result)[:100]}")
                        step_ok = True
                        break

                    except Exception as e:
                        error_msg = str(e)
                        print(f"[Executor] ❌ Step {step_num} attempt {attempt} failed: {error_msg}")

                        recovery = analyze_error(step, error_msg, attempt=attempt)
                        decision = recovery["decision"]
                        user_msg = recovery.get("user_message", "")

                        if speak and user_msg:
                            speak(user_msg)

                        if decision == ErrorDecision.RETRY:
                            attempt += 1
                            import time
                            time.sleep(2)
                            continue

                        elif decision == ErrorDecision.SKIP:
                            print(f"[Executor] ⏭️ Skipping step {step_num}")
                            completed_steps.append(step)
                            step_ok = True
                            break

                        elif decision == ErrorDecision.ABORT:
                            msg = f"Задача прервана, сэр. {recovery.get('reason', '')}"
                            if speak:
                                speak(msg)
                            return msg

                        else:
                            fix_suggestion = recovery.get("fix_suggestion", "")
                            if fix_suggestion and tool != "generated_code":
                                try:
                                    fixed_step = generate_fix(step, error_msg, fix_suggestion)
                                    if speak:
                                        speak("Пробую другой подход, сэр.")
                                    res = self._call_tool(
                                        fixed_step["tool"],
                                        fixed_step["parameters"],
                                        speak,
                                    )
                                    step_results[step_num] = res
                                    completed_steps.append(step)
                                    step_ok = True
                                    break
                                except Exception as fix_err:
                                    print(f"[Executor] ⚠️ Fix failed: {fix_err}")

                            failed_step = step
                            failed_error = error_msg
                            success = False
                            break

                if not step_ok and not failed_step:
                    failed_step = step
                    failed_error = "Max retries exceeded"
                    success = False

                if not success:
                    break

            if success:
                return self._summarize(goal, completed_steps, speak)

            if replan_attempts >= self.MAX_REPLAN_ATTEMPTS:
                msg = (
                    f"Сэр, задача не выполнена после {replan_attempts} "
                    "попыток перепланирования."
                )
                if speak:
                    speak(msg)
                return msg

            if speak:
                speak("Корректирую подход, сэр.")

            replan_attempts += 1
            plan = replan(goal, completed_steps, failed_step, failed_error)

    def _summarize(self, goal: str, completed_steps: list, speak: Callable | None) -> str:
        fallback = (
            f"Готово, сэр. Выполнено шагов: {len(completed_steps)} — {goal[:60]}."
        )
        try:
            from google import genai

            client = genai.Client(api_key=_get_api_key())
            steps_str = "\n".join(f"- {s.get('description', '')}" for s in completed_steps)
            prompt = (
                f'User goal: "{goal}"\n'
                f"Completed steps:\n{steps_str}\n\n"
                "Write a single natural sentence in Russian summarizing what was "
                "accomplished. Address the user as 'сэр'. Be direct and positive."
            )
            response = client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=prompt,
            )
            summary = response.text.strip()
            if speak:
                speak(summary)
            return summary
        except Exception:
            if speak:
                speak(fallback)
            return fallback
