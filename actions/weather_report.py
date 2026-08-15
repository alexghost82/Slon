# actions/weather_report.py

import webbrowser
from urllib.parse import quote_plus


def weather_action(
    parameters: dict,
    player=None,
    session_memory=None
):
    """
    Weather report action.
    Opens a Google weather search and gives a short spoken confirmation.
    """

    city = parameters.get("city")
    time = parameters.get("time")
    if not city or not isinstance(city, str):
        msg = "Сэр, для прогноза погоды не указан город."
        _speak_and_log(msg, player)
        return msg

    city = city.strip()

    if not time or not isinstance(time, str):
        time = "сегодня"
    else:
        time = time.strip()

    search_query = f"погода {city} {time}"
    encoded_query = quote_plus(search_query)
    url = f"https://www.google.com/search?q={encoded_query}"

    try:
        webbrowser.open(url)
    except Exception:
        msg = "Сэр, не удалось открыть браузер для прогноза погоды."
        _speak_and_log(msg, player)
        return msg

    msg = f"Показываю погоду: {city}, {time}, сэр."
    _speak_and_log(msg, player)

    if session_memory:
        try:
            session_memory.set_last_search(
                query=search_query,
                response=msg
            )
        except Exception:
            pass  

    return msg


def _speak_and_log(message: str, player=None):
    if player:
        try:
            from localization import tr

            player.write_log(f"{tr('log.prefix_assistant')} {message}")
        except Exception:
            pass