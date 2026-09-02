import sys

def resolve_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # Special handling for conftest.py - accept incoming
    if "conftest.py" in filepath:
        import re
        content = re.sub(r'<<<<<<<.*?\n(.*?)=======\n(.*?)\n>>>>>>>.*?\n', r'\2\n', content, flags=re.DOTALL)
    # For others, we want to keep the local changes (which include the NullPool fixes)
    else:
        import re
        content = re.sub(r'<<<<<<<.*?\n(.*?)=======\n(.*?)\n>>>>>>>.*?\n', r'\1\n', content, flags=re.DOTALL)

    with open(filepath, 'w') as f:
        f.write(content)

if __name__ == "__main__":
    resolve_file("backend/tests/conftest.py")
    resolve_file("backend/tests/test_ai_endpoints.py")
    resolve_file("backend/tests/test_billing_integration.py")
    resolve_file("backend/tests/test_crm_ai_endpoints.py")
    resolve_file("backend/tests/test_database_migrations.py")
    resolve_file("backend/tests/test_lms_learner.py")
