import json
import random
import re
import time
from collections import namedtuple
from urllib.parse import parse_qs
from urllib.parse import urlparse

import requests
from tqdm import tqdm

# --- networking ------------------------------------------------------------
#
# Every call below goes through _request(). Three things were going wrong on
# large batches (the report that prompted this: a 73-friend removal died
# partway through):
#
#   1. No request ever set a timeout, so a connection that stalled would hang
#      the worker thread forever with no way out.
#   2. PSN rate-limits a burst of back-to-back DELETEs. raise_for_status() turned
#      the first 429 into an exception that aborted the whole remaining batch.
#   3. A single transient failure anywhere in the loop discarded the progress
#      already made, and the caller had no idea who had actually been removed.
#
# So: bounded timeouts, retry with backoff on the statuses that are worth
# retrying, and a removal loop that isolates per-friend failures instead of
# letting one kill the run.

# (connect, read). The read budget is generous because PSN can be slow under
# load, but it is finite - that is the entire point.
DEFAULT_TIMEOUT = (10, 30)

# 429 is rate limiting; the 5xx family is PSN having a bad moment. Both are
# worth retrying. Everything else (401 expired token, 403, 404) is a real
# answer and retrying it just wastes the user's time.
RETRYABLE_STATUS = {429, 500, 502, 503, 504}

MAX_ATTEMPTS = 4
BACKOFF_BASE = 1.5

# Small gap between consecutive removals. Staying under the rate limit is much
# cheaper than being throttled and backing off once we hit it.
REMOVE_DELAY = 0.35

# stopped distinguishes "the user cancelled" from "finished with errors" - the
# two need very different wording in the UI.
RemovalResult = namedtuple("RemovalResult", "removed failures stopped")

# One session for the whole run: without it each of 73 removals pays for a
# fresh TCP + TLS handshake.
_session = requests.Session()


class Stopped(Exception):
    """Raised when the caller cancelled the operation mid-flight.

    Deliberately distinct from a request failure: a removal the user cancelled
    is not an error and must never be reported as one.
    """


def _wait(seconds, stop_event=None):
    """Sleep, waking early if stop_event is set. True means it was cut short.

    Every wait in this module goes through here. A plain time.sleep() would make
    Stop appear frozen for the length of a rate-limit backoff - up to 30s - which
    is exactly when a user is most likely to want out.
    """
    if stop_event is None:
        time.sleep(seconds)
        return False
    return stop_event.wait(seconds)


def _sleep_for(attempt, response=None):
    """Seconds to wait before the next attempt.

    Honours Retry-After when PSN sends one, since the server's own number beats
    anything guessed here. Otherwise exponential backoff with jitter, so a
    retried batch does not resynchronise into another burst.
    """
    if response is not None:
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                return min(float(retry_after), 60.0)
            except ValueError:
                pass
    return min(BACKOFF_BASE ** attempt + random.uniform(0, 0.4), 30.0)


def _request(method, url, stop_event=None, **kwargs):
    """Perform a request with a timeout and bounded retries.

    Raises the last error if every attempt fails, so callers keep the same
    failure semantics they had with raise_for_status(). Raises Stopped if
    stop_event is set while waiting to retry.
    """
    kwargs.setdefault("timeout", DEFAULT_TIMEOUT)
    last_error = None

    for attempt in range(MAX_ATTEMPTS):
        response = None
        try:
            response = _session.request(method, url, **kwargs)
        except (requests.Timeout, requests.ConnectionError) as e:
            last_error = e
        else:
            if response.status_code not in RETRYABLE_STATUS:
                response.raise_for_status()
                return response
            last_error = requests.HTTPError(
                f"{response.status_code} from {url}", response=response)

        if attempt == MAX_ATTEMPTS - 1:
            break
        if _wait(_sleep_for(attempt, response), stop_event):
            raise Stopped("cancelled while waiting to retry")

    raise last_error


def obtain_auth_code(npsso_token):
    url = "https://ca.account.sony.com/api/authz/v3/oauth/authorize"
    headers = {
        "Cookie": f"npsso={npsso_token}"
    }
    params = {
        "access_type": "offline",
        "client_id": "09515159-7237-4370-9b40-3806e67c0891",
        "scope": "psn:mobile.v2.core psn:clientapp",
        "redirect_uri": "com.scee.psxandroid.scecompcall://redirect",
        "response_type": "code",
    }
    response = _request(
        "GET",
        url,
        headers=headers,
        params=params,
        allow_redirects=False,
    )

    location_url = response.headers["location"]
    parsed_url = urlparse(location_url)
    parsed_qs = parse_qs(parsed_url.query)

    code = parsed_qs['code'][0]
    return code


def obtain_auth_jwt(code):
    url = "https://ca.account.sony.com/api/authz/v3/oauth/token"
    body = {
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": "com.scee.psxandroid.scecompcall://redirect",
        "scope": "psn:mobile.v2.core psn:clientapp",
        "token_format": "jwt",
    }
    headers = {
        "Authorization": "Basic MDk1MTUxNTktNzIzNy00MzcwLTliNDAtMzgwNmU2N2MwODkxOnVjUGprYTV0bnRCMktxc1A="
    }
    response = _request(
        "POST",
        url,
        headers=headers,
        data=body
    )

    auth_resp_json = response.json()
    return auth_resp_json["access_token"]


def authenticate_with_npsso_token(npsso_token):
    code = obtain_auth_code(npsso_token)
    access_token = obtain_auth_jwt(code)
    return access_token


def get_friend_list(jwt_token):
    url = "https://m.np.playstation.com/api/userProfile/v1/internal/users/me/friends"
    params = {
        "limit": 1000
    }
    headers = {
        "Content-Type": "application/json",
        "accept-language": "en-US",
        "user-agent": "okhttp/4.9.2",
        "Authorization": f"Bearer {jwt_token}"
    }

    response = _request("GET", url, params=params, headers=headers)

    response_json = response.json()
    return response_json['friends']


def profile_ids_to_names_chunked(jwt_token, profile_ids, start=0):
    url = "https://m.np.playstation.com/api/userProfile/v1/internal/users/profiles"
    params = {
        "accountIds": ",".join(profile_ids[start:start + 100])
    }
    headers = {
        "Content-Type": "application/json",
        "accept-language": "en-US",
        "user-agent": "okhttp/4.9.2",
        "Authorization": f"Bearer {jwt_token}"
    }
    response = _request("GET", url, params=params, headers=headers)

    response_json = response.json()
    return response_json['profiles']


def profile_ids_to_names(jwt_token, profile_ids):
    to_return = []

    chunk_size = 100
    num_chunks = len(profile_ids) // chunk_size

    for i in range(num_chunks + 1):
        start_index = i * chunk_size

        if profile_ids[start_index:start_index + 100]:
            to_return.extend(profile_ids_to_names_chunked(jwt_token, profile_ids, start_index))
    return to_return


def remove_friend(jwt_token, profile_id, stop_event=None):
    url = f"https://m.np.playstation.com/api/userProfile/v1/internal/users/me/friends/{profile_id}"
    headers = {
        "Content-Type": "application/json",
        "accept-language": "en-US",
        "user-agent": "okhttp/4.9.2",
        "Authorization": f"Bearer {jwt_token}"
    }
    _request("DELETE", url, headers=headers, stop_event=stop_event)


def is_name_whitelisted(patterns, name):
    for pattern in patterns:
        if re.match(pattern, name):
            return True
    return False


def get_friends_with_names(auth, whitelist_patterns):
    friend_ids = get_friend_list(auth)
    profiles = profile_ids_to_names(auth, friend_ids)
    names = [p['onlineId'] for p in profiles]
    friends_zip = zip(friend_ids, names)
    friend_ids_with_onlineIds = list(friends_zip)
    to_remove = []
    to_keep = []
    for friend in friend_ids_with_onlineIds:
        friend_id, friend_name = friend
        if is_name_whitelisted(whitelist_patterns, friend_name):
            to_keep.append(friend)
        else:
            to_remove.append(friend)
    return to_keep, to_remove


def remove_friends(auth, friends, progress_callback=None, delay=REMOVE_DELAY,
                   stop_event=None):
    """Remove each friend in turn, isolating per-friend failures.

    Returns a RemovalResult: .removed is the friend tuples PSN actually
    accepted, .failures is a list of (friend, error_message), and .stopped says
    whether the run ended early because the caller cancelled it.

    A failure no longer aborts the batch. Previously one 429 partway through a
    long run raised out of the loop, so the friends already removed were left
    unreported and the rest were silently skipped - which is what a caller saw
    as the whole operation "timing out".

    stop_event is an optional threading.Event. It is checked between removals
    and interrupts the throttle and retry waits, so cancelling takes effect
    immediately rather than after a backoff finishes. Whatever was removed
    before the stop is still returned - the removals are already permanent, so
    the caller must be told about them.
    """
    removed = []
    failures = []
    stopped = False
    total = len(friends)

    for idx, friend in enumerate(friends):
        if stop_event is not None and stop_event.is_set():
            stopped = True
            break

        try:
            remove_friend(auth, friend[0], stop_event=stop_event)
            removed.append(friend)
        except Stopped:
            # Cancelled, not failed. Must be caught ahead of the generic
            # handler below or the friend lands in the failure report.
            stopped = True
            break
        except Exception as e:
            failures.append((friend, str(e)))

        if progress_callback:
            progress_callback(idx + 1, total)

        # Throttle between requests, not after the last one.
        if delay and idx + 1 < total:
            if _wait(delay, stop_event):
                stopped = True
                break

    return RemovalResult(removed, failures, stopped)


if __name__ == '__main__':
    try:
        with open("configuration.json", 'r') as file:
            config = json.load(file)
    except FileNotFoundError:
        print("configuration.json file not found. Did you forget to rename the example file?")
        exit(1)

    auth = authenticate_with_npsso_token(config['npsso_token'])

    friend_ids = get_friend_list(auth)

    print(f"Found {len(friend_ids)} friends")

    profiles = profile_ids_to_names(auth, friend_ids)
    names = [p['onlineId'] for p in profiles]

    friends_zip = zip(friend_ids, names)
    friend_ids_with_onlineIds = list(friends_zip)

    to_remove = []
    to_keep = []

    for friend in friend_ids_with_onlineIds:
        friend_id, friend_name = friend

        if is_name_whitelisted(config['nameWhitelistPatterns'], friend_name):
            to_keep.append(friend)
        else:
            to_remove.append(friend)

    print(f"\nFriends to remove ({len(to_remove)}): ")
    print('\n'.join([p[1] for p in to_remove]))

    print(f"\nFriends to keep ({len(to_keep)}): ")
    print('\n'.join([p[1] for p in to_keep]))

    if input("\nValidate the output above. Continue? (y/n)") != "y":
        exit(1)

    print(f"\nRemoving {len(to_remove)} friends...")
    with tqdm(total=len(to_remove)) as bar:
        result = remove_friends(
            auth, to_remove, progress_callback=lambda done, total: bar.update(1))

    if result.stopped:
        print(f"\nStopped. Removed {len(result.removed)} of {len(to_remove)} "
              "friends before cancelling.")
    else:
        print(f"\nRemoved {len(result.removed)} of {len(to_remove)} friends.")
    if result.failures:
        print(f"\n{len(result.failures)} could not be removed:")
        for friend, error in result.failures:
            print(f"  {friend[1]} ({friend[0]}): {error}")
