<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>AI Scientific Claim Checker</title>

<!-- Bootstrap -->
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">

<style>
    body {
        background: #f4f6fb;
        font-family: 'Inter', sans-serif;
    }
    .card {
        border-radius: 16px;
        border: none;
        box-shadow: 0 6px 20px rgba(0,0,0,0.08);
    }
    .btn-analyze {
        background: #0066ff;
        border-radius: 10px;
        font-size: 17px;
        padding: 12px 16px;
    }
    .btn-analyze:hover {
        background: #0050d4;
    }
    #loadingSpinner {
        display: none;
        margin-top: 20px;
        text-align: center;
    }

    /* NEW BUTTON STYLE (small and clean) */
    .btn-history {
        font-size: 14px;
        padding: 6px 12px;
        border-radius: 8px;
    }

</style>

</head>
<body>

<div class="container mt-5">
    <div class="row justify-content-center">
        <div class="col-lg-7">

            <div class="d-flex justify-content-end mb-2">
                <a href="history.php" class="btn btn-secondary btn-history">
                    📜 History
                </a>
            </div>

            <div class="card p-4">
                <h2 class="text-center mb-3">🔬 AI Scientific Claim Checker</h2>
                <p class="text-muted text-center mb-4">
                    Input a statement and the AI will analyze scientific research to evaluate its validity.
                </p>

                <form id="analyzeForm" action="analyze.php" method="POST">
                    <textarea 
                        name="claim"
                        class="form-control"
                        rows="6"
                        placeholder="Example: Creatine damages the kidneys."
                        required></textarea>

                    <button type="submit" class="btn btn-primary w-100 btn-analyze mt-3">
                        Analyze Claim
                    </button>
                </form>

                <!-- Loading spinner -->
                <div id="loadingSpinner">
                    <div class="spinner-border text-primary" role="status"></div>
                    <p class="mt-2 text-primary">Analyzing claim, please wait...</p>
                </div>

            </div>

        </div>
    </div>
</div>

<!-- Bootstrap JS -->
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>

<script>
    document.getElementById("analyzeForm").addEventListener("submit", function() {
        document.getElementById("loadingSpinner").style.display = "block";
    });
</script>

</body>
</html>
