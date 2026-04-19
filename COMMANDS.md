# Voice Commands Reference

All commands are spoken after invoking Sky Control:
> "Hey Google, ask Sky Control to **[command]**"

Or open a session first:
> "Hey Google, talk to Sky Control" → then just say the command

---

## Targeting a specific Sky box

Append a room name to any command. If you only have one Sky box, you can omit it.

| Pattern | Example |
|---|---|
| `[command]` | *"pause"* |
| `[command] in the [room]` | *"pause in the living room"* |
| `[command] on the [room] sky` | *"channel up on the bedroom sky"* |
| `[command] the [room] sky box` | *"turn off the kitchen sky box"* |

---

## Playback

| Say this | Synonyms | What happens |
|---|---|---|
| **play** | resume, unpause, start playing | Resume playback |
| **pause** | freeze, hold | Pause playback |
| **stop** | halt | Stop playback |
| **record** | start recording | Record the current programme |
| **fast forward** | skip forward, ff | Fast forward |
| **rewind** | skip back | Rewind |

### Examples
```
"Hey Google, ask Sky Control to play"
"Hey Google, ask Sky Control to pause in the bedroom"
"Hey Google, ask Sky Control to fast forward in the living room"
"Hey Google, ask Sky Control to rewind"
"Hey Google, ask Sky Control to record in the kitchen"
```

---

## Channels

| Say this | Synonyms | What happens |
|---|---|---|
| **channel up** | next channel, channel plus | Go up one channel |
| **channel down** | previous channel, last channel, channel minus | Go down one channel |

### Examples
```
"Hey Google, ask Sky Control to channel up"
"Hey Google, ask Sky Control to next channel in the living room"
"Hey Google, ask Sky Control to channel down in the bedroom"
```

---

## Navigation

| Say this | Synonyms | What happens |
|---|---|---|
| **home** | sky home, go home, main menu | Go to Sky home screen |
| **guide** | tv guide, open the guide | Open the TV guide |
| **back** | go back | Press the back button |
| **up** | | D-pad up |
| **down** | | D-pad down |
| **left** | | D-pad left |
| **right** | | D-pad right |
| **select** | ok | Press OK/select |

### Examples
```
"Hey Google, ask Sky Control to guide"
"Hey Google, ask Sky Control to home in the bedroom"
"Hey Google, ask Sky Control to go back"
```

---

## Power

> **Note:** Sky Q doesn't have separate on/off states over the network — the power command toggles standby. If the box is on, it goes to standby. If in standby, it wakes up.

| Say this | Synonyms | What happens |
|---|---|---|
| **turn on** | switch on, wake up, power on | Toggle power (wake from standby) |
| **turn off** | switch off, power off | Toggle power (go to standby) |
| **standby** | | Toggle power |

### Examples
```
"Hey Google, ask Sky Control to turn on the living room sky"
"Hey Google, ask Sky Control to turn off the bedroom sky"
"Hey Google, ask Sky Control to standby"
```

---

## Colour buttons

| Say this | What happens |
|---|---|
| **red** | Press red button |
| **green** | Press green button |
| **yellow** | Press yellow button |
| **blue** | Press blue button |

### Examples
```
"Hey Google, ask Sky Control to red"
"Hey Google, ask Sky Control to blue in the living room"
```

---

## Other

| Say this | What happens |
|---|---|
| **search** | Open Sky search |
| **interactive** | Open interactive services |
| **box office** | Open Sky Box Office |
| **sky** | Press the Sky button |
| **services** | Open services |
| **help** | Open help |
| **dismiss** | Dismiss/close overlay |

---

## Utility commands

These are handled by Sky Control directly, without touching the Sky box.

| Say this | Response |
|---|---|
| *"what sky boxes do you know about"* | Lists all configured boxes |
| *"list my sky boxes"* | Lists all configured boxes |
| *"help"* (as a session opener) | Explains available commands |

---

## Adding custom room names

If your rooms aren't matched, edit `actions/custom/types/SkyDevice.yaml` and add synonyms:

```yaml
  snug:
    synonyms:
      - snug
      - small room
      - kids room
```

Then redeploy the Action (see README).

---

## Configuring boxes

Boxes are configured via the `SKY_DEVICES` environment variable on your server:

```
SKY_DEVICES=living_room:192.168.1.100,bedroom:192.168.1.101,kitchen:192.168.1.102
```

The name before `:` is what you say to Google — underscores become spaces, so `living_room` is matched by *"living room"*, *"lounge"*, *"front room"* etc.

Find your Sky Q box IP: **Sky Q remote → Settings → Network → Advanced Settings → IP address**

---

## How Google translates your voice into a command

```
You speak ──► Google Home mic
                   │
                   ▼
          Google speech-to-text
          (audio → text, done in Google's cloud)
                   │
                   ▼
          Google Actions NLU
          (matches text against training phrases in actions/custom/intents/
           extracts SkyCommand="pause" and SkyDevice="bedroom")
                   │
                   ▼
          POST /webhook on your Mac mini
          { "intent": { "params": {
              "SkyCommand": { "resolved": "pause" },
              "SkyDevice":  { "resolved": "bedroom" }
          }}}
                   │
                   ▼
          pyskyq sends TCP packet to Sky Q box (port 49160)
                   │
                   ▼
          Google speaks the response back through your Google Home
```

**Google handles 100% of the voice recognition and language understanding.** Your server just receives a clean JSON object with the resolved command and device — no audio processing on your end.
