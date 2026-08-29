UPDATE user_roles SET role = 'SUPER_ADMIN' WHERE user_id = (SELECT id FROM users WHERE email = 'YOUR_TEST_EMAIL@example.com');
