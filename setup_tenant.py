"""Create a new tenant from the template."""

import os
import shutil
import sys


def main():
    if len(sys.argv) < 2:
        print("Usage: python setup_tenant.py <tenant-name>")
        print("Example: python setup_tenant.py alex-chen")
        sys.exit(1)

    tenant_name = sys.argv[1]
    tenants_dir = os.path.join(os.path.dirname(__file__), "tenants")
    template_dir = os.path.join(tenants_dir, "_template")
    target_dir = os.path.join(tenants_dir, tenant_name)

    if os.path.exists(target_dir):
        print(f"Tenant '{tenant_name}' already exists at {target_dir}")
        sys.exit(1)

    if not os.path.exists(template_dir):
        print(f"Template directory not found at {template_dir}")
        sys.exit(1)

    shutil.copytree(template_dir, target_dir)
    os.makedirs(os.path.join(target_dir, "generated_carousels"), exist_ok=True)

    print(f"Created tenant: {target_dir}")
    print(f"\nNext steps:")
    print(f"  1. Edit {os.path.join(target_dir, 'business_config.json')} with your business details")
    print(f"  2. Add RSS feeds to {os.path.join(target_dir, 'feeds.json')}")
    print(f"  3. Write your voice profile in {os.path.join(target_dir, 'prompts', 'base_system.md')}")
    print(f"  4. Customize remaining prompt files in {os.path.join(target_dir, 'prompts')}")
    print(f"  5. Run: python run.py --tenant {tenant_name}")


if __name__ == "__main__":
    main()
