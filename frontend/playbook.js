"use strict";
const PLAYBOOK_API = "http://127.0.0.1:8001/contracts/playbook/rules";
const ruleGrid = document.getElementById("ruleGrid");
const pageStatus = document.getElementById("pageStatus");
const setStatus = (message, error = false) => {
  pageStatus.textContent = message;
  pageStatus.style.color = error ? "#ff7b86" : "#27d17f";
};
function field(labelText, name, value, multiline = false) {
  const label = document.createElement("label");
  label.textContent = labelText;
  label.htmlFor = `${name}-${Math.random().toString(36).slice(2, 9)}`;
  const input = document.createElement(multiline ? "textarea" : "input");
  input.id = label.htmlFor;
  input.name = name;
  input.value = value || "";
  label.appendChild(input);
  return { label, input };
}
async function loadRules() {
  ruleGrid.replaceChildren();
  setStatus("Loading playbook rules…");
  try {
    const response = await fetch(PLAYBOOK_API);
    if (!response.ok) throw new Error(`API returned ${response.status}`);
    const payload = await response.json();
    for (const rule of payload.rules || []) renderRule(rule);
    setStatus(`${(payload.rules || []).length} rules loaded. Changes apply to future analyses.`);
  } catch (error) {
    setStatus(`Could not load rules: ${error.message}. Check that the backend is running.`, true);
  }
}
function renderRule(rule) {
  const card = document.createElement("form");
  card.className = "rule-editor";
  const id = document.createElement("div"); id.className = "rule-id"; id.textContent = rule.rule_id;
  const title = document.createElement("h3"); title.textContent = rule.category;
  card.append(id, title);
  const requirement = field("Requirement", "requirement", rule.requirement, true);
  const description = field("Description / evaluation guidance", "description", rule.description, true);
  const severityLabel = document.createElement("label"); severityLabel.textContent = "Severity";
  const severity = document.createElement("select"); severity.name = "severity";
  for (const value of ["LOW", "MEDIUM", "HIGH"]) {
    const option = document.createElement("option"); option.value = value; option.textContent = value;
    option.selected = value === (rule.severity || "MEDIUM"); severity.appendChild(option);
  }
  severityLabel.appendChild(severity);
  const save = document.createElement("button"); save.type = "submit"; save.textContent = "Save rule";
  const notice = document.createElement("div"); notice.className = "notice"; notice.hidden = true;
  card.append(requirement.label, description.label, severityLabel, save, notice);
  card.addEventListener("submit", async (event) => {
    event.preventDefault(); save.disabled = true; notice.hidden = true;
    try {
      const response = await fetch(`${PLAYBOOK_API}/${encodeURIComponent(rule.rule_id)}`, {
        method: "PUT", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ requirement: requirement.input.value, description: description.input.value, severity: severity.value })
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || `API returned ${response.status}`);
      notice.textContent = "Saved. Re-analyze contracts to apply this rule."; notice.hidden = false;
      setStatus(`Updated ${rule.rule_id}. Existing findings were not changed.`);
    } catch (error) { setStatus(`Could not save ${rule.rule_id}: ${error.message}`, true); }
    finally { save.disabled = false; }
  });
  ruleGrid.appendChild(card);
}
document.getElementById("refreshRules").addEventListener("click", loadRules);
loadRules();
