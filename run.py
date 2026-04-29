"""Signal & Stance launcher.

Usage:
    python run.py                     # Uses default tenant (first in tenants/)
    python run.py --tenant dana-wang  # Uses specific tenant
    python run.py --list              # Lists available tenants
"""

import argparse
import os
import sys


def get_tenants_dir():
    return os.path.join(os.path.dirname(__file__), "tenants")


def list_tenants():
    tenants_dir = get_tenants_dir()
    tenants = []
    for name in sorted(os.listdir(tenants_dir)):
        tenant_path = os.path.join(tenants_dir, name)
        config_path = os.path.join(tenant_path, "business_config.json")
        if os.path.isdir(tenant_path) and os.path.exists(config_path) and name != "_template":
            tenants.append(name)
    return tenants


def main():
    parser = argparse.ArgumentParser(description="Signal & Stance launcher")
    parser.add_argument("--tenant", "-t", help="Tenant directory name")
    parser.add_argument("--list", "-l", action="store_true", help="List available tenants")
    args = parser.parse_args()

    if args.list:
        tenants = list_tenants()
        if tenants:
            print("Available tenants:")
            for t in tenants:
                print(f"  - {t}")
        else:
            print("No tenants found. Create one in tenants/ using _template as a guide.")
        sys.exit(0)

    # Select tenant
    tenants = list_tenants()
    if args.tenant:
        if args.tenant not in tenants:
            print(f"Tenant '{args.tenant}' not found. Available: {', '.join(tenants)}")
            sys.exit(1)
        tenant_name = args.tenant
    elif tenants:
        tenant_name = tenants[0]
        print(f"No tenant specified, using: {tenant_name}")
    else:
        print("No tenants found. Create one in tenants/ using _template as a guide.")
        sys.exit(1)

    tenant_path = os.path.join(get_tenants_dir(), tenant_name)

    # Set environment variable so framework code knows which tenant to load
    os.environ["SIGNALSTANCE_TENANT_DIR"] = tenant_path

    # Add framework to Python path
    framework_dir = os.path.join(os.path.dirname(__file__), "framework")
    sys.path.insert(0, framework_dir)

    # Import and run the app. Surface tenant config problems as a one-line
    # error rather than a stack trace. Match by class name so we don't have
    # to import ConfigError from a module that may itself be the source of
    # the failure.
    try:
        from app import app, print_auth_banner
        from config import BIND_HOST, FLASK_PORT
    except Exception as e:
        if type(e).__name__ == "ConfigError":
            print(f"Config error: {e}", file=sys.stderr)
            sys.exit(1)
        raise

    print_auth_banner()

    app.run(
        debug=os.getenv("FLASK_DEBUG", "false").lower() == "true",
        host=BIND_HOST,
        port=FLASK_PORT,
    )


if __name__ == "__main__":
    main()
