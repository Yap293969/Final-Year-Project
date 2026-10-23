<?php
// POST api/logout.php
// Sent:   {}  (any JSON)
// Answer: {"ok": true}  -- the session is ended and its cookie removed.

require __DIR__ . '/_bootstrap.php';
require_method('POST');
read_json();

$_SESSION = [];
$params = session_get_cookie_params();
setcookie(session_name(), '', [
    'expires'  => time() - 3600,
    'path'     => $params['path'],
    'httponly' => true,
    'samesite' => 'Lax',
    'secure'   => $params['secure'],
]);
session_destroy();

send_json(200, ['ok' => true]);
