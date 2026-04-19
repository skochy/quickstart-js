# Mac Mini Setup — Sky Q Voice Control Backend

These are exact steps to host the webhook server on a Mac Mini connected to your home Wi-Fi.
The Mac Mini must be on the **same network** as your Sky Q boxes.

---

## What you'll install

- **Python 3.12** — runs the webhook server
- **cloudflared** — creates a secure tunnel so Google can reach your local server
- **launchd service** — keeps the server running automatically on boot

---

## Step 1 — Install Homebrew (if not already installed)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

After it finishes, follow any instructions it prints about adding Homebrew to your PATH.
Verify it works:

```bash
brew --version
```

---

## Step 2 — Install Python 3.12 and cloudflared

```bash
brew install python@3.12 cloudflare/cloudflare/cloudflared
```

Verify:

```bash
python3.12 --version
cloudflared --version
```

---

## Step 3 — Clone the repo

```bash
mkdir -p ~/skyq-voice && cd ~/skyq-voice
git clone https://github.com/skochy/quickstart-js.git .
```

Or if you already have it cloned:

```bash
cd ~/skyq-voice
git pull origin main
```

---

## Step 4 — Find your Sky Q box IP addresses

On each Sky Q remote:
> **Home → Settings → Network → Advanced Settings**

Note down the IP address for each box (e.g. `192.168.1.100`).

---

## Step 5 — Create the environment file

```bash
cp .env.example .env
nano .env
```

Edit the `SKY_DEVICES` line with your actual box IPs and room names:

```env
SKY_DEVICES=living_room:192.168.1.100,bedroom:192.168.1.101

LOG_LEVEL=INFO
```

Names must match what you'll say to Google Home. Use underscores for spaces.
Save: `Ctrl+O` then `Enter`, then `Ctrl+X`.

---

## Step 6 — Create Python virtual environment and install dependencies

```bash
cd ~/skyq-voice
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate
```

---

## Step 7 — Test the server runs

```bash
cd ~/skyq-voice
source .venv/bin/activate
export $(grep -v '^#' .env | xargs)
uvicorn src.app:app --host 0.0.0.0 --port 8000
```

You should see:

```
INFO:     Sky Q Voice Control starting. Registered devices: {'living room': '192.168.1.100', ...}
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Test it: open a new Terminal tab and run:

```bash
curl http://localhost:8000/health
```

You should get back something like:
```json
{"status":"ok","devices":{"living room":"192.168.1.100","bedroom":"192.168.1.101"}}
```

Press `Ctrl+C` to stop the test server.

---

## Step 8 — Install as a permanent background service (launchd)

This makes the server start automatically on boot and restart if it crashes.

```bash
cat > ~/Library/LaunchAgents/com.skyq.voicecontrol.plist << 'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.skyq.voicecontrol</string>

  <key>ProgramArguments</key>
  <array>
    <string>/Users/YOURUSERNAME/skyq-voice/.venv/bin/uvicorn</string>
    <string>src.app:app</string>
    <string>--host</string>
    <string>0.0.0.0</string>
    <string>--port</string>
    <string>8000</string>
  </array>

  <key>WorkingDirectory</key>
  <string>/Users/YOURUSERNAME/skyq-voice</string>

  <key>EnvironmentVariables</key>
  <dict>
    <key>SKY_DEVICES</key>
    <string>living_room:192.168.1.100,bedroom:192.168.1.101</string>
    <key>LOG_LEVEL</key>
    <string>INFO</string>
  </dict>

  <key>StandardOutPath</key>
  <string>/Users/YOURUSERNAME/skyq-voice/logs/server.log</string>
  <key>StandardErrorPath</key>
  <string>/Users/YOURUSERNAME/skyq-voice/logs/server.log</string>

  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
</dict>
</plist>
PLIST
```

**Replace `YOURUSERNAME` with your actual macOS username** (run `whoami` to check).
**Replace the `SKY_DEVICES` value** with your actual boxes.

Create the logs directory and load the service:

```bash
mkdir -p ~/skyq-voice/logs
launchctl load ~/Library/LaunchAgents/com.skyq.voicecontrol.plist
```

Check it's running:

```bash
launchctl list | grep skyq
curl http://localhost:8000/health
```

View logs:

```bash
tail -f ~/skyq-voice/logs/server.log
```

---

## Step 9 — Set up Cloudflare Tunnel

This creates a permanent, free HTTPS URL so Google can reach your server.

### 9a — Create a Cloudflare account and tunnel

1. Go to [cloudflare.com](https://cloudflare.com) and create a free account.
2. Go to **Zero Trust → Networks → Tunnels → Create a tunnel**.
3. Name it **skyq-voice**, click **Save**.
4. Choose **Cloudflared**, then copy the tunnel token shown on screen (long string starting with `eyJ...`).

### 9b — Configure the tunnel on the Mac Mini

```bash
cloudflared service install <PASTE YOUR TOKEN HERE>
```

This installs cloudflared as a system service that starts on boot.

Then in the Cloudflare dashboard, add a **Public Hostname**:
- **Subdomain**: `skyq` (or whatever you like)
- **Domain**: your domain (or use Cloudflare's free `*.trycloudflare.com` — see below)
- **Service**: `http://localhost:8000`

Your webhook URL will be `https://skyq.yourdomain.com/webhook`.

### 9b (alternative) — Quick tunnel without a domain

If you don't have a domain, use a temporary tunnel for testing:

```bash
cloudflared tunnel --url http://localhost:8000
```

It prints a URL like `https://random-words.trycloudflare.com` — use that as your webhook URL.
Note: this URL changes every time you restart cloudflared, so it's only for testing.

---

## Step 10 — Set up the Google Actions project

This is a one-time step on any machine (not necessarily the Mac Mini).

### Install the gactions CLI

```bash
brew install --cask gactions
```

Or download manually from [developers.google.com/assistant/actionssdk/gactions](https://developers.google.com/assistant/actionssdk/gactions).

### Create the project

1. Go to [console.actions.google.com](https://console.actions.google.com).
2. Click **New project** → name it **Sky Control** → select **Custom** → **Blank project**.
3. Copy the **Project ID** from the URL or Settings (e.g. `sky-control-123456`).

### Deploy the Action

```bash
cd ~/skyq-voice

# Log in to your Google account
gactions login

# Inject your public webhook URL
export WEBHOOK_URL=https://skyq.yourdomain.com
sed "s|\${{env.WEBHOOK_URL}}|$WEBHOOK_URL|g" \
  actions/webhooks/ActionsOnGoogleFulfillment.yaml > /tmp/fulfillment.yaml
cp /tmp/fulfillment.yaml actions/webhooks/ActionsOnGoogleFulfillment.yaml

# Push the action to Google
gactions push --project-id YOUR_PROJECT_ID --action-package actions/

# Deploy to test mode
gactions deploy preview --project-id YOUR_PROJECT_ID
```

### Link to your Google account

In the Actions console:
- Go to **Test** → **Simulator** → type `Talk to Sky Control`
- It should respond: *"Sky Control ready. What would you like to do?"*

On your Google Home devices, say:
> **"Hey Google, talk to Sky Control"**

---

## Service management cheatsheet

```bash
# Restart the webhook server
launchctl unload ~/Library/LaunchAgents/com.skyq.voicecontrol.plist
launchctl load   ~/Library/LaunchAgents/com.skyq.voicecontrol.plist

# Stop it
launchctl unload ~/Library/LaunchAgents/com.skyq.voicecontrol.plist

# View live logs
tail -f ~/skyq-voice/logs/server.log

# Test it's working
curl http://localhost:8000/health
curl http://localhost:8000/devices

# Update to latest code
cd ~/skyq-voice
git pull origin main
source .venv/bin/activate
pip install -r requirements.txt
deactivate
launchctl unload ~/Library/LaunchAgents/com.skyq.voicecontrol.plist
launchctl load   ~/Library/LaunchAgents/com.skyq.voicecontrol.plist
```

---

## Assign a static IP to the Mac Mini

To stop the Mac Mini's IP changing and breaking things:
- On your router, find the DHCP reservations / static lease section.
- Reserve the Mac Mini's current IP for its MAC address.

Or on macOS: **System Settings → Network → Wi-Fi → Details → TCP/IP → Configure IP: Manually**.

---

## Troubleshooting

**`curl http://localhost:8000/health` times out**
- Check the service is running: `launchctl list | grep skyq`
- Check logs: `tail -50 ~/skyq-voice/logs/server.log`

**"Failed to send command" in logs**
- The Mac Mini can't reach the Sky box. Test: `ping 192.168.1.100`
- Check Sky Q's IP hasn't changed — assign a static IP via your router.

**Google can't reach the webhook**
- Test: `curl https://skyq.yourdomain.com/health` from any machine.
- If the Cloudflare tunnel is down: `launchctl list | grep cloudflared`

**"I couldn't find a Sky box called ..."**
- Check `SKY_DEVICES` in the plist matches what you're saying.
- Call `curl http://localhost:8000/devices` to see what's registered.
