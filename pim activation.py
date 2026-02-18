import asyncio
import os
import configparser
from playwright.async_api import async_playwright

# ----------------------------------------
# Load config
# ----------------------------------------
config = configparser.ConfigParser()
config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.ini")

if not os.path.exists(config_path):
    print(f"ERROR: config.ini not found at {config_path}")
    exit(1)

config.read(config_path)

# Read global settings
JUSTIFICATION = config.get("settings", "justification", fallback="MSSP")
SESSION_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    config.get("settings", "session_file", fallback="pim_session.json")
)

# Read tenants (any section that starts with "tenant_")
TENANTS = []
for section in config.sections():
    if section.startswith("tenant_"):
        groups_raw = config.get(section, "groups", fallback="")
        groups = [g.strip() for g in groups_raw.split(",") if g.strip()]
        TENANTS.append({
            "name": config.get(section, "name"),
            "tenant_id": config.get(section, "tenant_id"),
            "groups": groups
        })

if not TENANTS:
    print("ERROR: No tenants found in config.ini")
    exit(1)

print(f"Loaded {len(TENANTS)} tenant(s) from config.ini")


# ----------------------------------------
# Activate a single group
# ----------------------------------------
async def activate_group(page, group_name):
    print(f"    Activating {group_name}...")
    try:
        await page.wait_for_timeout(2000)

        # Click Activate in the row
        await page.get_by_role("row", name=group_name).get_by_role("button", name="Activate").click()

        # Wait for dialog to fully open
        await page.wait_for_timeout(5000)

        # Target the Reason field (index 3)
        inputs = await page.get_by_role("textbox").all()
        reason_field = inputs[3]
        await reason_field.click()
        await page.wait_for_timeout(500)
        await reason_field.fill(JUSTIFICATION)
        await page.wait_for_timeout(1000)

        # Click the final Activate button in the dialog
        await page.get_by_role("button", name="Activate").last.click()
        await page.wait_for_timeout(3000)

        print(f"    Activated: {group_name}")
    except Exception as e:
        print(f"    Failed: {group_name} - {e}")


# ----------------------------------------
# Process a single tenant
# ----------------------------------------
async def process_tenant(page, tenant):
    print(f"\nProcessing {tenant['name']}...")

    url = f"https://entra.microsoft.com/{tenant['tenant_id']}/#view/Microsoft_Azure_PIMCommon/ActivationMenuBlade/~/aadgroup"
    await page.goto(url, wait_until="networkidle", timeout=30000)
    await page.wait_for_timeout(5000)

    print(f"  Reached PIM for {tenant['name']}")

    for group in tenant["groups"]:
        await activate_group(page, group)


# ----------------------------------------
# Main
# ----------------------------------------
async def main():
    async with async_playwright() as p:

        session_exists = os.path.exists(SESSION_FILE)
        browser = await p.chromium.launch(headless=False, slow_mo=500)

        if session_exists:
            print("Found saved session, loading...")
            context = await browser.new_context(storage_state=SESSION_FILE)
        else:
            print("No saved session found, starting fresh login...")
            context = await browser.new_context()

        page = await context.new_page()

        # Navigate to Entra and log in if needed
        await page.goto("https://entra.microsoft.com", wait_until="networkidle")

        if not session_exists or "login" in page.url or "microsoftonline" in page.url:
            print("Please log in and approve the MFA push notification...")
            await page.wait_for_function(
                "window.location.hostname === 'entra.microsoft.com'",
                timeout=120000
            )
            await page.wait_for_timeout(5000)
            print("Login detected, saving session...")
            await context.storage_state(path=SESSION_FILE)
            print(f"Session saved to {SESSION_FILE}")
        else:
            print("Already logged in via saved session, proceeding...")
            await page.wait_for_timeout(3000)

        # Process each tenant
        for tenant in TENANTS:
            await process_tenant(page, tenant)

        print("\nAll tenants processed.")
        await asyncio.sleep(3)
        await browser.close()


asyncio.run(main())