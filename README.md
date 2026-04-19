# Sky Q Voice Control via Google Home

Control your Sky Q set-top boxes with your voice using Google Home / Google Assistant and [pyskyq](https://github.com/bradwood/pyskyq).

```
"Hey Google, ask Sky Control to pause"
"Hey Google, ask Sky Control to channel up in the bedroom"
"Hey Google, ask Sky Control to turn off the living room Sky"
```

---

## Architecture

```
Google Home ──► Google Actions ──► Webhook (FastAPI) ──► pyskyq ──► Sky Q box (TCP)
                                        │
                                   Your local network
                              (Raspberry Pi / home server)
```

- **Google Actions** (Conversational Action) handles the voice interface and NLU.
- **FastAPI webhook** runs on your local network, receives intents, and sends remote-control commands.
- **pyskyq** communicates with Sky Q boxes over TCP port 49160 on your LAN.
- **Cloudflare Tunnel** (or ngrok) bridges the internet → your local server so Google can reach the webhook.

---

## Quick Start

### 1. Configure your Sky boxes

Copy `.env.example` to `.env` and set `SKY_DEVICES`:

```bash
cp .env.example .env
```

```env
# Format: name:ip,name:ip,...
# The name is what you say to Google Home ("in the bedroom")
SKY_DEVICES=living_room:192.168.1.100,bedroom:192.168.1.101
```

Find your Sky Q box IP addresses in your router's admin panel or Sky Q settings → Network.

### 2. Run the webhook server

**Option A — Docker Compose (recommended)**

```bash
docker compose up -d
```

To also start the Cloudflare Tunnel:

```bash
docker compose --profile tunnel up -d
```

**Option B — Locally (development)**

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
SKY_DEVICES=living_room:192.168.1.100 uvicorn src.app:app --reload
```

The server starts on `http://localhost:8000`.
Verify it works: `curl http://localhost:8000/health`

### 3. Expose the webhook to the internet

Google Actions requires a public HTTPS URL to call your webhook.

**Option A — Cloudflare Tunnel (free, recommended for production)**

1. Create a free [Cloudflare account](https://cloudflare.com).
2. Go to **Zero Trust → Network → Tunnels → Create a tunnel**.
3. Name it `skyq-voice`, then copy the tunnel token.
4. Set `CLOUDFLARE_TUNNEL_TOKEN=<your-token>` in `.env`.
5. Configure the tunnel to route `your-domain.com → http://skyq-voice:8000`.
6. Your webhook URL is `https://your-domain.com/webhook`.

**Option B — ngrok (quick testing)**

```bash
ngrok http 8000
# Note the https://xxxx.ngrok.io URL — use it as your webhook URL
```

### 4. Set up Google Actions

#### Prerequisites

```bash
npm install -g @google/gactions
gactions login
```

#### Create a project

1. Go to [console.actions.google.com](https://console.actions.google.com).
2. Click **New project**, name it **Sky Control**, choose **Custom**.
3. Note the **Project ID** (e.g. `sky-control-12345`).

#### Configure and deploy

```bash
# Inject your webhook URL
export WEBHOOK_URL=https://your-domain.com
sed -i "s|\${{env.WEBHOOK_URL}}|$WEBHOOK_URL|g" \
  actions/webhooks/ActionsOnGoogleFulfillment.yaml

# Push the Action
gactions push --project-id YOUR_PROJECT_ID --action-package actions/

# Deploy and test
gactions deploy preview --project-id YOUR_PROJECT_ID
```

#### Test with Google Home

1. In the Actions console, go to **Test → Simulator**.
2. Type: `Talk to Sky Control`
3. Then: `pause in the living room`

On your physical Google Home devices, say:
- **"Hey Google, talk to Sky Control"** then **"pause"**
- Or configure a **Google Home Routine** with the phrase *"Hey Google, pause Sky"* → action *"Talk to Sky Control and say pause"*

---

## Supported Voice Commands

| What you say | Sky Q action |
|---|---|
| pause | Pause playback |
| play / resume | Resume playback |
| stop | Stop playback |
| record | Start recording |
| fast forward / skip forward | Fast forward |
| rewind / skip back | Rewind |
| channel up / next channel | Channel up |
| channel down / previous channel | Channel down |
| guide / tv guide | Open TV guide |
| home / sky home | Go to Sky home |
| back / go back | Back |
| turn on / turn off / standby | Toggle power |
| red / green / yellow / blue | Colour buttons |
| search | Search |
| interactive | Interactive services |

Add a room after any command to target a specific box:
- *"pause in the living room"*
- *"channel up in the bedroom"*
- *"turn off the kitchen Sky"*

---

## GitHub Actions CI/CD

### What runs automatically

| Trigger | Workflow | What it does |
|---|---|---|
| Any push / PR | `ci.yml` | Run tests + lint |
| Push to `main` | `deploy.yml` | Build Docker image → push to GHCR → SSH deploy |
| Push to `main` (actions/ changed) | `deploy-actions.yml` | Push Google Actions project |

### Required GitHub Secrets

Set these in **Settings → Secrets and variables → Actions**:

| Secret | Description |
|---|---|
| `SKY_DEVICES` | Your Sky box IP map (e.g. `living_room:192.168.1.100`) |
| `SSH_HOST` | IP/hostname of your home server |
| `SSH_USER` | SSH username |
| `SSH_KEY` | SSH private key (generate with `ssh-keygen`) |
| `GOOGLE_ACTIONS_CREDENTIALS` | Google service account JSON for gactions CLI |
| `GOOGLE_ACTIONS_PROJECT_ID` | Your Google Actions project ID |
| `WEBHOOK_URL` | Public HTTPS URL of your webhook |

### Pull the Docker image on your server

```bash
echo $GITHUB_TOKEN | docker login ghcr.io -u YOUR_GITHUB_USER --password-stdin
docker pull ghcr.io/skochy/quickstart-js:main
```

Or use `docker compose pull` if you've copied `docker-compose.yml` to the server.

---

## Configuration Reference

### `SKY_DEVICES` format

```
name1:ip1,name2:ip2,name3:ip3
```

- Names are case-insensitive; underscores and hyphens are treated as spaces.
- Names should match what you say to Google Home (e.g. `living_room` → *"in the living room"*).

### Adding device synonyms to Google Actions

Edit `actions/custom/types/SkyDevice.yaml` to add your room names, then redeploy:

```yaml
  lounge:
    synonyms:
      - lounge
      - living room
      - front room
```

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/webhook` | Google Actions fulfillment |
| `GET` | `/health` | Health check + registered devices |
| `GET` | `/devices` | List configured Sky boxes |
| `GET` | `/commands` | List supported commands |

---

## Development

```bash
pip install -r requirements-dev.txt
pytest -v
ruff check src/ tests/
```

---

## Troubleshooting

**"Failed to send command to 192.168.x.x"**
- Ensure the Sky Q box is on and on the same network as the server.
- Verify the IP address: `ping 192.168.x.x`.
- Check port 49160 is reachable: `nc -zv 192.168.x.x 49160`.
- Some routers block internal traffic by device isolation — check your router settings.

**"I couldn't find a Sky box called ..."**
- Make sure `SKY_DEVICES` is set correctly and the name matches what you're saying.
- Check `/health` to see what devices are registered.

**Google Actions not reaching the webhook**
- Verify the tunnel is running: `curl https://your-domain.com/health`.
- Check the webhook URL in `actions/webhooks/ActionsOnGoogleFulfillment.yaml`.

**Personal vs published Action**
- This Action is deployed in **preview/test mode** — it works on devices linked to your Google account without publishing.
- To use it on all household devices, link each Google account to the Action project in the Actions console under **Deploy → Account linking**.
