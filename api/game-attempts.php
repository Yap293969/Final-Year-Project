<?php
// api/game-attempts.php -- the logged-in user's rounds of "Scam or Safe?" (Game.html).
//
// POST  saves one finished game. js/game.js sends it on the results screen.
//   Sent: {"score": 850, "correct_count": 9, "total_rounds": 10, "scams_caught": 6,
//          "scams_total": 6, "safe_trusted": 3, "safe_total": 4, "best_streak": 7,
//          "hints_used": 1}
//   Whether it was passed is decided here, not by the page: at least the pass mark
//   (config.php, out of 10) right.
//   Answer: {"ok": true, "id": 3, "passed": true, "stats": {...}}
//
// GET   the summary and the most recent games (newest first).
//   Answer: {"ok": true, "stats": {"attempts": 5, "passed": 2, "best_score": 900,
//            "pass_mark": 8, "first_pass_attempt": 3}, "attempts": [...]}

require __DIR__ . '/_bootstrap.php';
$method = require_method('GET', 'POST');
$userId = require_login();

function pass_mark_for(int $totalRounds): int
{
    // The pass mark is set out of 10 rounds; scale it if a game had fewer.
    return (int) ceil(config()['game_pass_mark'] * $totalRounds / 10);
}

function game_stats(int $userId): array
{
    $stmt = db()->prepare(
        'SELECT COUNT(*) AS attempts,
                COALESCE(SUM(passed), 0) AS passed,
                COALESCE(MAX(score), 0) AS best_score
         FROM game_attempts WHERE user_id = ?'
    );
    $stmt->execute([$userId]);
    $stats = array_map('intval', $stmt->fetch());

    // Which attempt was the first one passed (1 = the very first game), or null.
    $stmt = db()->prepare(
        'SELECT COUNT(*) FROM game_attempts
         WHERE user_id = ? AND id <= (SELECT MIN(id) FROM game_attempts WHERE user_id = ? AND passed = 1)'
    );
    $stmt->execute([$userId, $userId]);
    $first = (int) $stmt->fetchColumn();

    $stats['first_pass_attempt'] = $first > 0 ? $first : null;
    $stats['pass_mark'] = (int) config()['game_pass_mark'];
    return $stats;
}

if ($method === 'POST') {
    $data = read_json();

    // Every field must be a whole number in a sensible range.
    $limits = [
        'total_rounds'  => [1, 20],
        'correct_count' => [0, 20],
        'score'         => [0, 2000],
        'scams_caught'  => [0, 20],
        'scams_total'   => [0, 20],
        'safe_trusted'  => [0, 20],
        'safe_total'    => [0, 20],
        'best_streak'   => [0, 20],
        'hints_used'    => [0, 20],
    ];
    $v = [];
    foreach ($limits as $key => [$min, $max]) {
        $value = $data[$key] ?? null;
        if (!is_int($value) || $value < $min || $value > $max) {
            send_error(400, 'This game result is incomplete, so it was not saved.');
        }
        $v[$key] = $value;
    }
    $n = $v['total_rounds'];
    $consistent = $v['correct_count'] <= $n
        && $v['scams_total'] + $v['safe_total'] === $n
        && $v['scams_caught'] <= $v['scams_total']
        && $v['safe_trusted'] <= $v['safe_total']
        && $v['scams_caught'] + $v['safe_trusted'] === $v['correct_count']
        && $v['best_streak'] <= $v['correct_count']
        && $v['hints_used'] <= $n
        && $v['score'] <= 100 * $v['correct_count'];
    if (!$consistent) {
        send_error(400, "This game result doesn't add up, so it was not saved.");
    }

    $passed = $v['correct_count'] >= pass_mark_for($n);

    $stmt = db()->prepare(
        'INSERT INTO game_attempts
           (user_id, score, correct_count, total_rounds, scams_caught, scams_total,
            safe_trusted, safe_total, best_streak, hints_used, passed)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
    );
    $stmt->execute([$userId, $v['score'], $v['correct_count'], $n, $v['scams_caught'],
                    $v['scams_total'], $v['safe_trusted'], $v['safe_total'],
                    $v['best_streak'], $v['hints_used'], $passed ? 1 : 0]);

    send_json(201, ['ok' => true, 'id' => (int) db()->lastInsertId(),
                    'passed' => $passed, 'stats' => game_stats($userId)]);
}

// GET
$limit = (int) config()['history_limit'];
$stmt = db()->prepare(
    "SELECT id, score, correct_count, total_rounds, scams_caught, scams_total,
            safe_trusted, safe_total, best_streak, hints_used, passed, created_at
     FROM game_attempts WHERE user_id = ?
     ORDER BY created_at DESC, id DESC
     LIMIT $limit"
);
$stmt->execute([$userId]);
$attempts = array_map(function (array $row): array {
    foreach ($row as $key => $value) {
        if ($key !== 'created_at') {
            $row[$key] = (int) $value;
        }
    }
    $row['passed'] = (bool) $row['passed'];
    return $row;
}, $stmt->fetchAll());

send_json(200, ['ok' => true, 'stats' => game_stats($userId), 'attempts' => $attempts]);
