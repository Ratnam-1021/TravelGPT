let currentStyle = 'Balanced';
let currentItineraryData = null;

// Set Destination from Chip
function setDestination(name) {
    document.getElementById('destination').value = name;
    document.querySelectorAll('#quickDestinations .chip').forEach(chip => {
        chip.classList.toggle('active', chip.innerText.includes(name));
    });
}

// Set Travel Style
function setTravelStyle(style, btn) {
    currentStyle = style;
    document.querySelectorAll('.style-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
}

// Toggle Interest Chip
function toggleInterest(chip) {
    chip.classList.toggle('active');
}

// Tab Switcher
function switchTab(tabId, btn) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    document.querySelectorAll('.tab-content').forEach(c => c.classList.add('hidden'));
    document.getElementById(tabId).classList.remove('hidden');
}

// Main Itinerary Generation
async function generateItinerary() {
    const dest = document.getElementById('destination').value.trim();
    const duration = parseInt(document.getElementById('duration').value, 10);
    const travelers = parseInt(document.getElementById('travelers').value, 10);
    const budget = parseFloat(document.getElementById('budget').value);
    const currency = document.getElementById('currency').value;

    const selectedInterests = Array.from(document.querySelectorAll('#interestContainer .chip-toggle.active'))
        .map(chip => chip.innerText.replace(/^[^\s]+\s*/, ''));

    if (!dest) {
        alert("Please enter a valid destination.");
        return;
    }

    // Toggle UI States
    document.getElementById('emptyState').classList.add('hidden');
    document.getElementById('itineraryOutput').classList.add('hidden');
    document.getElementById('loadingState').classList.remove('hidden');

    const requestPayload = {
        destination: dest,
        duration_days: duration,
        travelers_count: travelers,
        budget: budget,
        currency: currency,
        travel_style: currentStyle,
        interests: selectedInterests
    };

    try {
        const response = await fetch('/api/plan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestPayload)
        });

        if (!response.ok) {
            throw new Error(`Server returned status ${response.status}`);
        }

        const data = await response.json();
        currentItineraryData = data;
        renderItinerary(data);

        document.getElementById('loadingState').classList.add('hidden');
        document.getElementById('itineraryOutput').classList.remove('hidden');
    } catch (err) {
        console.error("Itinerary Generation Error:", err);
        alert("Error generating itinerary. Please make sure the backend server is running.");
        document.getElementById('loadingState').classList.add('hidden');
        document.getElementById('emptyState').classList.remove('hidden');
    }
}

// Render Generated Itinerary
function renderItinerary(data) {
    // 1. Header & Summary
    document.getElementById('outTitle').innerText = data.trip_title || `${data.duration_days}-Day Trip to ${data.destination}`;
    document.getElementById('outSummary').innerText = data.summary || "";

    // 2. Render Schedule Days
    const container = document.getElementById('daysContainer');
    container.innerHTML = "";

    data.days.forEach(day => {
        const dayCard = document.createElement('div');
        dayCard.className = 'day-card';

        let activitiesHtml = "";
        day.activities.forEach(act => {
            activitiesHtml += `
                <div class="activity-row">
                    <div><span class="slot-badge">${act.time_slot}</span></div>
                    <div>
                        <strong>${escapeHtml(act.title)}</strong>
                        <div class="act-desc">${escapeHtml(act.description)}</div>
                    </div>
                    <div><i class="fa-solid fa-map-pin"></i> ${escapeHtml(act.location)}</div>
                    <div><strong>${data.currency} ${act.estimated_cost}</strong></div>
                </div>
            `;
        });

        let tipsHtml = "";
        if (day.insider_tips && day.insider_tips.length > 0) {
            tipsHtml = `
                <div class="tips-box">
                    <i class="fa-solid fa-lightbulb"></i> <strong>Tips:</strong> ${day.insider_tips.map(t => escapeHtml(t)).join(' • ')}
                </div>
            `;
        }

        dayCard.innerHTML = `
            <div class="day-header" onclick="this.nextElementSibling.classList.toggle('hidden')">
                <h4>Day ${day.day}: ${escapeHtml(day.theme)}</h4>
                <span><strong>Est. Day Cost:</strong> ${data.currency} ${day.daily_estimated_cost} <i class="fa-solid fa-chevron-down"></i></span>
            </div>
            <div class="day-body">
                ${activitiesHtml}
                ${tipsHtml}
            </div>
        `;
        container.appendChild(dayCard);
    });

    // 3. Render Cost Breakdown Tab
    const cost = data.cost_estimate;
    document.getElementById('costTarget').innerText = `${cost.currency} ${cost.target_budget.toLocaleString()}`;
    document.getElementById('costTotal').innerText = `${cost.currency} ${cost.total_estimated_cost.toLocaleString()}`;

    const statusBadge = document.getElementById('costStatus');
    statusBadge.innerText = cost.budget_status;
    if (cost.budget_status === "Over Budget") {
        statusBadge.style.backgroundColor = "rgba(239, 68, 68, 0.2)";
        statusBadge.style.color = "var(--danger)";
    } else {
        statusBadge.style.backgroundColor = "rgba(16, 185, 129, 0.2)";
        statusBadge.style.color = "var(--success)";
    }

    const pct = Math.min(100, Math.round((cost.total_estimated_cost / cost.target_budget) * 100));
    document.getElementById('meterFill').style.width = `${pct}%`;
    document.getElementById('budgetMeterText').innerText = `${pct}% of target budget used`;

    const expenseGrid = document.getElementById('expenseGrid');
    expenseGrid.innerHTML = "";
    cost.breakdown.forEach(item => {
        const card = document.createElement('div');
        card.className = 'expense-card';
        card.innerHTML = `
            <div class="expense-card-top">
                <span>${escapeHtml(item.category)}</span>
                <span>${cost.currency} ${item.amount.toLocaleString()}</span>
            </div>
            <div style="font-size:12px; color:var(--text-muted);">${item.percentage}% • ${escapeHtml(item.notes)}</div>
        `;
        expenseGrid.appendChild(card);
    });

    // 4. Render RAG Context Tab
    const ragList = document.getElementById('ragList');
    ragList.innerHTML = "";
    if (data.retrieved_policies_and_guides && data.retrieved_policies_and_guides.length > 0) {
        data.retrieved_policies_and_guides.forEach(rag => {
            const rCard = document.createElement('div');
            rCard.className = 'rag-card';
            rCard.innerHTML = `
                <div class="rag-source"><i class="fa-solid fa-file-lines"></i> ${escapeHtml(rag.source)} (Relevance Score: ${rag.relevance_score})</div>
                <div class="rag-snippet">${escapeHtml(rag.content)}</div>
            `;
            ragList.appendChild(rCard);
        });
    } else {
        ragList.innerHTML = `<p style="color:var(--text-muted); font-size:13px;">No explicit guide chunks retrieved for this query.</p>`;
    }
}

// Export PDF Handler
async function exportPDF() {
    if (!currentItineraryData) {
        alert("No active itinerary to export!");
        return;
    }

    try {
        const response = await fetch('/api/export-pdf', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ itinerary: currentItineraryData })
        });

        if (!response.ok) {
            throw new Error("Failed to generate PDF");
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `Itinerary_${currentItineraryData.destination.replace(/\s+/g, '_')}.pdf`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
    } catch (err) {
        console.error("PDF Export Error:", err);
        alert("Could not export PDF. Please check backend connection.");
    }
}

// Utility: Escape HTML
function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/[&<>"']/g, function(m) {
        return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' }[m];
    });
}
