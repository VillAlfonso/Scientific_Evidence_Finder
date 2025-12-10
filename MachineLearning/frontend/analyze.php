<?php
// NEW: Database Connection
$pdo = new PDO("mysql:host=localhost;dbname=fact_checker", "root", "");

// 1) Read the claim from the form
$claim = trim($_POST['claim'] ?? $_POST['text'] ?? '');

if ($claim === '') {
    die("No text provided. (Frontend did not send 'claim')");
}

// 2) Call the FastAPI backend
$apiUrl = "http://127.0.0.1:8001/analyze";

$payload = json_encode(["claim" => $claim]);

$ch = curl_init($apiUrl);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_HTTPHEADER, [
    "Content-Type: application/json"
]);
curl_setopt($ch, CURLOPT_POSTFIELDS, $payload);

$response = curl_exec($ch);
$httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

if ($response === false) {
    die("Failed to communicate with backend.");
}

if ($httpCode !== 200) {
    die("Backend returned error ($httpCode):<br><pre>" . htmlspecialchars($response) . "</pre>");
}

$data = json_decode($response, true);


// 3) NEW: Insert claim into DB
$stmt = $pdo->prepare("INSERT INTO claims (claim_text, verdict, truth_score) VALUES (?, ?, ?)");
$stmt->execute([$claim, $data["verdict"] ?? null, $data["truth_score"] ?? 0]);
$claim_id = $pdo->lastInsertId();

// 4) NEW: Insert papers into DB
if (!empty($data["papers"])) {
    $paperInsert = $pdo->prepare("
        INSERT INTO claim_papers (
            claim_id, title, authors, journal, source, published, url, abstract
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ");

    foreach ($data["papers"] as $p) {
        $paperInsert->execute([
            $claim_id,
            $p["title"]      ?? null,
            $p["authors"]    ?? null,
            $p["journal"]    ?? null,
            $p["source"]     ?? null,
            $p["published"]  ?? null,
            $p["url"]        ?? null,
            $p["abstract"]   ?? null
        ]);
    }
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Fact Check Result</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap" rel="stylesheet">
<style>
    body { font-family: 'Inter', sans-serif; background: #f5f7fa; margin: 0; padding: 0; }
    .container {
        max-width: 900px;
        margin: 40px auto;
        background: #fff;
        padding: 30px;
        border-radius: 12px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.08);
    }
    .paper {
        background: #eef2f7;
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 12px;
    }
    .verdict-box {
        padding: 18px;
        background: #eaf1ff;
        border-left: 6px solid #0066ff;
        border-radius: 8px;
        margin-bottom: 20px;
    }
    a { color: #0055ff; text-decoration: none; }
    a:hover { text-decoration: underline; }
    pre {
        white-space: pre-wrap;
        background: #f7f7f7;
        padding: 12px;
        border-radius: 8px;
    }
</style>
</head>
<body>

<div class="container">
    <a href="index.php">← Back</a>

    <h2>Analyzed Claim:</h2>
    <p><strong><?= htmlspecialchars($claim) ?></strong></p>

    <h2>AI Verdict</h2>
    <div class="verdict-box">
        <pre><?= htmlspecialchars($data['verdict'] ?? 'No verdict returned.') ?></pre>
    </div>

    <h2>Scientific Papers</h2>

<?php if (!empty($data['papers'])): ?>
    <?php foreach ($data['papers'] as $p): ?>
        <div class="paper">

            <h3 class="paper-title">
                <?= htmlspecialchars($p['title'] ?? 'Untitled') ?>
            </h3>

            <?php if (!empty($p['authors'])): ?>
                <p>👤 <strong>Authors:</strong> <?= htmlspecialchars($p['authors']) ?></p>
            <?php endif; ?>

            <?php if (!empty($p['journal'])): ?>
                <p>🏛️ <strong>Journal / Publisher:</strong> <?= htmlspecialchars($p['journal']) ?></p>
            <?php endif; ?>

            <?php if (!empty($p['source'])): ?>
                <p>🌐 <strong>Source:</strong> <?= htmlspecialchars($p['source']) ?></p>
            <?php endif; ?>

            <?php if (!empty($p['published'])): ?>
                <p>📅 <strong>Published:</strong> <?= htmlspecialchars($p['published']) ?></p>
            <?php endif; ?>

            <p><?= nl2br(htmlspecialchars($p['abstract'] ?? '')) ?></p>

            <?php if (!empty($p['url'])): ?>
                <a href="<?= htmlspecialchars($p['url']) ?>" target="_blank">🔗 View Full Paper</a>
            <?php endif; ?>

        </div>
    <?php endforeach; ?>
<?php else: ?>
    <p>No papers found.</p>
<?php endif; ?>

</div>
</body>
</html>
