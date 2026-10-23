<?php
// Is this a scam? -- settings for the accounts API (api/*.php).
//
// The values below are Laragon's defaults: MySQL on this computer, user "root",
// no password. Change them here if your MySQL is set up differently.
//
// Create the database first by running database/schema.sql (see that file).

return [
    // --- MySQL ------------------------------------------------------------------
    'db_host' => '127.0.0.1',
    'db_port' => 3306,
    'db_name' => 'isthisascam',
    'db_user' => 'root',
    'db_pass' => '',

    // --- Sign-up rules ----------------------------------------------------------
    'password_min_length' => 8,
    'name_max_length'     => 50,

    // --- "Scam or Safe?" (Game.html) --------------------------------------------
    // A game counts as passed when at least this many answers out of 10 are right.
    // 8 is where the game's own "Sharp Eyes" rank starts.
    'game_pass_mark' => 8,

    // --- My records (Account.html) ----------------------------------------------
    // How many recent scans and games the page lists.
    'history_limit' => 50,
];
