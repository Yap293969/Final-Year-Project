<?php
// GET api/me.php
// Answer: {"ok": true, "user": {...}}  when logged in,
//         {"ok": true, "user": null}   when not.
// Every page asks this (js/auth.js) to decide whether the header shows
// "Log in" or the user's name.

require __DIR__ . '/_bootstrap.php';
require_method('GET');

$id = current_user_id();
$user = $id === null ? null : find_user($id);

if ($id !== null && $user === null) {
    // The account was deleted while this session was open.
    $_SESSION = [];
}

send_json(200, ['ok' => true, 'user' => $user ? public_user($user) : null]);
