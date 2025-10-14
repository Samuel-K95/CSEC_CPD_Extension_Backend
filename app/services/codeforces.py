import re, httpx, asyncio


BASE_URL = "https://codeforces.com/api/"

async def verify_handle(handle: str) -> bool:
    """Check if a codeforces handle exists."""
    print("validating user", handle)
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{BASE_URL}user.info", params={"handles": handle}, timeout=5)
            print("response json:", r.json())
            data = r.json()
            return data.get("status") == "OK"
    except Exception as e:
        print(f"Error verifying handle: {e}")
        return False

def extract_contest_id(contest_link: str) -> str:
    """
    Extracts the contest ID from a Codeforces contest link.
    Example: "https://codeforces.com/contest/1234" -> "1234"
    """
    match = re.search(r'/(\d+)(?:/)?$', contest_link)
    if match:
        return match.group(1)
    raise ValueError("Invalid Codeforces contest link")


async def get_codeforces_standings_handles(contest_link: str, as_manager: bool = False, from_row: int = 1, count: int = 0, show_unofficial: bool = True) -> dict:
    """
    Fetches contest standings from Codeforces API and returns a dictionary
    mapping user handles to their rank.
    """
    print("getting codeforces standings", contest_link)
    contest_id = extract_contest_id(contest_link)
    params = {
        "contestId": contest_id,
        "asManager": as_manager,
        "from": from_row,
        "showUnofficial": show_unofficial,
    }
    if count > 0:
        params["count"] = count

    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{BASE_URL}contest.standings", params=params, timeout=10)
            r.raise_for_status()  # Raise an exception for bad status codes
            data = r.json()

        print("response json:", data)
        if data.get("status") != "OK":
            print(f"Error from Codeforces API: {data.get('comment')}")
            return {}

        standings = {}
        for row in data["result"]["rows"]:
            handle = row["party"]["members"][0]["handle"]
            rank = row["rank"]
            standings[handle] = rank


        
        return standings

    except httpx.RequestError as e:
        print(f"Error fetching standings: {e}")
        return {}
    except (KeyError, IndexError) as e:
        print(f"Error parsing standings data: {e}")
        return {}