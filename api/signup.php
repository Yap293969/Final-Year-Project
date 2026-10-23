<?php
// POST api/signup.php
// Sent:   {"email": "...", "first_name": "...", "last_name": "...", "password": "..."}
// Answer: {"ok": true, "user": {...}}  and the new user is logged in straight away.
// Errors: 400 with a message the page shows next to the form; 409 if the email is taken.

require __DIR__ . '/_bootstrap.php';
require_method('POST');

$data = read_json();
$c = config();

$email     = strtolower(text_field($data, 'email'));
$firstName = text_field($data, 'first_name');
$lastName  = text_field($data, 'last_name');
// The password is not trimmed: spaces are allowed and count.
$password  = is_string($data['password'] ?? null) ? $data['password'] : '';

$errors = [];
if ($email === '' || strlen($email) > 254 || filter_var($email, FILTER_VALIDATE_EMAIL) === false) {
    $errors['email'] = 'Enter a valid email address, like name@example.com.';
}
foreach (['first_name' => [$firstName, 'first name'], 'last_name' => [$lastName, 'last name']] as $key => [$value, $label]) {
    if ($value === '') {
        $errors[$key] = 'Enter your ' . $label . '.';
    } elseif (mb_strlen($value) > $c['name_max_length']) {
        $errors[$key] = 'Your ' . $label . ' can be at most ' . $c['name_max_length'] . ' characters.';
    } elseif (preg_match('/[\p{C}<>]/u', $value)) {
        $errors[$key] = 'Your ' . $label . ' contains characters that are not allowed.';
    }
}
if (mb_strlen($password) < $c['password_min_length']) {
    $errors['password'] = 'Use at least ' . $c['password_min_length'] . ' characters.';
} elseif (strlen($password) > 72) {
    // bcrypt, which password_hash() uses, only reads the first 72 bytes.
    $errors['password'] = 'Use at most 72 characters.';
}

if ($errors) {
    send_json(400, ['ok' => false, 'error' => 'Please fix the highlighted fields.', 'fields' => $errors]);
}

$hash = password_hash($password, PASSWORD_DEFAULT);

try {
    $stmt = db()->prepare(
        'INSERT INTO users (email, first_name, last_name, password_hash, last_login_at)
         VALUES (?, ?, ?, ?, NOW())'
    );
    $stmt->execute([$email, $firstName, $lastName, $hash]);
} catch (PDOException $e) {
    if ($e->getCode() === '23000') {   // the UNIQUE index on email
        send_json(409, ['ok' => false, 'error' => 'An account with this email already exists. Try logging in.',
                        'fields' => ['email' => 'This email already has an account.']]);
    }
    throw $e;
}

$userId = (int) db()->lastInsertId();
log_in($userId);
send_json(201, ['ok' => true, 'user' => public_user(find_user($userId))]);
