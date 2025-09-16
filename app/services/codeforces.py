import requests


BASE_URL = "https://codeforces.com/api/"

def verify_handle(handle: str) -> bool:
    """Check if a codeforces handle exists."""
    print("validating user", handle)
    try:
        r = requests.get(f"{BASE_URL}user.info", params={"handles": handle}, timeout=5)
        print("response json:", r.json())
        data = r.json()
        return data.get("status") == "OK"
    except Exception as e:
        print(f"Error verifying handle: {e}")
        return False


def get_codeforces_standings_handles(contest_link: str) -> set[str]:
    """
    Placeholder: returns a set of Codeforces handles that actually competed.
    Later you can integrate the Codeforces API here.
    """
    # Example mock result:
    return set()