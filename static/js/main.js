document.addEventListener('DOMContentLoaded', () => {

    // Initialize Fetch Handlers
    handleUrlFetch('url1', 'fetch1', 'text1');
    handleUrlFetch('url2', 'fetch2', 'text2');

    // Attach Event to Analyze Button
    const analyzeBtn = document.getElementById('analyzeBtn');
    if (analyzeBtn) {
        analyzeBtn.addEventListener('click', checkPlagiarism);
    }

    // API Key Management (Session Storage)
    const apiKeyInput = document.getElementById('api_key');
    if (apiKeyInput) {
        // Load from session storage if exists
        const storedKey = sessionStorage.getItem('mineruApiKey');
        if (storedKey) {
            apiKeyInput.value = storedKey;
        }

        // Save to session storage when user types/pastes
        apiKeyInput.addEventListener('input', (e) => {
            sessionStorage.setItem('mineruApiKey', e.target.value.trim());
        });
    }
});

async function checkPlagiarism() {
    const t1 = document.getElementById('text1').value;
    const t2 = document.getElementById('text2').value;
    const resultBox = document.getElementById('result');

    if (!t1 || !t2) {
        alert("Please provide content for both documents.");
        return;
    }

    // Reset UI state for loading
    resultBox.className = 'result-card show';
    resultBox.innerHTML = `
        <div class="score-label">Running analysis...</div>
        <div style="font-size: 2rem; color: var(--text-muted); margin-top: 1rem;">⚙️</div>
    `;

    const formData = new FormData();
    formData.append('text1', t1);
    formData.append('text2', t2);

    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.similarity !== undefined) {
            const score = data.similarity.toFixed(2);
            let themeClass = 'theme-success';
            let message = 'Low Similarity';

            if (score > 50) {
                themeClass = 'theme-danger';
                message = 'High Similarity';
            } else if (score > 20) {
                themeClass = 'theme-warning';
                message = 'Moderate Similarity';
            }

            resultBox.className = `result-card show ${themeClass}`;
            resultBox.innerHTML = `
                <div class="score-label">${message}</div>
                <div class="score-display">${score}%</div>
                <div style="font-size: 0.9rem; margin-top: 0.5rem; opacity: 0.8;">Semantic Similarity (TF-IDF)</div>
            `;

        } else {
            showError(resultBox, data.message || "Unknown error");
        }

    } catch (error) {
        console.error('Error:', error);
        showError(resultBox, "Connection Error");
    }
}

function showError(el, msg) {
    el.className = 'result-card show theme-danger';
    el.innerHTML = `
        <div class="score-label">Error</div>
        <div style="font-size: 1.1rem; margin-top: 0.5rem;">${msg}</div>
    `;
}

function handleUrlFetch(urlInputId, fetchBtnId, textAreaId) {
    const urlInput = document.getElementById(urlInputId);
    const fetchBtn = document.getElementById(fetchBtnId);
    const textArea = document.getElementById(textAreaId);

    if (!urlInput || !fetchBtn || !textArea) return;

    fetchBtn.addEventListener('click', async function () {
        const url = urlInput.value.trim();
        const apiKeyInput = document.getElementById('api_key');
        const apiKey = apiKeyInput ? apiKeyInput.value.trim() : sessionStorage.getItem('mineruApiKey');

        if (!apiKey) {
            alert("Please enter your MinerU API Key first.");
            return;
        }

        if (!url) {
            alert("Please enter a URL");
            return;
        }

        // Save original states
        const originalPlaceholder = textArea.placeholder;
        const originalBtnText = fetchBtn.innerHTML;

        // Loading state
        textArea.placeholder = "Extracting text relative to document length... (this might take a moment)";
        textArea.value = "";
        fetchBtn.innerHTML = "⏳ Fetching...";
        fetchBtn.disabled = true;

        const formData = new FormData();
        formData.append('url', url);
        formData.append('api_key', apiKey);

        try {
            const response = await fetch('/extract_text', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.text) {
                textArea.value = data.text;
            } else {
                textArea.value = "Error extracting text: " + (data.error || "Unknown error");
            }
        } catch (error) {
            console.error('Error:', error);
            textArea.value = "Error extracting text due to connection failure.";
        } finally {
            // Restore states
            textArea.placeholder = originalPlaceholder;
            fetchBtn.innerHTML = originalBtnText;
            fetchBtn.disabled = false;
        }
    });
}
