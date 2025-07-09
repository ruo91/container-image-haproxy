#!/usr/bin/env python3

import argparse
from jinja2 import Template
import subprocess
import re
import os
import sys

def get_multus_ip(interface='net1'):
    """
    Retrieve the IP address of a specified interface (default: net1).
    If unavailable, return fallback "*".
    """
    try:
        result = subprocess.check_output(['ip', '-4', 'addr', 'show', interface], universal_newlines=True)
        match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', result)
        if match:
            return match.group(1)
    except Exception as e:
        print(f"[WARN] Could not determine Multus IP from interface '{interface}': {e}")
    return "*"

def to_hex_escape(s):
    """
    Convert a string to HAProxy-compatible hex-escaped form.
    Example: "AUTH admin password\r\n" -> "\\x41\\x55..."
    """
    return ''.join(f'\\x{ord(c):02x}' for c in s)

def main():
    parser = argparse.ArgumentParser(
        description="Render HAProxy config from Jinja2 template with Multus IP, Redis User, and Redis Password (hex encoded AUTH line)."
    )
    parser.add_argument("--template", required=True, help="Path to the input Jinja2 template file")
    parser.add_argument("--output", required=True, help="Path to write the rendered haproxy.cfg")
    parser.add_argument("--interface", default="net1", help="Multus interface name (default: net1)")

    args = parser.parse_args()

    # Retrieve Multus IP
    MULTUS_IP = get_multus_ip(args.interface)

    # Get Redis user and password from environment
    REDIS_USER = os.environ.get("REDIS_USER", "").strip()
    REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD", "").strip()

    if not REDIS_USER:
        print("[WARN] REDIS_USER environment variable is not set. Defaulting to empty string.")
    if not REDIS_PASSWORD:
        print("[WARN] REDIS_PASSWORD environment variable is not set. Defaulting to empty string.")

    # Create single-line AUTH command
    auth_command = f"AUTH {REDIS_USER} {REDIS_PASSWORD}\r\n"
    AUTH_HEX = to_hex_escape(auth_command)

    #print(f"[INFO] AUTH command (raw): {auth_command.strip()}")
    #print(f"[INFO] AUTH command (hex): {AUTH_HEX}")

    # Load Jinja2 template
    try:
        with open(args.template, "r") as f:
            template_content = f.read()
            template = Template(template_content)
    except Exception as e:
        print(f"[ERROR] Failed to read template from {args.template}: {e}")
        sys.exit(1)

    # Render template
    try:
        rendered = template.render(
            MULTUS_IP=MULTUS_IP,
            REDIS_USER=REDIS_USER,
            REDIS_PASSWORD=REDIS_PASSWORD,
            AUTH_HEX=AUTH_HEX
        ).rstrip() + "\n"
    except Exception as e:
        print(f"[ERROR] Failed to render template: {e}")
        sys.exit(1)

    # Write output
    try:
        with open(args.output, "w") as f:
            f.write(rendered)
        os.chmod(args.output, 0o644)
        print(f"[INFO] haproxy.cfg successfully written to {args.output}")
    except Exception as e:
        print(f"[ERROR] Failed to write {args.output}: {e}")
        sys.exit(1)

    # Verify
    if os.path.exists(args.output):
        size = os.path.getsize(args.output)
        print(f"[INFO] File check OK: {args.output} exists (size: {size} bytes)")
    else:
        print(f"[ERROR] File check FAILED: {args.output} does not exist")
        sys.exit(1)

    # Final log
    print(f"[INFO] Multus IP used: {MULTUS_IP}")
    print(f"[INFO] Redis user: {REDIS_USER}")

if __name__ == "__main__":
    main()
