with open("backend/tests/test_crm_ai_endpoints.py", "r") as f:
    content = f.read()

content = content.replace('user, token = await create_user_and_token(db_session, mock_redis, f"user-{uuid.uuid4()}@crmai.com", org, "OWNER")', 'user, token = await create_user_and_token(db_session, mock_redis, f"user-{uuid.uuid4()}@crmai.com", org, "OWNER")')
content = content.replace('user, token = await create_user_and_token(db_session, mock_redis, f"draft-{uuid.uuid4()}@crmai.com", org, "OWNER")', 'user, token = await create_user_and_token(db_session, mock_redis, f"draft-{uuid.uuid4()}@crmai.com", org, "OWNER")')

with open("backend/tests/test_crm_ai_endpoints.py", "w") as f:
    f.write(content)
