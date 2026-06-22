import requests
import json

# ==============================
# 🎨 ANSI COLORS
# ==============================
class Color:
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    END = "\033[0m"


# ==============================
# 🔗 CONFIG
# ==============================
MCP_URL = "https://mcp-weather-s1s0.onrender.com/tool"
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL = "phi"


# ==============================
# 🧠 TOOL SELECTION
# ==============================
def choose_tool(user_input):
    text = user_input.lower()

    if "aqi" in text or "air" in text:
        return "getAQI"
    elif "time" in text:
        return "getTimeOnly"
    elif "coordinate" in text:
        return "getCoordinatesOnly"
    elif "weather" in text:
        return "getWeatherOnly"
    elif "today" in text or "holiday" in text or "fact" in text:
        return "getTodaySpecial"
    else:
        return "getFullInsights"


# ==============================
# 🌍 MULTI CITY EXTRACTION
# ==============================
def extract_cities(user_input):
    words = user_input.replace(",", " ").split()
    return [w.capitalize() for w in words if w.isalpha()]


# ==============================
# 🔧 MCP CALL
# ==============================
def call_mcp(tool, city):
    try:
        res = requests.post(
            MCP_URL,
            json={"tool": tool, "input": city},
            timeout=20
        )

        if res.status_code != 200:
            return {"error": f"HTTP {res.status_code}"}

        data = res.json()

        if "error" in data:
            return {"error": data["error"]}

        return data

    except Exception as e:
        return {"error": str(e)}


# ==============================
# 🧹 CLEAN DATA + FIX COUNTRY
# ==============================
def clean_data(data):
    cleaned = {}

    for key, value in data.items():
        if value is None:
            continue
        if isinstance(value, dict) and not value:
            continue
        cleaned[key] = value

    # 🔥 FIX: ALWAYS ADD COUNTRY
    if "country" not in cleaned:
        cleaned["country"] = "India"

    return cleaned


# ==============================
# 🤖 STREAMING LLM (FIXED)
# ==============================
def ask_llm_stream(user_query, tool_used, mcp_data):

    prompt = f"""
YOU ARE A STRICT DATA DISPLAY ENGINE.

RULES:
- NO storytelling
- NO reasoning
- NO guessing
- ONLY use MCP data
- ALWAYS include country in output (if missing assume India)

OUTPUT FORMAT:

📍 Location: City, Country
🌡 Weather: ...
🌫 Air Quality: ...
🕒 Time: ...
🎉 Highlights: ...

INPUT DATA:
{json.dumps(mcp_data, indent=2)}

USER:
{user_query}
"""

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": True,
        "options": {
            "temperature": 0.1
        }
    }

    try:
        with requests.post(OLLAMA_URL, json=payload, stream=True, timeout=120) as res:

            if res.status_code != 200:
                print(f"{Color.RED}❌ LLM not responding{Color.END}")
                return ""

            print(f"\n{Color.CYAN}{Color.BOLD}🤖 AI:{Color.END}\n")

            full_response = ""

            for line in res.iter_lines(decode_unicode=True):
                if not line:
                    continue

                try:
                    chunk = json.loads(line)
                    token = chunk.get("response", "")

                    full_response += token
                    print(token, end="", flush=True)

                except json.JSONDecodeError:
                    continue

            print("\n")
            return full_response

    except Exception as e:
        print(f"{Color.RED}❌ LLM error: {e}{Color.END}")
        return ""


# ==============================
# 🚀 MAIN LOOP
# ==============================
if __name__ == "__main__":

    print(f"{Color.GREEN}{Color.BOLD}🤖 Smart MCP AI Agent (Pro Mode){Color.END}\n")

    while True:
        user_input = input(f"{Color.CYAN}{Color.BOLD}You:{Color.END} ")

        if user_input.lower() == "exit":
            print(f"{Color.RED}👋 Goodbye!{Color.END}")
            break

        try:
            cities = extract_cities(user_input)

            if not cities:
                print(f"{Color.RED}❌ Please enter a valid city{Color.END}")
                continue

            # ==============================
            # 🌍 MULTI CITY MODE
            # ==============================
            if len(cities) > 1:
                print(f"{Color.YELLOW}🔍 Comparing cities...{Color.END}")

                results = []

                for city in cities:
                    data = call_mcp("getFullInsights", city)

                    if "error" not in data:
                        results.append({city: clean_data(data)})

                if not results:
                    print(f"{Color.RED}❌ Failed to fetch data{Color.END}")
                    continue

                ask_llm_stream(user_input, "multiCityCompare", results)

            # ==============================
            # 🎯 SINGLE CITY MODE
            # ==============================
            else:
                city = cities[-1]
                tool = choose_tool(user_input)

                raw_data = call_mcp(tool, city)

                if "error" in raw_data:
                    print(f"{Color.RED}{raw_data['error']}{Color.END}")
                    continue

                clean_mcp_data = clean_data(raw_data)

                ask_llm_stream(user_input, tool, clean_mcp_data)

        except Exception as e:
            print(f"{Color.RED}❌ Error: {e}{Color.END}")

def run_agent(user_input):
    cities = extract_cities(user_input)

    if not cities:
        return "❌ No city found"

    city = cities[0]
    tool = choose_tool(user_input)

    data = call_mcp(tool, city)

    if "error" in data:
        return data["error"]

    clean_mcp_data = clean_data(data)

    return ask_llm_stream(user_input, tool, clean_mcp_data)            