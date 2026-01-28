// API Configuration
const API_BASE_URL = window.location.origin + '/api';

// DOM Elements
const urlInput = document.getElementById('urlInput');
const analyzeBtn = document.getElementById('analyzeBtn');
const loadingState = document.getElementById('loadingState');
const errorState = document.getElementById('errorState');
const errorMessage = document.getElementById('errorMessage');
const retryBtn = document.getElementById('retryBtn');
const resultsSection = document.getElementById('resultsSection');
const newAnalysisBtn = document.getElementById('newAnalysisBtn');

// Current state
let currentUrl = '';

// Event Listeners
analyzeBtn.addEventListener('click', handleAnalyze);
retryBtn.addEventListener('click', handleRetry);
newAnalysisBtn.addEventListener('click', handleNewAnalysis);

urlInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        handleAnalyze();
    }
});

// Main Analysis Handler
async function handleAnalyze() {
    const url = urlInput.value.trim();

    if (!url) {
        showError('Please enter a valid URL');
        return;
    }

    currentUrl = url;
    showLoading();

    try {
        const response = await fetch(`${API_BASE_URL}/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url: url })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Analysis failed');
        }

        const data = await response.json();
        displayResults(data);
    } catch (error) {
        showError(error.message);
    }
}

// Show Loading State
function showLoading() {
    hideAllStates();
    loadingState.classList.remove('hidden');
    analyzeBtn.disabled = true;
}

// Show Error State
function showError(message) {
    hideAllStates();
    errorMessage.textContent = message;
    errorState.classList.remove('hidden');
    analyzeBtn.disabled = false;
}

// Hide All States
function hideAllStates() {
    loadingState.classList.add('hidden');
    errorState.classList.add('hidden');
    resultsSection.classList.add('hidden');
}

// Display Results
function displayResults(data) {
    hideAllStates();
    resultsSection.classList.remove('hidden');
    analyzeBtn.disabled = false;

    // Credibility Score
    const score = data.credibility_score || 0;
    document.getElementById('scoreValue').textContent = Math.round(score);

    const scoreCircle = document.getElementById('scoreCircle');
    scoreCircle.className = 'score-circle';
    if (score >= 70) {
        scoreCircle.classList.add('high');
    } else if (score >= 40) {
        scoreCircle.classList.add('medium');
    } else {
        scoreCircle.classList.add('low');
    }

    // Score Interpretation
    const interpretation = getScoreInterpretation(score);
    document.getElementById('scoreInterpretation').textContent = interpretation;

    // Context Status
    displayAssessment(
        'contextStatus',
        'contextExplanation',
        data.is_out_of_context,
        data.detailed_results?.out_of_context
    );

    // Propaganda Status
    displayAssessment(
        'propagandaStatus',
        'propagandaExplanation',
        data.is_propaganda,
        data.detailed_results?.propaganda
    );

    // Content Context
    document.getElementById('contentContext').textContent =
        data.content_context || 'No content description available.';

    // Key Concerns
    displayList(
        'keyConcernsList',
        data.detailed_results?.key_concerns,
        'No major concerns identified.'
    );

    // Positive Indicators
    displayList(
        'positiveIndicatorsList',
        data.detailed_results?.positive_indicators,
        'No positive indicators identified.'
    );

    // Summary (if available)
    const summarySection = document.getElementById('summarySection');
    const summaryText = document.getElementById('summaryText');
    if (data.detailed_results?.summary) {
        summaryText.textContent = data.detailed_results.summary;
        summarySection.classList.remove('hidden');
    } else {
        summarySection.classList.add('hidden');
    }

    // Metadata
    document.getElementById('analyzedUrl').innerHTML =
        `<strong>URL:</strong> <a href="${data.url}" target="_blank" rel="noopener">${truncateUrl(data.url)}</a>`;
    document.getElementById('analysisDuration').innerHTML =
        `<strong>Duration:</strong> ${(data.analysis_duration || 0).toFixed(1)}s`;
    document.getElementById('requestId').innerHTML =
        `<strong>Request ID:</strong> #${data.request_id}`;
}

// Display Assessment (Yes/No/Uncertain)
function displayAssessment(statusId, explanationId, assessment, details) {
    const statusElement = document.getElementById(statusId);
    const explanationElement = document.getElementById(explanationId);

    const status = assessment || 'Uncertain';
    statusElement.textContent = status;
    statusElement.className = 'status-badge ' + status.toLowerCase();

    if (details && details.explanation) {
        explanationElement.textContent = details.explanation;
    } else {
        explanationElement.textContent = 'No detailed explanation available.';
    }
}

// Display List (concerns or indicators)
function displayList(listId, items, emptyMessage) {
    const listElement = document.getElementById(listId);
    listElement.innerHTML = '';

    if (!items || items.length === 0) {
        const li = document.createElement('li');
        li.textContent = emptyMessage;
        li.style.background = '#f9fafb';
        li.style.color = '#6b7280';
        li.style.borderLeft = 'none';
        listElement.appendChild(li);
        return;
    }

    items.forEach(item => {
        const li = document.createElement('li');
        li.textContent = item;
        listElement.appendChild(li);
    });
}

// Get Score Interpretation
function getScoreInterpretation(score) {
    if (score >= 80) {
        return 'High credibility - Content appears trustworthy and well-sourced';
    } else if (score >= 60) {
        return 'Good credibility - Content is generally reliable with minor concerns';
    } else if (score >= 40) {
        return 'Moderate credibility - Content has notable concerns, verify claims';
    } else if (score >= 20) {
        return 'Low credibility - Content has significant issues, approach with caution';
    } else {
        return 'Very low credibility - Content is highly questionable or unreliable';
    }
}

// Truncate URL for display
function truncateUrl(url, maxLength = 50) {
    if (url.length <= maxLength) return url;
    return url.substring(0, maxLength) + '...';
}

// Handle Retry
function handleRetry() {
    urlInput.value = currentUrl;
    handleAnalyze();
}

// Handle New Analysis
function handleNewAnalysis() {
    urlInput.value = '';
    currentUrl = '';
    hideAllStates();
    urlInput.focus();
}

// Initial focus on input
urlInput.focus();
