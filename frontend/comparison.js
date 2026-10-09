
/* =========================================================
   CLAUSEGUARD AI
   EVIDENCE-GROUNDED CHANGE INTELLIGENCE
========================================================= */

"use strict";

const API_BASE = "http://127.0.0.1:8001";

let contracts = [];
let selectedV1 = null;
let selectedV2 = null;
let comparisonData = null;
let requestSequence = 0;

/* =========================================================
   INITIALIZATION
========================================================= */

document.addEventListener("DOMContentLoaded", () => {
    bindEvents();
    loadContracts();
});

function bindEvents() {
    document.getElementById("v1Selector")
        ?.addEventListener("change", handleV1Change);

    document.getElementById("v2Selector")
        ?.addEventListener("change", handleV2Change);

    document.getElementById("refreshComparison")
        ?.addEventListener("click", loadContracts);
}

/* =========================================================
   LOAD CONTRACTS
========================================================= */

async function loadContracts() {
    const requestId = ++requestSequence;

    setSystemStatus("loading", "Loading contracts...");
    clearComparisonUI();
    showLoading("Loading available contracts...");

    try {
        const response = await fetch(`${API_BASE}/contracts`);
        const payload = await parseResponse(response);

        if (!response.ok) {
            throw new Error(getErrorMessage(payload, response.status));
        }

        contracts = normalizeContracts(payload);

        if (contracts.length === 0) {
            selectedV1 = null;
            selectedV2 = null;

            populateSelectors();

            showSelectionPrompt(
                "No contracts found. Upload a contract before comparing."
            );

            setSystemStatus("online", "No contracts available");
            return;
        }

        populateSelectors();
        restoreSelections();

        if (requestId !== requestSequence) return;

        if (selectedV1 && selectedV2) {
            await runComparison();
        } else {
            showSelectionPrompt(
                "Select two contracts or versions to compare."
            );

            setSystemStatus("online", "Backend connected");
        }
    } catch (error) {
        if (requestId !== requestSequence) return;

        console.error("Contract loading failed:", error);

        showComparisonError(error.message);
        setSystemStatus("error", "Backend unavailable");
    }
}

function normalizeContracts(payload) {
    let items = [];

    if (Array.isArray(payload)) {
        items = payload;
    } else if (Array.isArray(payload?.contracts)) {
        items = payload.contracts;
    } else if (Array.isArray(payload?.items)) {
        items = payload.items;
    } else if (Array.isArray(payload?.data)) {
        items = payload.data;
    }

    return items
        .map(contract => ({
            id: Number(contract.id),

            name:
                contract.contract_name ||
                contract.name ||
                contract.file_name ||
                contract.filename ||
                `Contract ${contract.id}`,

            file_name:
                contract.file_name ||
                contract.filename ||
                "",

            version: Number(
                contract.version_number ??
                contract.version ??
                1
            ),

            parent_contract_id:
                contract.parent_contract_id === null ||
                contract.parent_contract_id === undefined ||
                contract.parent_contract_id === ""
                    ? null
                    : Number(contract.parent_contract_id),

            uploaded_at: contract.uploaded_at || null
        }))
        .filter(contract => Number.isFinite(contract.id))
        .sort((a, b) => {
            const nameComparison = a.name.localeCompare(b.name);

            return nameComparison !== 0
                ? nameComparison
                : a.id - b.id;
        });
}

/* =========================================================
   SELECTORS
========================================================= */

function populateSelectors() {
    const v1Selector = document.getElementById("v1Selector");
    const v2Selector = document.getElementById("v2Selector");

    if (!v1Selector || !v2Selector) return;

    populateSelector(v1Selector, "Select first contract");
    populateSelector(v2Selector, "Select second contract");

    updateSelectors();
}

function populateSelector(selector, placeholder) {
    selector.replaceChildren();

    const firstOption = document.createElement("option");
    firstOption.value = "";
    firstOption.textContent = placeholder;

    selector.appendChild(firstOption);

    contracts.forEach(contract => {
        const option = document.createElement("option");

        option.value = String(contract.id);
        option.textContent = buildContractLabel(contract);

        selector.appendChild(option);
    });
}

function buildContractLabel(contract) {
    const name = contract.name || `Contract ${contract.id}`;

    // Only contracts explicitly linked to a parent are displayed
    // as generated child versions.
    if (contract.parent_contract_id !== null) {
        return `${name} — V${contract.version}`;
    }

    // Independent uploads are not automatically labelled as V1.
    return name;
}

function restoreSelections() {
    const savedV1 = readSavedId("comparisonV1Id");
    const savedV2 = readSavedId("comparisonV2Id");

    selectedV1 =
        contracts.find(contract => contract.id === savedV1) || null;

    selectedV2 =
        contracts.find(contract => contract.id === savedV2) || null;

    if (
        selectedV1 &&
        selectedV2 &&
        selectedV1.id === selectedV2.id
    ) {
        selectedV2 = null;
    }

    updateSelectors();
}

function readSavedId(key) {
    try {
        const value = localStorage.getItem(key);

        if (!value) return null;

        const id = Number(value);

        return Number.isFinite(id) ? id : null;
    } catch {
        return null;
    }
}

function saveSelection(key, contract) {
    try {
        if (contract) {
            localStorage.setItem(key, String(contract.id));
        } else {
            localStorage.removeItem(key);
        }
    } catch (error) {
        console.warn("Could not save comparison selection:", error);
    }
}

function updateSelectors() {
    const v1Selector = document.getElementById("v1Selector");
    const v2Selector = document.getElementById("v2Selector");

    if (v1Selector) {
        v1Selector.value = selectedV1
            ? String(selectedV1.id)
            : "";
    }

    if (v2Selector) {
        v2Selector.value = selectedV2
            ? String(selectedV2.id)
            : "";
    }
}

async function handleV1Change(event) {
    const id = Number(event.target.value);

    selectedV1 = id
        ? contracts.find(contract => contract.id === id) || null
        : null;

    saveSelection("comparisonV1Id", selectedV1);

    await runComparison();
}

async function handleV2Change(event) {
    const id = Number(event.target.value);

    selectedV2 = id
        ? contracts.find(contract => contract.id === id) || null
        : null;

    saveSelection("comparisonV2Id", selectedV2);

    await runComparison();
}

/* =========================================================
   RUN COMPARISON
========================================================= */

async function runComparison() {
    const requestId = ++requestSequence;

    clearComparisonUI();

    if (!selectedV1 || !selectedV2) {
        showSelectionPrompt(
            "Select two contracts or versions to compare."
        );

        setSystemStatus("online", "Select contracts to continue");
        return;
    }

    if (selectedV1.id === selectedV2.id) {
        showSelectionPrompt(
            "Select two different contracts to compare."
        );

        setSystemStatus("online", "Choose different contracts");
        return;
    }

    updateSelectorMessage(
        `Comparing ${buildContractLabel(selectedV1)} → ` +
        `${buildContractLabel(selectedV2)}`
    );

    showLoading("Analyzing risk differences...");
    setSystemStatus("loading", "Analyzing contract changes...");

    try {
        const url =
            `${API_BASE}/contracts/${encodeURIComponent(selectedV1.id)}` +
            `/risk-comparison?v2_contract_id=` +
            encodeURIComponent(selectedV2.id);

        const response = await fetch(url);
        const payload = await parseResponse(response);

        if (requestId !== requestSequence) return;

        if (!response.ok) {
            throw new Error(getErrorMessage(payload, response.status));
        }

        if (
            !payload ||
            !payload.risk_summary ||
            !Array.isArray(payload.risk_changes)
        ) {
            throw new Error(
                "The backend returned an unexpected comparison response."
            );
        }

        comparisonData = payload;

        renderComparison(comparisonData);

        saveSelection("comparisonV1Id", selectedV1);
        saveSelection("comparisonV2Id", selectedV2);

        setSystemStatus("online", "Backend connected");

        updateSelectorMessage(
            `Compared ${buildContractLabel(selectedV1)} → ` +
            `${buildContractLabel(selectedV2)}`
        );
    } catch (error) {
        if (requestId !== requestSequence) return;

        console.error("Comparison failed:", error);

        showComparisonError(error.message);
        setSystemStatus("error", "Comparison unavailable");
    }
}

/* =========================================================
   RESPONSE HELPERS
========================================================= */

async function parseResponse(response) {
    try {
        return await response.json();
    } catch {
        return {};
    }
}

function getErrorMessage(payload, status) {
    const detail = payload?.detail;

    if (Array.isArray(detail)) {
        return detail
            .map(item => item.msg || JSON.stringify(item))
            .join("; ");
    }

    if (typeof detail === "string" && detail.trim()) {
        return detail;
    }

    return `Request failed with HTTP ${status}.`;
}

/* =========================================================
   RESET AND ERROR STATES
========================================================= */

function clearComparisonUI() {
    comparisonData = null;

    [
        "changesDetected",
        "riskIncreased",
        "riskReduced",
        "unchangedCount",
        "netRiskImpact"
    ].forEach(id => setText(id, "—"));

    setText("comparisonResultCount", "0");

    setText(
        "overallResultTitle",
        "Waiting for comparison"
    );

    setText(
        "overallResultDescription",
        "Select two contracts to inspect their risk impact."
    );

    const results = document.getElementById("comparisonResults");
    const unchanged = document.getElementById("unchangedClauses");
    const regression = document.getElementById("regressionSection");
    const overall = document.getElementById("overallResult");

    if (results) results.replaceChildren();
    if (unchanged) unchanged.replaceChildren();

    regression?.classList.add("hidden");

    overall?.classList.remove(
        "result-improved",
        "result-regression",
        "result-neutral"
    );
}

function showLoading(message) {
    const container = document.getElementById("comparisonResults");

    if (!container) return;

    container.innerHTML = `
        <div class="comparison-loading">
            ${escapeHtml(message)}
        </div>
    `;
}

function showSelectionPrompt(message) {
    updateSelectorMessage(message);
    showLoading(message);

    setText("overallResultTitle", "Waiting for contract selection");
    setText("overallResultDescription", message);
}

function showComparisonError(message) {
    const safeMessage =
        message || "An unexpected error occurred.";

    updateSelectorMessage(safeMessage);

    const results = document.getElementById("comparisonResults");

    if (results) {
        results.innerHTML = `
            <div class="comparison-error">
                <strong>Comparison unavailable</strong>
                <p>${escapeHtml(safeMessage)}</p>
                <p>
                    Check that the backend is running and that both
                    contracts have been analyzed.
                </p>
            </div>
        `;
    }

    const unchanged = document.getElementById("unchangedClauses");
    const regression = document.getElementById("regressionSection");

    if (unchanged) unchanged.replaceChildren();
    regression?.classList.add("hidden");

    setText("overallResultTitle", "Comparison unavailable");
    setText("overallResultDescription", safeMessage);

    setText("changesDetected", "—");
    setText("riskIncreased", "—");
    setText("riskReduced", "—");
    setText("unchangedCount", "—");
    setText("netRiskImpact", "—");
    setText("comparisonResultCount", "0");
}

function updateSelectorMessage(message) {
    setText("selectorMessage", message);
}

/* =========================================================
   SYSTEM STATUS
========================================================= */

function setSystemStatus(state, message) {
    const status = document.getElementById("systemStatus");
    const description = document.getElementById("systemStatusText");
    const dot = document.querySelector(".status-dot");

    if (status) {
        status.textContent =
            state === "error"
                ? "System Attention"
                : state === "loading"
                    ? "Processing"
                    : "System Online";
    }

    if (description) {
        description.textContent = message;
    }

    if (dot) {
        dot.style.background =
            state === "error"
                ? "#ff5c70"
                : state === "loading"
                    ? "#f0b45c"
                    : "#26d98a";
    }
}

/* =========================================================
   METRICS
========================================================= */

function extractMetrics(summary) {
    const risksReduced = Number(summary.risks_reduced || 0);
    const risksIncreased = Number(summary.risks_increased || 0);
    const risksResolved = Number(summary.risks_resolved || 0);
    const newRisks = Number(summary.new_risks || 0);
    const unchanged = Number(summary.unchanged || 0);
    const netRiskImprovement =
        Number(summary.net_risk_improvement || 0);

    return {
        risksReduced,
        risksIncreased,
        risksResolved,
        newRisks,
        unchanged,
        netRiskImprovement,
        riskRegression: Boolean(summary.risk_regression),

        changesDetected:
            risksReduced +
            risksIncreased +
            risksResolved +
            newRisks
    };
}

function renderComparison(data) {
    const summary = data.risk_summary || {};
    const metrics = extractMetrics(summary);

    renderMetrics(metrics);
    renderOverallResult(metrics);
    renderRiskChanges(data);
    renderUnchanged(summary);
    renderRegression(data, metrics);

    setText(
        "comparisonResultCount",
        data.risk_changes.length
    );
}

function renderMetrics(metrics) {
    setText("changesDetected", metrics.changesDetected);

    setText(
        "riskIncreased",
        metrics.risksIncreased + metrics.newRisks
    );

    setText(
        "riskReduced",
        metrics.risksReduced + metrics.risksResolved
    );

    setText("unchangedCount", metrics.unchanged);

    const net = metrics.netRiskImprovement;

    setText(
        "netRiskImpact",
        `${net > 0 ? "+" : ""}${net}`
    );
}

/* =========================================================
   OVERALL RESULT
========================================================= */

function renderOverallResult(metrics) {
    const card = document.getElementById("overallResult");
    const title = document.getElementById("overallResultTitle");
    const description =
        document.getElementById("overallResultDescription");

    const icon = card?.querySelector(".overall-result-icon");

    if (!card || !title || !description) return;

    card.classList.remove(
        "result-improved",
        "result-regression",
        "result-neutral"
    );

    const hasRegression =
        metrics.riskRegression ||
        metrics.risksIncreased > 0 ||
        metrics.newRisks > 0;

    if (hasRegression) {
        card.classList.add("result-regression");

        if (icon) icon.textContent = "!";

        title.textContent = "RISK REGRESSION DETECTED";

        description.textContent =
            `${metrics.risksIncreased} increased risk finding(s) and ` +
            `${metrics.newRisks} new risk finding(s). Review before approval.`;

        return;
    }

    if (metrics.risksReduced > 0 || metrics.risksResolved > 0) {
        card.classList.add("result-improved");

        if (icon) icon.textContent = "✓";

        title.textContent = "RISK PROFILE IMPROVED";

        description.textContent =
            `${metrics.risksReduced} risk finding(s) reduced and ` +
            `${metrics.risksResolved} resolved, with no detected regression.`;

        return;
    }

    card.classList.add("result-neutral");

    if (icon) icon.textContent = "—";

    title.textContent = "NO MATERIAL RISK IMPROVEMENT";

    description.textContent =
        "The comparison did not identify a net reduction in playbook risk.";
}

/* =========================================================
   IMPACT NORMALIZATION
========================================================= */

function normalizeImpact(value) {
    const impact = String(value || "NO CHANGE")
        .trim()
        .toUpperCase();

    const validImpacts = new Set([
        "RISK REDUCED",
        "RISK INCREASED",
        "RISK RESOLVED",
        "NEW RISK",
        "NEW STANDARD FINDING",
        "FINDING REMOVED",
        "NO CHANGE"
    ]);

    return validImpacts.has(impact)
        ? impact
        : "NO CHANGE";
}

function impactClass(impact) {
    if (
        impact === "RISK REDUCED" ||
        impact === "RISK RESOLVED"
    ) {
        return "reduced";
    }

    if (
        impact === "RISK INCREASED" ||
        impact === "NEW RISK"
    ) {
        return "increased";
    }

    return "same";
}

/* =========================================================
   RENDER RISK CHANGES
========================================================= */

function renderRiskChanges(data) {
    const container = document.getElementById("comparisonResults");

    if (!container) return;

    const changes = Array.isArray(data.risk_changes)
        ? data.risk_changes
        : [];

    if (changes.length === 0) {
        container.innerHTML = `
            <div class="comparison-empty">
                The backend returned no risk-change records.
            </div>
        `;
        return;
    }

    container.innerHTML = changes
        .map(renderRiskChangeCard)
        .join("");
}

function renderRiskChangeCard(item) {
    const impact = normalizeImpact(item.risk_impact);
    const className = impactClass(impact);

    const category = escapeHtml(item.category || "Contract rule");
    const ruleId = escapeHtml(item.rule_id || "Rule not specified");

    const reason = escapeHtml(
        item.v2?.reason ||
        item.v1?.reason ||
        "Review the contract evidence against the applicable playbook rule."
    );

    return `
        <article class="comparison-change-card ${className}">
            <div class="comparison-change-header">
                <div>
                    <span class="card-label">${ruleId}</span>
                    <h4>${category}</h4>
                </div>

                <span class="impact-badge ${className}">
                    ${escapeHtml(impact)}
                </span>
            </div>

            <div class="comparison-diff-grid">
                ${renderVersionPanel("FIRST CONTRACT", item.v1)}

                <div class="comparison-diff-arrow" aria-hidden="true">
                    →
                </div>

                ${renderVersionPanel("SECOND CONTRACT", item.v2)}
            </div>

            <div class="comparison-explanation">
                <strong>Assessment</strong>
                <p>${reason}</p>

                ${renderPlaybookRequirement(item)}

                ${renderRecommendedAction(item)}
            </div>
        </article>
    `;
}

function renderVersionPanel(label, finding) {
    if (!finding) {
        return `
            <div class="comparison-version-panel">
                <span class="card-label">${escapeHtml(label)}</span>

                <strong>Finding not present</strong>

                <p>
                    No finding for this rule was returned for this contract.
                </p>
            </div>
        `;
    }

    const status = String(
        finding.status || "NOT SPECIFIED"
    ).toUpperCase();

    const severity = String(
        finding.severity || "NOT SPECIFIED"
    ).toUpperCase();

    const actual = finding.actual || "Actual value not specified";
    const evidence = finding.evidence || "No evidence returned";

    return `
        <div class="comparison-version-panel">
            <span class="card-label">${escapeHtml(label)}</span>

            <div class="comparison-status-row">
                <span class="status-pill ${statusClass(status)}">
                    ${escapeHtml(status)}
                </span>

                <span class="severity-label">
                    ${escapeHtml(severity)}
                </span>
            </div>

            <strong class="comparison-actual">
                ${escapeHtml(actual)}
            </strong>

            <div class="comparison-evidence">
                <strong>Contract evidence</strong>
                <p>${escapeHtml(evidence)}</p>
            </div>

            ${
                finding.expected
                    ? `
                        <p class="comparison-expected">
                            <strong>Expected:</strong>
                            ${escapeHtml(finding.expected)}
                        </p>
                    `
                    : ""
            }
        </div>
    `;
}

function renderPlaybookRequirement(item) {
    const requirement =
        item.v2?.expected ||
        item.v1?.expected;

    if (!requirement) return "";

    return `
        <p class="comparison-playbook-requirement">
            <strong>Playbook requirement:</strong>
            ${escapeHtml(requirement)}
        </p>
    `;
}

function renderRecommendedAction(item) {
    const action =
        item.v2?.recommended_action ||
        item.v1?.recommended_action;

    if (!action) return "";

    return `
        <p class="comparison-recommended-action">
            <strong>Recommended action:</strong>
            ${escapeHtml(action)}
        </p>
    `;
}

function statusClass(status) {
    switch (status) {
        case "RISKY":
            return "status-risky";

        case "MISSING":
            return "status-missing";

        case "AMBIGUOUS":
            return "status-ambiguous";

        case "STANDARD":
            return "status-standard";

        default:
            return "status-unknown";
    }
}

/* =========================================================
   UNCHANGED RULES
========================================================= */

function renderUnchanged(summary) {
    const container = document.getElementById("unchangedClauses");

    if (!container) return;

    // The current backend returns an unchanged count, not a dedicated
    // unchanged_clauses array. Do not fabricate clause-level details.
    const count = Number(summary.unchanged || 0);

    if (count === 0) {
        container.innerHTML = `
            <div class="comparison-empty">
                No rules were classified as having an unchanged risk state.
            </div>
        `;
        return;
    }

    container.innerHTML = `
        <div class="unchanged-item">
            <strong>${count} unchanged risk rule(s)</strong>
            <span>
                These rules retained the same risk score. This does not
                necessarily mean their clause wording remained identical.
            </span>
        </div>
    `;
}

/* =========================================================
   REGRESSION ALERT
========================================================= */

function renderRegression(data, metrics) {
    const section = document.getElementById("regressionSection");
    const container = document.getElementById("regressionContent");

    if (!section || !container) return;

    const changes = Array.isArray(data.risk_changes)
        ? data.risk_changes
        : [];

    const regressions = changes.filter(item => {
        const impact = normalizeImpact(item.risk_impact);

        return (
            impact === "RISK INCREASED" ||
            impact === "NEW RISK"
        );
    });

    const hasRegression =
        metrics.riskRegression ||
        metrics.risksIncreased > 0 ||
        metrics.newRisks > 0;

    if (!hasRegression) {
        section.classList.add("hidden");
        container.replaceChildren();
        return;
    }

    section.classList.remove("hidden");

    if (regressions.length === 0) {
        container.innerHTML = `
            <div class="regression-item">
                <strong>Backend reported a regression</strong>
                <p>
                    Review the risk summary and selected contracts before
                    accepting the revised version.
                </p>
            </div>
        `;
        return;
    }

    container.innerHTML = regressions.map(item => `
        <div class="regression-item">
            <strong>
                ${escapeHtml(item.category || item.rule_id || "Risk finding")}
            </strong>

            <p>
                ${escapeHtml(
                    item.v2?.reason ||
                    item.v2?.evidence ||
                    "The revised contract introduced or increased risk."
                )}
            </p>

            <p>
                <strong>Impact:</strong>
                ${escapeHtml(normalizeImpact(item.risk_impact))}
            </p>
        </div>
    `).join("");
}

/* =========================================================
   GENERAL HELPERS
========================================================= */

function setText(id, value) {
    const element = document.getElementById(id);

    if (element) {
        element.textContent = String(value ?? "");
    }
}

function escapeHtml(value) {
    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
