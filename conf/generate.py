import argparse
from jinja2 import Template
import subprocess
import re
import os
import sys

def get_multus_ip(interface='net1'):
    """
    Retrieve the IP address of a specified interface (default: net1).
    If unavailable, return fallback IP 0.0.0.0.
    """
    try:
        result = subprocess.check_output(['ip', '-4', 'addr', 'show', interface], universal_newlines=True)
        match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', result)
        if match:
            return match.group(1)
    except Exception as e:
        print(f"[ERROR] Could not determine Multus IP from interface '{interface}': {e}")
    return "*"

def main():
    parser = argparse.ArgumentParser(description="Render HAProxy config from Jinja2 template with Multus IP.")
    parser.add_argument("--template", required=True, help="Path to the input Jinja2 template file")
    parser.add_argument("--output", required=True, help="Path to write the rendered haproxy.cfg")
    parser.add_argument("--interface", default="net1", help="Multus interface name (default: net1)")

    args = parser.parse_args()

    MULTUS_IP = get_multus_ip(args.interface)

    # Step 1: Load the Jinja2 template file
    try:
        with open(args.template, "r") as f:
            template = Template(f.read())
    except Exception as e:
        print(f"[ERROR] Failed to read template from {args.template}: {e}")
        sys.exit(1)

    # Step 2: Render the template with the Multus IP and ensure trailing newline
    try:
        rendered = template.render(MULTUS_IP=MULTUS_IP).rstrip() + "\n"
    except Exception as e:
        print(f"[ERROR] Failed to render template: {e}")
        sys.exit(1)

    # Step 3: Write the rendered output to the specified output file
    try:
        with open(args.output, "w") as f:
            f.write(rendered)
        os.chmod(args.output, 0o644)
        print(f"[INFO] haproxy.cfg successfully written to {args.output}")
    except Exception as e:
        print(f"[ERROR] Failed to write {args.output}: {e}")
        sys.exit(1)

    # Step 4: Verify that the file exists and display its size
    if os.path.exists(args.output):
        size = os.path.getsize(args.output)
        print(f"[INFO] File check OK: {args.output} exists (size: {size} bytes)")
    else:
        print(f"[ERROR] File check FAILED: {args.output} does not exist")
        sys.exit(1)

    # Step 5: Display the resolved Multus IP
    print(f"[INFO] Multus IP used: {MULTUS_IP}")

if __name__ == "__main__":
    main()
