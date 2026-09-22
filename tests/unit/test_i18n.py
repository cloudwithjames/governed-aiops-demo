import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "api"))

from app.i18n import I18N, get_i18n, get_message


REQUIRED_KEYS = [
    "title", "subtitle", "reset_demo", "inject_incident", "start_diagnosis",
    "customer_portal", "gateway", "backend", "healthy", "critical",
    "observe", "diagnose", "plan", "approval", "execute", "verify", "record",
    "evidence_board", "root_cause", "confidence", "evidence_ids",
    "remediation_plan", "action", "expected_impact", "risk", "blast_radius",
    "rollback", "post_checks", "approve_change", "reject_change",
    "approval_message", "ai_engineer", "final_report",
    "incident_id", "status", "approved_by", "verification", "mttr",
    "started", "resolved", "download_json", "mode",
    "ai_reasons", "human_approves", "tools_execute",
]


def test_all_keys_exist_in_en():
    for key in REQUIRED_KEYS:
        assert key in I18N["en"], f"Missing key '{key}' in EN"


def test_all_keys_exist_in_zh():
    for key in REQUIRED_KEYS:
        assert key in I18N["zh"], f"Missing key '{key}' in ZH"


def test_get_i18n_en():
    result = get_i18n("en")
    assert result["title"] == "Huawei Cloud Governed AI Operations"


def test_get_i18n_zh():
    result = get_i18n("zh")
    assert "华为云" in result["title"]


def test_get_i18n_fallback():
    result = get_i18n("fr")
    assert result == I18N["en"]


def test_get_message():
    assert get_message("en", "healthy") == "Healthy"
    assert get_message("zh", "healthy") == "正常"


def test_en_zh_have_same_keys():
    en_keys = set(I18N["en"].keys())
    zh_keys = set(I18N["zh"].keys())
    assert en_keys == zh_keys, f"Key mismatch: EN-only={en_keys-zh_keys}, ZH-only={zh_keys-en_keys}"
