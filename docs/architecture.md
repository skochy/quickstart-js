# Architecture & Data Flow

## The key concept

Your Mac Mini never opens any inbound ports and never "pushes" anything.
`cloudflared` starts on boot and opens a persistent **outbound** connection to
Cloudflare's edge servers. When Google later calls your webhook URL, Cloudflare
forwards the request back through that already-open tunnel — like a phone call
you placed that stays on hold until someone needs to talk to you.

---

## Architecture diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  GOOGLE CLOUD                                                               │
│                                                                             │
│  ┌──────────────────┐    audio     ┌───────────────────────────────────┐   │
│  │  Google Home     │ ──────────►  │  Google Assistant                 │   │
│  │  (your speaker)  │ ◄──────────  │  · Wake word detection            │   │
│  │  Living room /   │  TTS audio   │  · Speech-to-text                 │   │
│  │  Bedroom / etc.  │              │  · Natural language understanding  │   │
│  └──────────────────┘              │  · Slot filling                   │   │
│                                    │    SkyCommand = "pause"            │   │
│                                    │    SkyDevice  = "bedroom"          │   │
│                                    └─────────────┬─────────────────────┘   │
│                                                  │ POST /webhook            │
│                                                  │ (structured JSON,        │
│                                                  │  no audio)               │
└──────────────────────────────────────────────────┼─────────────────────────┘
                                                   │
                                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  CLOUDFLARE EDGE  (skyq.yourdomain.com)                                     │
│                                                                             │
│  Receives HTTPS request from Google.                                        │
│  Looks up the tunnel named "skyq-voice".                                   │
│  Forwards request through the persistent tunnel connection.                 │
└─────────────────────────┬───────────────────────────────────────────────────┘
                          │  Persistent outbound tunnel (QUIC / HTTP/2)
                          │  ◄── Mac Mini opened this connection on boot
                          │
┌─────────────────────────┼───────────────────────────────────────────────────┐
│  YOUR HOME NETWORK      │                                                   │
│                         ▼                                                   │
│          ┌──────────────────────────┐                                       │
│          │  Mac Mini                │                                       │
│          │                          │                                       │
│          │  ┌────────────────────┐  │                                       │
│          │  │  cloudflared       │  │  · Opened outbound tunnel on boot    │
│          │  │  (tunnel agent)    │  │  · Forwards traffic to localhost:8000 │
│          │  └────────┬───────────┘  │                                       │
│          │           │              │                                       │
│          │           ▼              │                                       │
│          │  ┌────────────────────┐  │                                       │
│          │  │  FastAPI server    │  │  · Parses intent JSON                │
│          │  │  (src/app.py)      │  │  · Resolves device name → IP        │
│          │  │  port 8000         │  │  · Returns spoken response           │
│          │  └────────┬───────────┘  │                                       │
│          │           │              │                                       │
│          │           ▼              │                                       │
│          │  ┌────────────────────┐  │                                       │
│          │  │  pyskyq            │  │  press_remote(ip, REMOTECOMMANDS.pause│
│          │  │  (sky_controller)  │  │  port 49160)                         │
│          │  └────────┬───────────┘  │                                       │
│          └───────────┼──────────────┘                                       │
│                      │  TCP  port 49160  (same LAN)                         │
│          ┌───────────┼──────────────────────────────┐                       │
│          │           ▼              ▼               │                       │
│          │  ┌──────────────┐  ┌──────────────┐     │                       │
│          │  │ Sky Q        │  │ Sky Q        │ ... │                       │
│          │  │ Living room  │  │ Bedroom      │     │                       │
│          │  │ 192.168.1.100│  │ 192.168.1.101│     │                       │
│          │  └──────────────┘  └──────────────┘     │                       │
│          └──────────────────────────────────────────┘                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Data flow — one voice command, step by step

```
  YOU                  GOOGLE HOME        GOOGLE CLOUD          CLOUDFLARE
   │                       │                   │                     │
   │  "Hey Google, ask     │                   │                     │
   │   Sky Control to      │                   │                     │
   │   pause in the        │                   │                     │
   │   bedroom"            │                   │                     │
   │──────────────────────►│                   │                     │
   │                       │  audio stream     │                     │
   │                       │──────────────────►│                     │
   │                       │                   │ speech-to-text      │
   │                       │                   │ ─────────────────   │
   │                       │                   │ "pause in the       │
   │                       │                   │  bedroom"           │
   │                       │                   │                     │
   │                       │                   │ NLU / slot filling  │
   │                       │                   │ ─────────────────   │
   │                       │                   │ intent: SkyControl  │
   │                       │                   │ SkyCommand: "pause" │
   │                       │                   │ SkyDevice: "bedroom"│
   │                       │                   │                     │
   │                       │                   │  POST /webhook      │
   │                       │                   │  (HTTPS)            │
   │                       │                   │────────────────────►│
   │                       │                   │                     │


  MAC MINI (FastAPI)    cloudflared          CLOUDFLARE           PYSKYQ
         │                   │                   │                   │
         │  ◄── persistent outbound tunnel ──────┤                   │
         │       (opened by cloudflared           │                   │
         │        when Mac Mini booted)           │                   │
         │                   │                   │                   │
         │◄──────────────────│◄──────────────────│                   │
         │  forwarded POST                        │                   │
         │  {                                     │                   │
         │    handler: "SkyControl"               │                   │
         │    params: {                           │                   │
         │      SkyCommand: "pause"               │                   │
         │      SkyDevice:  "bedroom"             │                   │
         │    }                                   │                   │
         │  }                                     │                   │
         │                                        │                   │
         │  resolve "bedroom"                     │                   │
         │  ─────────────────                     │                   │
         │  → 192.168.1.101                       │                   │
         │                                        │                   │
         │  press_remote(                         │                   │
         │    "192.168.1.101",                    │                   │
         │    REMOTECOMMANDS.pause,               │                   │
         │    49160                               │                   │
         │  )                                     │                   │
         │──────────────────────────────────────────────────────────►│
         │                                        │         TCP :49160│
         │                                        │          to Sky Q │
         │◄──────────────────────────────────────────────────────────│
         │  success                               │                   │
         │                                        │                   │
         │──────────────────►│────────────────────►                   │
         │  HTTP 200                              │                   │
         │  {                                     │                   │
         │    prompt: {                           │                   │
         │      speech: "Pausing on Bedroom."     │                   │
         │    }                                   │                   │
         │  }                                     │                   │


  YOU                  GOOGLE HOME        GOOGLE CLOUD          CLOUDFLARE
   │                       │                   │                     │
   │                       │                   │◄────────────────────│
   │                       │                   │  response forwarded │
   │                       │                   │  back to Assistant  │
   │                       │                   │                     │
   │                       │                   │ text-to-speech      │
   │                       │                   │ ─────────────────   │
   │                       │◄──────────────────│                     │
   │                       │  audio            │                     │
   │◄──────────────────────│                   │                     │
   │  "Pausing on          │                   │                     │
   │   Bedroom."           │                   │                     │
```

---

## Why your router needs no changes

```
                INTERNET
                    │
            ┌───────┴────────┐
            │   Your Router  │
            │                │
            │  No ports open │  ◄── nothing inbound allowed
            │  No forwarding │
            └───────┬────────┘
                    │  LAN
          ┌─────────┼──────────────────┐
          │         │                  │
          ▼         ▼                  ▼
     Mac Mini    Sky Q boxes       Other devices
     opens an    (192.168.x.x)
     OUTBOUND
     connection
     to Cloudflare
     on boot
          │
          └──────── outbound ──────────► Cloudflare edge
                    (like loading                │
                     a web page,                 │ Google calls
                     but it stays               │ this URL
                     connected)                  │
                         ◄───────────────────────┘
                         traffic flows back through
                         the connection the Mac Mini
                         already opened
```

The cloudflared agent works like a reverse proxy over a persistent outbound
WebSocket/QUIC connection. Because the Mac Mini initiated the connection
(outbound), your router treats it the same as you browsing a website —
no special firewall rules or port forwarding needed.

---

## How Google connects your voice to your Google Home

Google Home devices are permanently signed in to your Google account.
When you deploy the Action in **preview mode**, Google links it to your account.
Any Google Home device on that account can invoke it. Google's cloud does all
the routing — your local network is never involved in the voice recognition side.

```
Your Google account
        │
        ├── Google Home (living room)  ┐
        ├── Google Home (bedroom)      ├── all can invoke "Sky Control"
        ├── Google Home Mini (kitchen) ┘
        │
        └── Sky Control Action (preview mode)
                    │
                    └── Webhook: https://skyq.yourdomain.com/webhook
                                          │
                                     Cloudflare → Mac Mini
```
