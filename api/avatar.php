<?php
// api/avatar.php -- the logged-in person's profile picture.
//
// GET     the picture itself (an image, not JSON). 404 when none was uploaded;
//         the page then shows the default picture, web/img/default-avatar.jpg.
// POST    upload a new picture: multipart/form-data with one file named "avatar".
//         Answer: {"ok": true, "user": {...}}
// DELETE  remove the picture, so the default one is shown again.
//         Answer: {"ok": true, "user": {...}}
//
// Only the person who is logged in can see or change their own picture.
//
// SAFETY, in plain words
// - Only JPG, PNG and WebP up to 2 MB are taken. The file's real contents are
//   checked, not its name, so "virus.exe" renamed to "me.jpg" is refused.
// - When PHP's GD extension is on (it is in Laragon), the picture is redrawn as a
//   fresh 256 x 256 JPG. That drops anything hidden inside the file, including
//   photo metadata such as the GPS location a phone may have stored.
// - The picture is kept in the database, never in the website folder, so it can
//   never be opened or run as a page on the web server.
// - An upload must carry the X-Requested-With header. Another website can't add
//   that header without the browser asking this server first, which stops a
//   page elsewhere from changing someone's picture (CSRF).

require __DIR__ . '/_bootstrap.php';
$method = require_method('GET', 'POST', 'DELETE');
$userId = require_login();

const AVATAR_MAX_BYTES = 2 * 1024 * 1024;   // 2 MB
const AVATAR_SIZE      = 256;               // pixels, width and height after redrawing
const AVATAR_MAX_SIDE  = 6000;              // refuse absurdly large pictures before decoding them
const AVATAR_TYPES     = ['image/jpeg', 'image/png', 'image/webp'];

function avatar_columns_missing(PDOException $e): void
{
    if ($e->getCode() === '42S22') {
        send_error(503, 'Profile pictures need one database update first: run ' .
                        'database/add_profile_picture.sql in HeidiSQL (see that file).');
    }
    throw $e;
}

// --- GET: send the picture ---------------------------------------------------------

if ($method === 'GET') {
    try {
        $stmt = db()->prepare('SELECT avatar_image, avatar_type FROM users WHERE id = ?');
        $stmt->execute([$userId]);
    } catch (PDOException $e) {
        avatar_columns_missing($e);
    }
    $row = $stmt->fetch();
    if (!$row || $row['avatar_image'] === null || !in_array($row['avatar_type'], AVATAR_TYPES, true)) {
        send_error(404, 'No profile picture uploaded.');
    }
    header('Content-Type: ' . $row['avatar_type']);
    header('Content-Length: ' . strlen($row['avatar_image']));
    // The page asks for avatar.php?v=<when it changed>, so a cached copy is never stale.
    header('Cache-Control: private, max-age=31536000, immutable');
    header("Content-Security-Policy: default-src 'none'");
    echo $row['avatar_image'];
    exit;
}

// POST and DELETE change things: they must come from this site's own pages.
if (($_SERVER['HTTP_X_REQUESTED_WITH'] ?? '') !== 'fetch') {
    send_error(403, 'This request was refused.');
}

// --- DELETE: back to the default picture -------------------------------------------

if ($method === 'DELETE') {
    try {
        db()->prepare('UPDATE users SET avatar_image = NULL, avatar_type = NULL,
                                        avatar_updated_at = NULL WHERE id = ?')
            ->execute([$userId]);
    } catch (PDOException $e) {
        avatar_columns_missing($e);
    }
    send_json(200, ['ok' => true, 'user' => public_user(find_user($userId))]);
}

// --- POST: a new picture -------------------------------------------------------------

$tooBig = 'That picture is too large. Please choose one under 2 MB.';

// A file bigger than PHP's post_max_size arrives as an empty request.
if (empty($_FILES) && (int) ($_SERVER['CONTENT_LENGTH'] ?? 0) > 0) {
    send_error(413, $tooBig);
}

$file = $_FILES['avatar'] ?? null;
if (!is_array($file) || is_array($file['error'] ?? null)) {
    send_error(400, 'Please choose a picture to upload.');
}
switch ($file['error']) {
    case UPLOAD_ERR_OK:
        break;
    case UPLOAD_ERR_INI_SIZE:
    case UPLOAD_ERR_FORM_SIZE:
        send_error(413, $tooBig);
    case UPLOAD_ERR_NO_FILE:
        send_error(400, 'Please choose a picture to upload.');
    default:
        error_log('isthisascam: avatar upload failed with PHP upload error ' . $file['error']);
        send_error(500, 'The picture could not be uploaded. Please try again.');
}

if (!is_uploaded_file($file['tmp_name']) || $file['size'] <= 0) {
    send_error(400, 'Please choose a picture to upload.');
}
if ($file['size'] > AVATAR_MAX_BYTES) {
    send_error(413, $tooBig);
}

// What the file really is, from its contents (not its name or what the browser says).
$finfo = new finfo(FILEINFO_MIME_TYPE);
$type = $finfo->file($file['tmp_name']);
$info = @getimagesize($file['tmp_name']);
if (!in_array($type, AVATAR_TYPES, true) || $info === false || $info['mime'] !== $type) {
    send_error(415, 'Please choose a JPG, PNG or WebP picture.');
}
[$width, $height] = $info;
if ($width < 1 || $height < 1 || $width > AVATAR_MAX_SIDE || $height > AVATAR_MAX_SIDE) {
    send_error(415, 'That picture is too large in size. Please choose a smaller one.');
}

$bytes = file_get_contents($file['tmp_name']);
if ($bytes === false) {
    send_error(500, 'The picture could not be read. Please try again.');
}

// Redraw it as a square 256 x 256 JPG, cropped from the middle (needs PHP's GD).
if (function_exists('imagecreatefromstring')) {
    $source = @imagecreatefromstring($bytes);
    if ($source === false) {
        send_error(415, 'That picture could not be opened. Please try a different one.');
    }
    $side = min($width, $height);
    $square = imagecreatetruecolor(AVATAR_SIZE, AVATAR_SIZE);
    // A see-through PNG gets a white background instead of black.
    imagefill($square, 0, 0, imagecolorallocate($square, 255, 255, 255));
    imagecopyresampled($square, $source, 0, 0,
                       intdiv($width - $side, 2), intdiv($height - $side, 2),
                       AVATAR_SIZE, AVATAR_SIZE, $side, $side);
    ob_start();
    imagejpeg($square, null, 88);
    $bytes = ob_get_clean();
    imagedestroy($source);
    imagedestroy($square);
    $type = 'image/jpeg';
}

try {
    db()->prepare('UPDATE users SET avatar_image = ?, avatar_type = ?, avatar_updated_at = NOW()
                   WHERE id = ?')
        ->execute([$bytes, $type, $userId]);
} catch (PDOException $e) {
    avatar_columns_missing($e);
}

send_json(200, ['ok' => true, 'user' => public_user(find_user($userId))]);
