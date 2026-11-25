"""WebPulse Lite (Free Open-Source Edition) — Quick single-URL SSL, status & title check.

Full multi-page broken-link crawler, 6 security headers audit, adaptive EN/zh-TW HTML
client reports & GitHub Actions workflow: https://taijibalaadmin.gumroad.com/l/millyq
"""

from __future__ import annotations

import argparse
import html
import re
import socket
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone


def check_site(raw_url: str, timeout: float = 8.0) -> int:
    url = raw_url.strip()
    if "://" not in url:
        url = f"https://{url}"
    parsed = urllib.parse.urlparse(url)
    req = urllib.request.Request(url, headers={"User-Agent": "WebPulse-Lite/1.0"})

    start = time.perf_counter()
    try:
        if parsed.hostname in ("127.0.0.1", "localhost", "::1"):
            cm = urllib.request.build_opener(urllib.request.ProxyHandler({})).open(req, timeout=timeout)
        else:
            cm = urllib.request.urlopen(req, timeout=timeout)
        with cm as resp:
            ttfb_ms = round((time.perf_counter() - start) * 1000, 1)
            body = resp.read(200_000).decode("utf-8", errors="replace")
            status = resp.status
            final_url = resp.geturl()
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        print(f"[FAIL] Could not reach {url}: {exc}")
        return 2

    title_match = re.search(r"<title[^>]*>(.*?)</title>", body, re.IGNORECASE | re.DOTALL)
    title = html.unescape(" ".join(title_match.group(1).split())) if title_match else "(missing)"

    ssl_info = "Plain HTTP (no TLS)"
    if urllib.parse.urlparse(final_url).scheme == "https":
        host = urllib.parse.urlparse(final_url).hostname or ""
        try:
            ctx = ssl.create_default_context()
            with socket.create_connection((host, 443), timeout=timeout) as sock:
                with ctx.wrap_socket(sock, server_hostname=host) as tls:
                    cert = tls.getpeercert()
            exp = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
            days_left = (exp - datetime.now(timezone.utc)).days
            ssl_info = f"Valid ({days_left} days left, expires {exp.date()})"
        except (ssl.SSLError, OSError, KeyError) as exc:
            ssl_info = f"TLS Error: {exc}"

    print(f"URL      : {final_url}")
    print(f"Status   : HTTP {status} ({ttfb_ms} ms TTFB)")
    print(f"SSL/TLS  : {ssl_info}")
    print(f"Title    : {title}")
    print("\nNeed multi-page broken-link crawling, 6 security headers & adaptive EN/繁中 HTML client reports?")
    print("-> WebPulse Audit Kit ($9): https://taijibalaadmin.gumroad.com/l/millyq")
    return 0 if 200 <= status < 400 else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="WebPulse Lite — Free single-URL quick check.")
    parser.add_argument("url", help="Target URL to inspect")
    args = parser.parse_args()
    return check_site(args.url)


if __name__ == "__main__":
    raise SystemExit(main())
