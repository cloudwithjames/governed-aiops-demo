function toSaoPauloTime(utcStr) {
    if (!utcStr) return "";
    try {
        const d = new Date(utcStr);
        const opts = { timeZone: "America/Sao_Paulo", hour12: false,
            year: "numeric", month: "2-digit", day: "2-digit",
            hour: "2-digit", minute: "2-digit", second: "2-digit" };
        return d.toLocaleString("pt-BR", opts);
    } catch(e) {
        const d = new Date(utcStr);
        const sp = new Date(d.getTime() - 3 * 3600 * 1000);
        return sp.toISOString().replace("T", " ").substring(0, 19);
    }
}

function toSaoPauloTimeShort() {
    try {
        const d = new Date();
        return d.toLocaleString("pt-BR", { timeZone: "America/Sao_Paulo", hour12: false,
            year: "numeric", month: "2-digit", day: "2-digit",
            hour: "2-digit", minute: "2-digit", second: "2-digit" });
    } catch(e) {
        const d = new Date();
        const sp = new Date(d.getTime() - 3 * 3600 * 1000);
        return sp.toISOString().replace("T", " ").substring(0, 19);
    }
}

function applyI18n() {
    const map = {
        "title": "title", "subtitle": "subtitle",
        "reset-demo": "reset_demo",
        "btn-inject": "inject_incident", "btn-diagnose": "start_diagnosis",
        "label-portal": "customer_portal", "label-gateway": "gateway", "label-backend": "backend",
        "step-1": "observe", "step-2": "diagnose", "step-3": "plan",
        "step-4": "approval", "step-5": "execute", "step-6": "verify", "step-7": "record",
        "evidence-title": "evidence_board",
        "agent-title": "ai_engineer",
        "rc-title": "root_cause", "rc-cause-label": "root_cause",
        "rc-confidence-label": "confidence", "rc-evidence-label": "evidence_ids",
        "rc-time-label": "rc_time",
        "plan-title": "remediation_plan",
        "plan-action-label": "action", "plan-impact-label": "expected_impact",
        "plan-risk-label": "risk", "plan-blast-label": "blast_radius",
        "plan-rollback-label": "rollback", "plan-postchecks-label": "post_checks",
        "plan-time-label": "plan_time",
        "approval-title": "approval", "approval-message": "approval_message",
        "btn-approve": "approve_change", "btn-reject": "reject_change",
        "exec-title": "exec_title",
        "report-title": "final_report", "btn-download": "download_json",
        "service-status-title": "service_status",
        "timeline-title": "timeline_title",
    };
    for (const [id, key] of Object.entries(map)) {
        const el = document.getElementById(id);
        if (el) el.textContent = t(key);
    }
    document.getElementById("principle-1").textContent = t("ai_reasons");
    document.getElementById("principle-2").textContent = t("human_approves");
    document.getElementById("principle-3").textContent = t("tools_execute");

    const portalLink = document.getElementById("portal-link");
    if (portalLink) portalLink.textContent = t("open_portal");

    const modeBadge = document.getElementById("mode-badge");
    modeBadge.textContent = state.mode === "hermes" ? t("mode_hermes") : t("mode_mock");

    const transcript = document.getElementById("agent-transcript");
    if (transcript && transcript.children.length === 0) {
        transcript.innerHTML = `<p style="color:#999">${t("no_transcript")}</p>`;
    }
    const evidenceBoard = document.getElementById("evidence-board");
    if (evidenceBoard && evidenceBoard.children.length === 0) {
        evidenceBoard.innerHTML = `<p style="color:#999">${t("no_evidence")}</p>`;
    }
}

function renderTimeline() {
    for (let i = 1; i <= 7; i++) {
        const el = document.querySelector(`.timeline-step[data-step="${i}"]`);
        if (!el) continue;
        el.className = `timeline-step step-${state.timelineSteps[i]}`;
    }
}

function renderServiceStatus(data) {
    const portalEl = document.getElementById("status-portal");
    const gatewayEl = document.getElementById("status-gateway");
    const backendEl = document.getElementById("status-backend");

    const setStatus = (el, healthy, label) => {
        const cls = healthy ? "status-healthy" : "status-critical";
        el.className = `card-status ${cls}`;
        el.textContent = healthy ? t("healthy") : t("critical");
    };

    setStatus(portalEl, data.portal_healthy, "portal");
    setStatus(backendEl, data.backend_healthy, "backend");

    const gatewayHealthy = data.gateway_upstream && data.gateway_upstream.includes(":8080");
    setStatus(gatewayEl, gatewayHealthy, "gateway");

    document.getElementById("card-portal").querySelector(".card-status").textContent =
        data.portal_healthy ? t("healthy") : t("critical");
    document.getElementById("card-backend").querySelector(".card-status").textContent =
        data.backend_healthy ? t("healthy") : t("critical");
    document.getElementById("card-gateway").querySelector(".card-status").textContent =
        gatewayHealthy ? t("healthy") : t("critical");
}

function renderEvidence(evidence) {
    const board = document.getElementById("evidence-board");
    if (!evidence || evidence.length === 0) {
        board.innerHTML = `<p style="color:#999">${t("no_evidence")}</p>`;
        return;
    }
    board.innerHTML = evidence.map(ev => {
        const summary = currentLang === "zh" ? ev.summary_zh : ev.summary_en;
        let rawDisplay = JSON.parse(JSON.stringify(ev.raw_json || {}));
        if (rawDisplay.entries && Array.isArray(rawDisplay.entries)) {
            const seen = new Map();
            const deduped = [];
            for (const entry of rawDisplay.entries) {
                const key = `${entry.message}|${entry.target}|${entry.error}`;
                if (seen.has(key)) {
                    const existing = deduped[seen.get(key)];
                    existing.count = (existing.count || 1) + 1;
                } else {
                    seen.set(key, deduped.length);
                    deduped.push(entry);
                }
            }
            for (const e of deduped) {
                if (e.timestamp) e.timestamp = toSaoPauloTime(e.timestamp);
            }
            rawDisplay.entries = deduped;
        }
        if (rawDisplay.changes) {
            for (const c of rawDisplay.changes) {
                if (c.timestamp) c.timestamp = toSaoPauloTime(c.timestamp);
            }
        }
        const ts = ev.created_at ? toSaoPauloTime(ev.created_at) : "";
        return `<div class="evidence-card" onclick="this.classList.toggle('expanded')">
            <span class="evidence-code">${ev.evidence_code}</span>
            <span class="evidence-summary">${summary}</span>
            ${ts ? `<span class="evidence-time">${ts}</span>` : ""}
            <div class="evidence-raw">${JSON.stringify(rawDisplay, null, 2)}</div>
        </div>`;
    }).join("");
}

function addTranscript(source, message) {
    const transcript = document.getElementById("agent-transcript");
    if (transcript.querySelector("p[style]")) transcript.innerHTML = "";
    const ts = toSaoPauloTimeShort();
    const entry = document.createElement("div");
    entry.className = "transcript-entry";
    entry.innerHTML = `<span class="transcript-time">${ts}</span> <span class="transcript-source ${source}">[${source.toUpperCase()}]</span> ${message}`;
    transcript.appendChild(entry);
    transcript.scrollTop = transcript.scrollHeight;
}

function renderRootCause(rc) {
    if (!rc) { document.getElementById("root-cause-section").style.display = "none"; return; }
    document.getElementById("root-cause-section").style.display = "block";
    const cause = currentLang === "zh" ? rc.zh : rc.en;
    document.getElementById("rc-cause").textContent = cause || rc.en || "";
    document.getElementById("rc-confidence").textContent = `${(rc.confidence * 100).toFixed(0)}%`;
    document.getElementById("rc-evidence").textContent = (rc.evidence_ids || []).join(", ");
    document.getElementById("rc-time").textContent = toSaoPauloTimeShort();
}

function renderPlan(plan) {
    if (!plan) { document.getElementById("plan-section").style.display = "none"; return; }
    document.getElementById("plan-section").style.display = "block";
    document.getElementById("plan-action").textContent = plan.action || "";
    const impact = plan.impact ? (currentLang === "zh" ? plan.impact.zh : plan.impact.en) : "";
    document.getElementById("plan-impact").textContent = impact;
    document.getElementById("plan-risk").textContent = plan.risk || "";
    const blast = plan.blast_radius ? (currentLang === "zh" ? plan.blast_radius.zh : plan.blast_radius.en) : "";
    document.getElementById("plan-blast").textContent = blast;
    const rollback = plan.rollback ? (currentLang === "zh" ? plan.rollback.zh : plan.rollback.en) : "";
    document.getElementById("plan-rollback").textContent = rollback;
    document.getElementById("plan-postchecks").textContent = (plan.post_checks || []).join(", ");
    document.getElementById("plan-time").textContent = toSaoPauloTimeShort();
}

function renderApproval(visible) {
    document.getElementById("approval-section").style.display = visible ? "block" : "none";
}

function renderExec(content) {
    if (!content) { document.getElementById("exec-section").style.display = "none"; return; }
    document.getElementById("exec-section").style.display = "block";
    document.getElementById("exec-content").innerHTML = content;
}

function renderReport(report) {
    if (!report) { document.getElementById("report-section").style.display = "none"; return; }
    document.getElementById("report-section").style.display = "block";
    const rc = report.root_cause || {};
    const rcText = currentLang === "zh" ? (rc.zh || rc.en || "") : (rc.en || "");
    const remediation = report.remediation || {};
    const remText = currentLang === "zh" ? (remediation.zh || remediation.en || "") : (remediation.en || "");
    const verification = report.verification || {};
    const checks = verification.checks || {};

    let html = "";
    html += `<div class="report-row"><span class="report-label">${t("incident_id")}</span><span>${report.incident_id || ""}</span></div>`;
    const statusClass = (report.status === "REPORTED" || report.status === "RESOLVED") ? "report-status-ok" : "report-status-err";
    html += `<div class="report-row"><span class="report-label">${t("status")}</span><span class="${statusClass}">${report.status || ""}</span></div>`;
    html += `<div class="report-row"><span class="report-label">${t("root_cause")}</span><span>${rcText}</span></div>`;
    html += `<div class="report-row"><span class="report-label">${t("approved_by")}</span><span>${report.approval?.approved_by || ""}</span></div>`;
    html += `<div class="report-row"><span class="report-label">${t("verification")}</span><span>${Object.entries(checks).map(([k,v]) => `${k}: ${v ? "✓" : "✗"}`).join(", ")}</span></div>`;
    html += `<div class="report-row"><span class="report-label">${t("mttr")}</span><span>${report.mttr_seconds || 0}</span></div>`;
    html += `<div class="report-row"><span class="report-label">${t("started")}</span><span>${report.started || ""}</span></div>`;
    html += `<div class="report-row"><span class="report-label">${t("resolved")}</span><span>${report.resolved || ""}</span></div>`;
    document.getElementById("report-content").innerHTML = html;
    state.report = report;
}

function connectSSE(incidentId) {
    if (state.sseSource) state.sseSource.close();
    state.sseSource = new EventSource(`/api/incidents/${incidentId}/stream`);
    state.sseSource.addEventListener("event", async (e) => {
        const msg = JSON.parse(e.data);
        const ev = msg.data;
        state.events.push(ev);
        addTranscript(ev.source, `${ev.message_code}: ${JSON.stringify(ev.message_params || {})}`);

        if (ev.message_code && ev.message_code.startsWith("STATE_")) {
            const newStatus = ev.message_code.replace("STATE_", "");
            state.incidentStatus = newStatus;
            updateTimeline(newStatus);
            if (newStatus === "WAITING_APPROVAL") renderApproval(true);
            else renderApproval(false);
        }

        if (ev.message_code === "FIX_EXECUTED" || ev.message_code === "FIX_RESULT") {
            const params = ev.message_params || {};
            if (params.before || params.after) {
                renderExec(`<div class="exec-check"><span class="check-pass">✓ upstream changed: ${params.before || "?"} → ${params.after || "?"}</span></div>`);
            }
        }

        if (ev.message_code === "VERIFY_RESULT") {
            const checks = (ev.raw_payload || {}).checks || {};
            let html = "";
            for (const [k, v] of Object.entries(checks)) {
                html += `<div class="exec-check"><span class="${v ? "check-pass" : "check-fail"}">${v ? "✓" : "✗"} ${k}</span></div>`;
            }
            renderExec(html);
            const allPass = (ev.raw_payload || {}).all_pass;
            addTranscript("tool", allPass ? t("verification_passed") : t("verification_failed"));
        }

        if (ev.message_code === "REPORT_GENERATED") {
            addTranscript("system", t("report_generated"));
        }

        const incident = await getIncident(incidentId);
        if (incident.root_cause) renderRootCause(incident.root_cause);
        if (incident.plan) renderPlan(incident.plan);
        if (incident.verification) {
            const checks = incident.verification.checks || {};
            let html = "";
            for (const [k, v] of Object.entries(checks)) {
                html += `<div class="exec-check"><span class="${v ? "check-pass" : "check-fail"}">${v ? "✓" : "✗"} ${k}</span></div>`;
            }
            if (html) renderExec(html);
        }
        if (incident.report) renderReport(incident.report);

        await refreshStatus();
    });
    state.sseSource.addEventListener("evidence", async (e) => {
        const msg = JSON.parse(e.data);
        const ev = msg.data;
        const existing = state.evidence.find(x => x.evidence_code === ev.evidence_code);
        if (!existing) state.evidence.push(ev);
        else Object.assign(existing, ev);
        renderEvidence(state.evidence);
    });
    state.sseSource.onerror = () => {
        setTimeout(() => { if (state.incidentId) connectSSE(state.incidentId); }, 3000);
    };
}

async function refreshStatus() {
    try {
        const status = await fetchDemoStatus();
        renderServiceStatus(status);
    } catch (e) { console.error("status error:", e); }
}

async function resetDemo() {
    try {
        await resetDemoApi();
        resetState();
        renderTimeline();
        renderEvidence([]);
        renderRootCause(null);
        renderPlan(null);
        renderApproval(false);
        renderExec(null);
        renderReport(null);
        document.getElementById("agent-transcript").innerHTML = "";
        document.getElementById("btn-diagnose").disabled = true;
        await refreshStatus();
        applyI18n();
    } catch (e) { console.error("reset error:", e); }
}

async function injectIncident() {
    try {
        const result = await injectIncidentApi();
        renderServiceStatus(result);
        addTranscript("system", t("inject_incident"));
        const incident = await createIncident();
        state.incidentId = incident.id;
        state.incidentStatus = incident.status;
        document.getElementById("btn-diagnose").disabled = false;
        connectSSE(incident.id);
        addTranscript("system", `Incident ${incident.id} created`);
    } catch (e) { console.error("inject error:", e); }
}

async function startDiagnosis() {
    if (!state.incidentId) return;
    try {
        document.getElementById("btn-diagnose").disabled = true;
        addTranscript("agent", t("diagnosis_started"));
        await runDiagnosis(state.incidentId);
    } catch (e) {
        console.error("diagnosis error:", e);
        addTranscript("system", `Error: ${e.message}`);
        document.getElementById("btn-diagnose").disabled = false;
    }
}

async function approveIncident() {
    if (!state.incidentId) return;
    try {
        renderApproval(false);
        addTranscript("human", t("approval_granted"));
        await approveIncidentApi(state.incidentId, "Demo Operator");
    } catch (e) {
        console.error("approve error:", e);
        addTranscript("system", `Error: ${e.message}`);
    }
}

async function rejectIncident() {
    if (!state.incidentId) return;
    try {
        renderApproval(false);
        addTranscript("human", t("approval_rejected"));
        await rejectIncidentApi(state.incidentId, "Demo Operator");
    } catch (e) { console.error("reject error:", e); }
}

function downloadReport() {
    if (!state.report) return;
    const blob = new Blob([JSON.stringify(state.report, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `report-${state.incidentId || "unknown"}.json`;
    a.click();
    URL.revokeObjectURL(url);
}

async function init() {
    try {
        const modeData = await fetchMode();
        state.mode = modeData.mode;
    } catch (e) { state.mode = "mock"; }
    setLang(currentLang);
    applyI18n();
    await refreshStatus();
    setInterval(refreshStatus, 5000);
}

init();
