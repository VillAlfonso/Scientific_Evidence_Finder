<?php
$pdo = new PDO("mysql:host=localhost;dbname=fact_checker", "root", "");

// If ?id= is present → show single record
$viewId = $_GET['id'] ?? null;

if ($viewId) {

    // Fetch claim
    $stmt = $pdo->prepare("SELECT * FROM claims WHERE id = ?");
    $stmt->execute([$viewId]);
    $claim = $stmt->fetch(PDO::FETCH_ASSOC);

    // Fetch papers
    $stmt = $pdo->prepare("SELECT * FROM claim_papers WHERE claim_id = ?");
    $stmt->execute([$viewId]);
    $papers = $stmt->fetchAll(PDO::FETCH_ASSOC);

?>
<!DOCTYPE html>
<html>
<head>
<title>View Claim</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">

<style>
.card {
    border-radius: 14px;
    box-shadow: 0 6px 20px rgba(0,0,0,0.08);
}
.paper-box {
    background: #eef2f7;
    border-radius: 10px;
    padding: 14px;
    margin-bottom: 14px;
}
.truth-bar-bg {
    width: 100%;
    height: 14px;
    background: #ddd;
    border-radius: 8px;
    overflow: hidden;
    margin-bottom: 10px;
}
</style>

</head>
<body class="p-4">

<a href="history.php" class="btn btn-secondary mb-3">← Back to History</a>
<a href="index.php" class="btn btn-outline-primary mb-3">🏠 Home</a>

<div class="card p-4">
    <h3>Claim #<?= $claim['id'] ?></h3>
    <p><strong>Claim:</strong></p>
    <p><?= nl2br(htmlspecialchars($claim['claim_text'])) ?></p>

    <hr>

    <h4>AI Verdict</h4>
    <p><?= nl2br(htmlspecialchars($claim['verdict'])) ?></p>

    <?php if (!empty($claim['truth_score'])): ?>
        <p><strong>Truth Score:</strong> <?= $claim['truth_score'] ?> / 100</p>

        <div class="truth-bar-bg">
            <div style="
                width: <?= intval($claim['truth_score']) ?>%;
                height: 100%;
                background:
                    <?= $claim['truth_score'] >= 70 ? '#4caf50' : ($claim['truth_score'] >= 40 ? '#ffc107' : '#f44336') ?>;
            "></div>
        </div>
    <?php endif; ?>

    <hr>

    <h4>Scientific Papers Retrieved (<?= count($papers) ?>)</h4>

    <?php if (count($papers) === 0): ?>
        <p>No papers linked to this claim.</p>
    <?php else: ?>
        <?php foreach ($papers as $p): ?>
            <div class="paper-box">

                <h5><?= htmlspecialchars($p['title'] ?? 'Untitled') ?></h5>

                <?php if ($p['authors']): ?>
                    <p><strong>Authors:</strong> <?= htmlspecialchars($p['authors']) ?></p>
                <?php endif; ?>

                <?php if ($p['journal']): ?>
                    <p><strong>Journal:</strong> <?= htmlspecialchars($p['journal']) ?></p>
                <?php endif; ?>

                <?php if ($p['source']): ?>
                    <p><strong>Source:</strong> <?= htmlspecialchars($p['source']) ?></p>
                <?php endif; ?>

                <?php if ($p['published']): ?>
                    <p><strong>Published:</strong> <?= htmlspecialchars($p['published']) ?></p>
                <?php endif; ?>

                <p><?= nl2br(htmlspecialchars($p['abstract'])) ?></p>

                <?php if ($p['url']): ?>
                    <a href="<?= htmlspecialchars($p['url']) ?>" target="_blank" class="btn btn-sm btn-primary">View Full Paper</a>
                <?php endif; ?>

            </div>
        <?php endforeach; ?>
    <?php endif; ?>
</div>

</body>
</html>

<?php
    exit; // STOP HERE — prevents history table from loading
}

//
// OTHERWISE SHOW HISTORY TABLE
//

// Fetch all claims with paper count
$sql = "
    SELECT c.*, 
    (SELECT COUNT(*) FROM claim_papers WHERE claim_id = c.id) AS paper_count
    FROM claims c ORDER BY created_at DESC
";
$stmt = $pdo->query($sql);
$claims = $stmt->fetchAll(PDO::FETCH_ASSOC);

?>

<!DOCTYPE html>
<html>
<head>
<title>History</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">

<style>
.table-container {
    background: white;
    padding: 20px;
    border-radius: 14px;
    box-shadow: 0 6px 20px rgba(0,0,0,0.08);
}
</style>

</head>
<body class="p-4">

<div class="d-flex justify-content-between mb-3">
    <h2>📜 Analysis History</h2>
    <a href="index.php" class="btn btn-primary">🏠 Back to Home</a>
</div>

<div class="table-container">

<table class="table table-striped mt-3">
    <thead>
        <tr>
            <th>ID</th>
            <th>Claim</th>
            <th>Verdict</th>
            <th>Papers</th>
            <th>Date</th>
            <th>Actions</th>
        </tr>
    </thead>

    <tbody>
    <?php foreach ($claims as $c): ?>
    <tr>
        <td><?= $c["id"] ?></td>

        <td><?= htmlspecialchars(substr($c["claim_text"], 0, 60)) ?>...</td>

        <td><?= htmlspecialchars(substr($c["verdict"], 0, 60)) ?>...</td>

        <td>
            <?php if (!empty($c["truth_score"])): ?>
                <?= $c["truth_score"] ?>%
            <?php else: ?>
                -
            <?php endif; ?>
        </td>

        <td><?= $c["paper_count"] ?></td>

        <td><?= $c["created_at"] ?></td>

        <td>
            <a class="btn btn-sm btn-primary" href="history.php?id=<?= $c["id"] ?>">View</a>
            <a class="btn btn-sm btn-danger" href="delete.php?id=<?= $c["id"] ?>" 
               onclick="return confirm('Delete this entry?')">Delete</a>
        </td>
    </tr>
    <?php endforeach; ?>
    </tbody>

</table>

</div>

</body>
</html>
