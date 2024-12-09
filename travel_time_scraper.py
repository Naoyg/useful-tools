import re

import requests
from bs4 import BeautifulSoup


def fetch_page(url: str, params: dict, headers: dict) -> str:
    """Fetch the web page and return the response if successful"""
    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()  # Raise HTTPError for bad responses
    return response.text


def parse_travel_time(page_content: str) -> str:
    """Parse the travel time from the page content"""
    soup = BeautifulSoup(page_content, "html.parser")
    time_element = soup.select_one("li.time > span.small")
    if time_element:
        return time_element.get_text()
    return "Could not find travel time"


def get_travel_time(departure_station: str, arrival_station: str) -> int | None:
    """Get travel time (minutes) between two stations from Yahoo Transit"""
    url = "https://transit.yahoo.co.jp/search/result"
    params = {
        "from": departure_station,
        "to": arrival_station,
        "hh": "07",
        "m1": "3",
        "m2": "0",
        "al": "0",
        "shin": "0",
        "ex": "0",
        "hb": "0",
        "lb": "1",
        "sr": "0",
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }

    try:
        page_content = fetch_page(url, params, headers)
        travel_time = parse_travel_time(page_content)
        travel_time_minutes = convert_time_to_minutes(travel_time)
        return travel_time_minutes
    except requests.RequestException as e:
        print(f"Error: Could not retrieve data ({e})")
        return None


def convert_time_to_minutes(time_str: str) -> int:
    # 正規表現で時間と分を抽出
    match = re.match(r"((?P<hours>\d+)時間)?((?P<minutes>\d+)分)?", time_str)
    if not match:
        raise ValueError("Invalid time format")

    hours = int(match.group("hours")) if match.group("hours") else 0
    minutes = int(match.group("minutes")) if match.group("minutes") else 0

    total_minutes = hours * 60 + minutes
    return total_minutes


def main() -> None:
    """Main function to get and print travel time"""
    # 出発駅と到着駅を指定
    departure_station = "押上"
    arrival_station = "半蔵門"

    travel_time = get_travel_time(departure_station, arrival_station)
    print(
        f"Travel time from {departure_station} to {arrival_station} is: {travel_time} minutes"
    )


if __name__ == "__main__":
    main()
