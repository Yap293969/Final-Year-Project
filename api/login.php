<?php
// POST api/login.php
// Sent:   {"email": "...", "password": "..."}
// Answer: {"ok": true, "user": {...}}
// Errors: 401 "Email or password is wrong." -- the same message whichever one is wrong,
//         so the page never reveals which emails have an account.

require __DIR__ . '/_bootstrap.php';
require_method('POST');

$data = read_json();
$email    = strtolower(text_field($data, 'email'));
$password = is_string($data['password'] ?? null) ? $data['password'] : '';

if ($email === '' || $password === '') {
    send_error(400, 'Enter your email and password.');
}

$stmt = db()->prepare('SELECT id, password_hash FROM users WHERE email = ?');
$stmt->execute([$email]);
$row = $stmt->fetch();

if (!$row || !password_verify($password, $row['password_hash'])) {
    send_error(401, 'Email or password is wrong.');
}

$userId = (int) $row['id'];

// If PHP's default hashing has become stronger since this password was saved, upgrade it.
if (password_needs_rehash($row['password_hash'], PASSWORD_DEFAULT)) {
    db()->prepare('UPDATE users SET password_hash = ? WHERE id = ?')
        ->execute([password_hash($password, PASSWORD_DEFAULT), $userId]);
}
db()->prepare('UPDATE users SET last_login_at = NOW() WHERE id = ?')->execute([$userId]);

log_in($userId);
send_json(200, ['ok' => true, 'user' => public_user(find_user($userId))]);
