"""Static checks for the windows-sleep-wake-fix skill.

PowerShell is not available in CI, so these tests verify that the script
contains every setting it promises, supports undo, and is saved in an
encoding Windows PowerShell 5.1 reads correctly (UTF-8 with BOM).
"""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = ROOT / ".codex" / "skills" / "windows-sleep-wake-fix"
PS1 = SKILL_DIR / "scripts" / "fix-sleep-wake.ps1"
CMD = SKILL_DIR / "scripts" / "run-fix.cmd"
SKILL_MD = SKILL_DIR / "SKILL.md"

USB_SUBGROUP = "2a737441-1930-4402-8d77-b2bebba308a3"
USB_SELECTIVE_SUSPEND = "48e6b7a6-50f5-4782-a5d4-53bb8f07e226"


@pytest.fixture(scope="module")
def script_text() -> str:
    return PS1.read_text(encoding="utf-8-sig")


def test_skill_files_exist():
    assert SKILL_MD.exists()
    assert PS1.exists()
    assert CMD.exists()
    assert (SKILL_DIR / "agents" / "openai.yaml").exists()


def test_skill_frontmatter_has_name_and_description():
    text = SKILL_MD.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    header = text.split("---", 2)[1]
    assert "name: windows-sleep-wake-fix" in header
    assert "description:" in header


def test_ps1_is_utf8_with_bom():
    # Windows PowerShell 5.1 misreads Korean text in BOM-less UTF-8 files.
    assert PS1.read_bytes().startswith(b"\xef\xbb\xbf")


def test_requires_admin(script_text):
    assert "#Requires -RunAsAdministrator" in script_text


def test_disables_fast_startup(script_text):
    assert "HiberbootEnabled" in script_text


def test_disables_usb_selective_suspend_on_ac_and_dc(script_text):
    assert USB_SUBGROUP in script_text
    assert USB_SELECTIVE_SUSPEND in script_text
    assert "/setacvalueindex" in script_text
    assert "/setdcvalueindex" in script_text


def test_disables_pcie_link_state_power_management(script_text):
    assert "SUB_PCIEXPRESS" in script_text
    assert "ASPM" in script_text


def test_reapplies_active_scheme(script_text):
    assert "/setactive" in script_text


def test_backs_up_before_changing(script_text):
    export_call = script_text.index("Invoke-PowerCfg /export")
    first_change = script_text.index("Set-ItemProperty -Path $PowerKey -Name HiberbootEnabled -Value 0")
    first_power_change = script_text.index("Set-PowerValue $UsbSubgroup $UsbSuspend 0 0")
    assert export_call < first_change
    assert export_call < first_power_change


def test_supports_undo(script_text):
    assert "[switch]$Undo" in script_text


def test_reports_display_driver_events(script_text):
    # Event 4101 = display driver stopped responding and recovered.
    assert "4101" in script_text
    assert "Win32_VideoController" in script_text


def test_cmd_launcher_is_ascii_and_elevates():
    data = CMD.read_bytes()
    data.decode("ascii")  # cmd.exe handles non-ASCII poorly
    text = data.decode("ascii")
    assert "fix-sleep-wake.ps1" in text
    assert "RunAs" in text
    assert "ExecutionPolicy Bypass" in text
