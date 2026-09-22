async function apiGet(path) {
    const resp = await fetch(`/api${path}`);
    if (!resp.ok) throw new Error(`API ${path}: ${resp.status}`);
    return resp.json();
}

async function apiPost(path, body) {
    const resp = await fetch(`/api${path}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: body ? JSON.stringify(body) : undefined,
    });
    if (!resp.ok) throw new Error(`API ${path}: ${resp.status}`);
    return resp.json();
}

async function fetchDemoStatus() {
    return apiGet("/demo/status");
}

async function injectIncidentApi() {
    return apiPost("/demo/inject");
}

async function resetDemoApi() {
    return apiPost("/demo/reset");
}

async function createIncident() {
    return apiPost("/incidents");
}

async function runDiagnosis(id) {
    return apiPost(`/incidents/${id}/run-diagnosis`);
}

async function approveIncidentApi(id, approver) {
    const resp = await fetch(`/api/incidents/${id}/approve`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: `approver=${encodeURIComponent(approver)}`,
    });
    return resp.json();
}

async function rejectIncidentApi(id, approver) {
    const resp = await fetch(`/api/incidents/${id}/reject`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: `approver=${encodeURIComponent(approver)}`,
    });
    return resp.json();
}

async function getIncident(id) {
    return apiGet(`/incidents/${id}`);
}

async function getEvents(id) {
    return apiGet(`/incidents/${id}/events`);
}

async function getEvidence(id) {
    return apiGet(`/incidents/${id}/evidence`);
}

async function getReport(id) {
    return apiGet(`/incidents/${id}/report`);
}

async function fetchMode() {
    return apiGet("/mode");
}
