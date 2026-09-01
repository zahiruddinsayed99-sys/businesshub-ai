with open("backend/tests/test_lms_learner.py", "r") as f:
    content = f.read()

content = content.replace("/api/v1/lms/catalog/courses", "/api/v1/lms/catalog")

import re

# Match the old post call
pattern_post1 = r"response = await async_client\.post\(\s*f\"/api/v1/lms/catalog/\{course\.id\}/lessons/\{lesson\.id\}/complete\",\s*headers=\{\"Authorization\": f\"Bearer \{token\}\", \"X-Organization-Id\": str\(org_id\)\}\s*\)"
new_post1 = """response = await async_client.post(
        f"/api/v1/lms/lessons/{lesson.id}/progress",
        headers={"Authorization": f"Bearer {token}", "X-Organization-Id": str(org_id)},
        json={"is_completed": True}
    )"""
content = re.sub(pattern_post1, new_post1, content)
content = content.replace('assert response.json()["status"] == "COMPLETED"', 'assert response.json()["is_completed"] == True')
content = content.replace("/api/v1/lms/catalog/quizzes/{quiz.id}/attempts", "/api/v1/lms/quizzes/attempts?quiz_id={quiz.id}")

with open("backend/tests/test_lms_learner.py", "w") as f:
    f.write(content)
