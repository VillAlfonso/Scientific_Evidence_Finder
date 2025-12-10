<?php
$pdo = new PDO("mysql:host=localhost;dbname=fact_checker", "root", "");

$id = $_GET["id"];

// Delete claim → papers delete automatically because of ON DELETE CASCADE
$stmt = $pdo->prepare("DELETE FROM claims WHERE id = ?");
$stmt->execute([$id]);

header("Location: history.php");
exit;
