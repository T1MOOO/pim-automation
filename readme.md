# PIM Group Activation Script

Automates Privileged Identity Management (PIM) group activation across multiple Entra tenants using browser automation.

---

## Requirements

- Windows machine
- Python 3.x — download from https://www.python.org/downloads/
- Access to the tenants you want to activate roles in

---

## Installation

### 1. Install Playwright

Open PowerShell and run:

```powershell
pip install playwright --user
python -m playwright install chromium
```

### 2. Download the files

Place the following two files in the same folder (e.g. `C:\Users\yourname\pim-activation\`):

- `pim_activation.py`
- `config.ini`

---

## Configuration

Open `config.ini` in a text editor and fill in your details.

### Global settings

```ini
[settings]
justification = MSSP
session_file = pim_session.json
```

- `justification` — the reason text submitted when activating a role
- `session_file` — filename for the saved login session (no need to change this)

### Tenants

Each tenant has its own section. Fill in the `name`, `tenant_id`, and `groups` for each one:

```ini
[tenant_a]
name = Contoso
tenant_id = xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
groups = Sentinel_SOC_Analyst, Defender_SOC_Analyst
```

- `name` — a friendly label shown in the console output
- `tenant_id` — found in Entra admin center under Entra ID > Overview
- `groups` — comma separated list of PIM eligible group names to activate

You can add or remove tenants by adding or removing `[tenant_x]` sections. The section name just needs to start with `tenant_`.

---

## Usage

Run the script from PowerShell:

```powershell
python pim_activation.py
```

**First run:** A browser window will open and prompt you to log in to Entra. Log in and approve the MFA push notification. The session will be saved automatically so you won't need to log in again next time.

**Subsequent runs:** The saved session is loaded automatically and the script proceeds without any login prompt (unless the session has expired, in which case it will prompt you to log in again).

The script will then go through each tenant in order, navigate to PIM, and activate the configured groups automatically.

---

## File overview

| File | Description |
|---|---|
| `pim_activation.py` | Main script |
| `config.ini` | Tenant and group configuration |
| `pim_session.json` | Saved login session (auto-generated on first run) |

---

## Troubleshooting

**Session expired** — delete `pim_session.json` and run the script again to trigger a fresh login.

**Group not found** — make sure the group name in `config.ini` exactly matches the display name shown in PIM, including underscores and capitalisation.

**Script fails on a tenant** — check that you have eligible PIM assignments in that tenant. The script will print `Not eligible or not found` and move on if a group isn't assigned to you.
