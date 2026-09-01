with open("backend/tests/test_lms_learner.py", "r") as f:
    content = f.read()

content = content.replace("/api/v1/lms/catalog/courses", "/api/v1/lms/catalog")
content = content.replace("/api/v1/lms/catalog/quizzes/{quiz.id}/attempts", "/api/v1/lms/quizzes/attempts?quiz_id={quiz.id}")

old_post = """    response = await async_client.post(
        f"/api/v1/lms/catalog/{course.id}/lessons/{lesson.id}/complete",
        headers={"Authorization": f"Bearer {token}", "X-Organization-Id": str(org_id)}
    )"""

new_post = """    response = await async_client.post(
        f"/api/v1/lms/lessons/{lesson.id}/progress",
        headers={"Authorization": f"Bearer {token}", "X-Organization-Id": str(org_id)},
        json={"is_completed": True}
    )"""

content = content.replace(old_post, new_post)

with open("backend/tests/test_lms_learner.py", "w") as f:
    f.write(content)
