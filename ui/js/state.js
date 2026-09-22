const state = {
    incidentId: null,
    incidentStatus: null,
    mode: "mock",
    sseSource: null,
    evidence: [],
    events: [],
    rootCause: null,
    plan: null,
    report: null,
    timelineSteps: {
        1: "pending", 2: "pending", 3: "pending",
        4: "pending", 5: "pending", 6: "pending", 7: "pending",
    },
};

const STATE_TO_STEP = {
    IDLE: null,
    INCIDENT_DETECTED: 1,
    OBSERVING: 1,
    DIAGNOSING: 2,
    PLAN_READY: 3,
    WAITING_APPROVAL: 4,
    APPROVED: 4,
    REJECTED: 4,
    EXECUTING: 5,
    VERIFYING: 6,
    RECOVERED: 6,
    FAILED: null,
    REPORTED: 7,
};

function updateTimeline(status) {
    const currentStep = STATE_TO_STEP[status];
    for (let i = 1; i <= 7; i++) {
        if (status === "REPORTED") {
            state.timelineSteps[i] = "completed";
        } else if (status === "RECOVERED") {
            state.timelineSteps[i] = (i <= 6) ? "completed" : "active";
        } else if (currentStep === null && status === "FAILED") {
            state.timelineSteps[i] = "failed";
        } else if (currentStep === null) {
            state.timelineSteps[i] = "pending";
        } else if (i < currentStep) {
            state.timelineSteps[i] = "completed";
        } else if (i === currentStep) {
            if (status === "WAITING_APPROVAL") {
                state.timelineSteps[i] = "waiting";
            } else if (status === "APPROVED") {
                state.timelineSteps[i] = "completed";
            } else {
                state.timelineSteps[i] = "active";
            }
        } else {
            state.timelineSteps[i] = "pending";
        }
    }
    renderTimeline();
}

function resetState() {
    state.incidentId = null;
    state.incidentStatus = null;
    state.evidence = [];
    state.events = [];
    state.rootCause = null;
    state.plan = null;
    state.report = null;
    for (let i = 1; i <= 7; i++) state.timelineSteps[i] = "pending";
    if (state.sseSource) {
        state.sseSource.close();
        state.sseSource = null;
    }
}
