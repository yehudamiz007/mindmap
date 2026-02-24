---
name: ecovacs
description: >
  DEEBOT X8 PRO OMNI robot vacuum controller. Use when the user asks to start
  cleaning, stop, pause, resume, send to dock/charge, check vacuum status,
  battery level, or play a sound on the robot. Keywords: vacuum, robot,
  DEEBOT, שואב, רובוט, נקה, תפסיק, עגינה.
---

# ECOVACS DEEBOT X8 PRO OMNI Skill

## Robot Info
- **Model:** DEEBOT X8 PRO OMNI
- **Account:** yehudamiz007@gmail.com
- **Script:** `C:\Users\YEHUDA\.openclaw\workspace\scripts\ecovacs.py`
- **Python:** `C:\Users\YEHUDA\AppData\Local\Programs\Python\Python311\python.exe`

## Commands

Run all commands with:
```
exec: C:\Users\YEHUDA\AppData\Local\Programs\Python\Python311\python.exe C:\Users\YEHUDA\.openclaw\workspace\scripts\ecovacs.py <command>
```

| Command | What it does |
|---------|-------------|
| `status` | Battery level + current state |
| `clean`  | Start full auto clean |
| `stop`   | Stop cleaning |
| `pause`  | Pause cleaning |
| `resume` | Resume after pause |
| `charge` | Return to dock |
| `sound`  | Play sound on robot |

## Response format (JSON stdout)
```json
{
  "robot": "DEEBOT X8 PRO OMNI",
  "battery": "99%",
  "state": "Docked / Charging",
  "action": "Clean started"  // only when action was performed
}
```

## State values
- `Docked / Charging` - at dock
- `Cleaning` - actively cleaning
- `Returning to dock` - going back
- `Paused` - paused mid-clean
- `Idle` - idle, not cleaning
- `Error` - something went wrong

## Behavior

1. **Always run the command first**, then parse the JSON output
2. **Ignore stderr lines** - paho-mqtt cleanup warnings are noise, not errors
3. **Report back** in the user's language (Hebrew if they wrote Hebrew)
4. If state is already correct (e.g. user says "clean" but already cleaning), mention it

## Example interactions

**"תתחיל לנקות"** →
```
exec: python ecovacs.py clean
```
Reply: "מתחיל לנקות! 🧹 סוללה 99%"

**"מה הסטטוס של השואב?"** →
```
exec: python ecovacs.py status
```
Reply: "השואב עגון וטוען ⚡ סוללה 100%"

**"תחזור לעגינה"** →
```
exec: python ecovacs.py charge
```
Reply: "חוזר לעגינה 🏠"

**"תנגן צליל"** →
```
exec: python ecovacs.py sound
```
Reply: "מנגן צליל 🔊"

## Notes
- Script takes ~15 seconds (MQTT connection + command + disconnect)
- `getCleanInfo` errors in stderr are harmless - X8 uses V2 protocol
- Battery is polled fresh each time
