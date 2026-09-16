import os
import re

def resolve_file(filepath):
    if not os.path.exists(filepath):
        return

    with open(filepath, 'r') as f:
        content = f.read()

    # The previous regex didn't catch the empty block because it expected `\n` in group 2
    # `<<<<<<< HEAD\n=======\n>>>>>>> origin/develop\n`
    content = re.sub(r'<<<<<<< HEAD\n(.*?)=======\n(.*?)\n>>>>>>> origin/develop\n?', r'\1\n', content, flags=re.DOTALL)

    # Catch empty HEAD blocks as well
    content = re.sub(r'<<<<<<< HEAD\n=======\n(.*?)\n>>>>>>> origin/develop\n?', r'\1\n', content, flags=re.DOTALL)

    # Catch empty develop blocks
    content = re.sub(r'<<<<<<< HEAD\n(.*?)=======\n>>>>>>> origin/develop\n?', r'\1\n', content, flags=re.DOTALL)

    # Catch completely empty blocks
    content = re.sub(r'<<<<<<< HEAD\n=======\n>>>>>>> origin/develop\n?', r'\n', content, flags=re.DOTALL)

    # Some conflicts were with `jules-feature-billing-upgrade-5600347236651815190` instead of `HEAD`
    content = re.sub(r'<<<<<<< jules-feature-billing-upgrade.*?\n(.*?)=======\n(.*?)\n>>>>>>> develop\n?', r'\1\n', content, flags=re.DOTALL)
    content = re.sub(r'<<<<<<< jules-feature-billing-upgrade.*?\n=======\n(.*?)\n>>>>>>> develop\n?', r'\1\n', content, flags=re.DOTALL)
    content = re.sub(r'<<<<<<< jules-feature-billing-upgrade.*?\n(.*?)=======\n>>>>>>> develop\n?', r'\1\n', content, flags=re.DOTALL)
    content = re.sub(r'<<<<<<< jules-feature-billing-upgrade.*?\n=======\n>>>>>>> develop\n?', r'\n', content, flags=re.DOTALL)


    with open(filepath, 'w') as f:
        f.write(content)

files_to_resolve = [
    "backend/app/api/v1/endpoints/billing.py",
    "backend/tests/conftest.py",
    "backend/tests/test_ai_endpoints.py",
    "backend/tests/test_billing_integration.py",
    "backend/tests/test_crm_ai_endpoints.py",
    "backend/tests/test_database_migrations.py",
    "backend/tests/test_lms_learner.py",
    "backend/tests/test_tier2_api.py",
    "frontend/src/app/features/billing-dashboard/billing-dashboard.component.html",
    "frontend/src/app/features/billing-dashboard/billing-dashboard.component.ts",
    "frontend/src/app/features/billing-dashboard/components/upgrade-modal/upgrade-modal.html",
    "frontend/src/app/features/billing-dashboard/components/upgrade-modal/upgrade-modal.scss"
]

for f in files_to_resolve:
    resolve_file(f)
