import sys

def fix_indent(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        if "redis = await get_redis_client()" in line:
            lines[i] = "    redis = await get_redis_client()\n"

    with open(filepath, 'w') as f:
        f.writelines(lines)

if __name__ == "__main__":
    fix_indent("backend/tests/test_billing_integration.py")
