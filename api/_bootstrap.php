<?php
// Is this a scam? -- shared start-up code for every api/*.php file.
//
// Each endpoint starts with:  require __DIR__ . '/_bootstrap.php';
// It gives that file:
//   config()            the settings in config.php
//   db()                one PDO connection to MySQL (prepared statements only)
//   read_json()         the JSON the page sent, as an array
//   send_json()         an answer to the page, as JSON, then stops
//   require_method()    refuses any HTTP method the endpoint doesn't use
//   current_user_id()   the logged-in user's id, or null
//   require_login()     the logged-in user's id, or a 401 answer
//   public_user()       the user's details that are safe to send to the page
//
// SAFETY, in plain words
// - Every SQL query uses placeholders (?), so typed-in text can never change a query.
// - Passwords are kept only as password_hash() hashes.
// - The login is a PHP session cookie that page scripts can't read (HttpOnly) and
//   that other websites can't send along (SameSite=Lax).
// - Every POST must be JSON. A form on another website can't send JSON to this
//   API without the browser asking first, which stops cross-site form tricks (CSRF).
// - Errors from MySQL are written to PHP's error log, never sent to the page.

declare(strict_types=1);

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');
header('X-Content-Type-Options: nosniff');

function config(): array
{
    static $config = null;
    if ($config === null) {
        $config = require __DIR__ . '/config.php';
    }
    return $config;
}

function send_json(int $status, array $data): void
{
    http_response_code($status);
    echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    exit;
}

function send_error(int $status, string $message): void
{
    send_json($status, ['ok' => false, 'error' => $message]);
}

function db(): PDO
{
    static $pdo = null;
    if ($pdo === null) {
        $c = config();
        $dsn = sprintf('mysql:host=%s;port=%d;dbname=%s;charset=utf8mb4',
                       $c['db_host'], $c['db_port'], $c['db_name']);
        try {
            $pdo = new PDO($dsn, $c['db_user'], $c['db_pass'], [
                PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
                PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
                PDO::ATTR_EMULATE_PREPARES   => false,
            ]);
        } catch (PDOException $e) {
            error_log('isthisascam: database connection failed: ' . $e->getMessage());
            send_error(503, "The accounts database isn't available. Start MySQL in Laragon, " .
                            'and check that database/schema.sql has been run.');
        }
    }
    return $pdo;
}

// Any unexpected database error: log it, and give the page a plain message.
set_exception_handler(function (Throwable $e): void {
    error_log('isthisascam: ' . get_class($e) . ': ' . $e->getMessage());
    send_error(500, 'Something went wrong on the server. Please try again.');
});

function require_method(string ...$allowed): string
{
    $method = $_SERVER['REQUEST_METHOD'] ?? 'GET';
    if (!in_array($method, $allowed, true)) {
        header('Allow: ' . implode(', ', $allowed));
        send_error(405, 'This address does not accept ' . $method . ' requests.');
    }
    return $method;
}

function read_json(): array
{
    $type = strtolower($_SERVER['CONTENT_TYPE'] ?? '');
    if (strpos($type, 'application/json') !== 0) {
        send_error(415, 'Requests must be sent as JSON.');
    }
    $raw = file_get_contents('php://input', false, null, 0, 65536);
    $data = json_decode($raw === false ? '' : $raw, true);
    if (!is_array($data)) {
        send_error(400, 'The request could not be read.');
    }
    return $data;
}

// A text field from the request: trimmed, and '' when missing or not text.
function text_field(array $data, string $key): string
{
    $value = $data[$key] ?? '';
    return is_string($value) ? trim($value) : '';
}

// --- The login session ----------------------------------------------------------

session_name('isthisascam_session');
session_set_cookie_params([
    'lifetime' => 0,          // until the browser is closed
    'path'     => '/',
    'httponly' => true,
    'samesite' => 'Lax',
    'secure'   => (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off'),
]);
ini_set('session.use_strict_mode', '1');
session_start();

function current_user_id(): ?int
{
    return isset($_SESSION['user_id']) ? (int) $_SESSION['user_id'] : null;
}

function require_login(): int
{
    $id = current_user_id();
    if ($id === null) {
        send_error(401, 'Please log in first.');
    }
    return $id;
}

function log_in(int $userId): void
{
    session_regenerate_id(true);   // a new session id at login stops session fixation
    $_SESSION['user_id'] = $userId;
}

function public_user(array $row): array
{
    $updated = $row['avatar_updated_at'] ?? null;
    return [
        'id'         => (int) $row['id'],
        'email'      => $row['email'],
        'first_name' => $row['first_name'],
        'last_name'  => $row['last_name'],
        'created_at' => $row['created_at'],
        // null = no picture uploaded, so the page shows the default one.
        // Otherwise a number that changes whenever the picture does; the page adds
        // it to the picture's address so the browser never shows an old picture.
        'avatar_version' => $updated ? (int) strtotime($updated) : null,
    ];
}

function find_user(int $id): ?array
{
    try {
        $stmt = db()->prepare('SELECT id, email, first_name, last_name, created_at,
                                      CASE WHEN avatar_image IS NULL THEN NULL ELSE avatar_updated_at END
                                        AS avatar_updated_at
                               FROM users WHERE id = ?');
        $stmt->execute([$id]);
    } catch (PDOException $e) {
        // 42S22 = unknown column: database/add_profile_picture.sql hasn't been run yet.
        // Logging in still works; everyone just gets the default picture.
        if ($e->getCode() !== '42S22') {
            throw $e;
        }
        error_log('isthisascam: profile pictures are off until database/add_profile_picture.sql is run');
        $stmt = db()->prepare('SELECT id, email, first_name, last_name, created_at FROM users WHERE id = ?');
        $stmt->execute([$id]);
    }
    $row = $stmt->fetch();
    return $row ?: null;
}
