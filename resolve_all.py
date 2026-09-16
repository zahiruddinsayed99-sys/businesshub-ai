import os
import re

def resolve_file(filepath):
    if not os.path.exists(filepath):
        return

    with open(filepath, 'r') as f:
        content = f.read()

    # For conftest.py, we know exactly what it should look like (keep HEAD's db_cleanup, NullPool, test_engine drop_all/create_all)
    if filepath == "backend/tests/conftest.py":
        # Keep HEAD for the create_all block
        content = re.sub(r'<<<<<<< HEAD\n(.*?)\n=======\n(.*?)\n>>>>>>> origin/develop\n', r'\1\n', content, flags=re.DOTALL)
        # However, for CrmDeal import, it was an accident in HEAD, so remove it
        content = content.replace("from app.domain.models.crm_deal import CrmDeal\n", "")

    # For backend test files, HEAD has our test infrastructure fixes (mock bg tasks, NullPool, TRUNCATE cascade, IDOR fixes).
    # We want to KEEP HEAD (current change) for test_crm_ai_endpoints.py, test_database_migrations.py, test_billing_integration.py
    elif filepath.startswith("backend/tests/"):
        content = re.sub(r'<<<<<<< HEAD\n(.*?)\n=======\n(.*?)\n>>>>>>> origin/develop\n', r'\1\n', content, flags=re.DOTALL)

    # For backend/app/api/v1/endpoints/billing.py
    # We want to keep HEAD (which has our new upgrade endpoint)
    elif filepath == "backend/app/api/v1/endpoints/billing.py":
        content = re.sub(r'<<<<<<< HEAD\n(.*?)\n=======\n(.*?)\n>>>>>>> origin/develop\n', r'\1\n', content, flags=re.DOTALL)

    # For frontend components
    # We want to keep HEAD which has our new UI implementation
    elif filepath.startswith("frontend/"):
        content = re.sub(r'<<<<<<< HEAD\n(.*?)\n=======\n(.*?)\n>>>>>>> origin/develop\n', r'\1\n', content, flags=re.DOTALL)

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
