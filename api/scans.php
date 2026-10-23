<?php
// api/scans.php -- the logged-in user's checks from Checker.html.
//
// POST  saves one result. js/checker.js sends it after the model server answers.
//   Link:  {"scan_type": "url", "url": "...", "verdict": "phishing", "confidence": 99.1,
//           "phishing_probability": 99.1, "top_reason": "Hyphens in the website name: 3"}
//   Email: {"scan_type": "email", "subject": "...", "body": "...", "verdict": "...",
//           "confidence": 97.3, "phishing_probability": 97.3}
//   Only the subject and the first 200 characters of an email are kept.
//   Answer: {"ok": true, "id": 12}
//
// GET   lists the most recent results (newest first) and a short summary.
//   Answer: {"ok": true, "summary": {"total": 9, "phishing": 4, "legitimate": 5},
//            "scans": [{"id": 12, "scan_type": "url", ...}, ...]}

require __DIR__ . '/_bootstrap.php';
$method = require_method('GET', 'POST');
$userId = require_login();

function clip(string $text, int $max): string
{
    $text = preg_replace('/\s+/u', ' ', $text) ?? '';
    return mb_strlen($text) > $max ? mb_substr($text, 0, $max - 1) . '…' : $text;
}

function percent($value): ?float
{
    if (!is_int($value) && !is_float($value)) {
        return null;
    }
    $value = (float) $value;
    return ($value >= 0 && $value <= 100) ? round($value, 2) : null;
}

if ($method === 'POST') {
    $data = read_json();
    $type = text_field($data, 'scan_type');
    $verdict = text_field($data, 'verdict');
    $confidence = percent($data['confidence'] ?? null);
    $probability = percent($data['phishing_probability'] ?? null);

    if (!in_array($type, ['email', 'url'], true)
        || !in_array($verdict, ['phishing', 'legitimate'], true)
        || $confidence === null || $probability === null) {
        send_error(400, 'This scan result is incomplete, so it was not saved.');
    }

    $url = $subject = $preview = $topReason = null;
    if ($type === 'url') {
        $url = text_field($data, 'url');
        if ($url === '' || mb_strlen($url) > 2048) {
            send_error(400, 'The link is missing or too long to save.');
        }
        $reason = text_field($data, 'top_reason');
        $topReason = $reason === '' ? null : clip($reason, 255);
    } else {
        $subject = clip(text_field($data, 'subject'), 255);
        $preview = clip(text_field($data, 'body'), 200);
        if ($subject === '' && $preview === '') {
            send_error(400, 'The email is empty, so it was not saved.');
        }
    }

    $stmt = db()->prepare(
        'INSERT INTO scan_results
           (user_id, scan_type, url, email_subject, email_preview, verdict,
            confidence, phishing_probability, top_reason)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)'
    );
    $stmt->execute([$userId, $type, $url, $subject ?: null, $preview ?: null, $verdict,
                    $confidence, $probability, $topReason]);
    send_json(201, ['ok' => true, 'id' => (int) db()->lastInsertId()]);
}

// GET
$stmt = db()->prepare(
    'SELECT COUNT(*) AS total,
            COALESCE(SUM(verdict = \'phishing\'), 0)   AS phishing,
            COALESCE(SUM(verdict = \'legitimate\'), 0) AS legitimate
     FROM scan_results WHERE user_id = ?'
);
$stmt->execute([$userId]);
$summary = array_map('intval', $stmt->fetch());

$limit = (int) config()['history_limit'];
$stmt = db()->prepare(
    "SELECT id, scan_type, url, email_subject, email_preview, verdict,
            confidence, phishing_probability, top_reason, created_at
     FROM scan_results WHERE user_id = ?
     ORDER BY created_at DESC, id DESC
     LIMIT $limit"
);
$stmt->execute([$userId]);
$scans = array_map(function (array $row): array {
    $row['id'] = (int) $row['id'];
    $row['confidence'] = (float) $row['confidence'];
    $row['phishing_probability'] = (float) $row['phishing_probability'];
    return $row;
}, $stmt->fetchAll());

send_json(200, ['ok' => true, 'summary' => $summary, 'scans' => $scans]);
