"""
ecovacs.py - DEEBOT X8 PRO OMNI controller
Usage:
  python ecovacs.py status
  python ecovacs.py clean
  python ecovacs.py stop
  python ecovacs.py pause
  python ecovacs.py resume
  python ecovacs.py charge
  python ecovacs.py sound
  python ecovacs.py fan_speed quiet|normal|max|max_plus
  python ecovacs.py water low|medium|high|ultrahigh
  python ecovacs.py mode vacuum|mop|vacuum_mop|mop_after_vacuum
  python ecovacs.py volume 0-10
  python ecovacs.py count 1|2
"""
import aiohttp, asyncio, sys, json

from deebot_client.api_client import ApiClient
from deebot_client.authentication import Authenticator, create_rest_config
from deebot_client.mqtt_client import MqttClient, create_mqtt_config
from deebot_client.device import Device
from deebot_client.util import md5
from deebot_client.commands.json.clean import CleanV2, CleanAction
from deebot_client.commands.json.clean import GetCleanInfoV2
from deebot_client.commands.json.charge import Charge
from deebot_client.commands.json.battery import GetBattery
from deebot_client.commands.json.charge_state import GetChargeState
from deebot_client.commands.json.play_sound import PlaySound
from deebot_client.commands.json.fan_speed import SetFanSpeed, GetFanSpeed, FanSpeedLevel
from deebot_client.commands.json.water_info import SetWaterInfo, GetWaterInfo, WaterAmount
from deebot_client.commands.json.work_mode import SetWorkMode, GetWorkMode, WorkMode
from deebot_client.commands.json.volume import SetVolume, GetVolume
from deebot_client.commands.json.clean_count import SetCleanCount, GetCleanCount
from deebot_client.events import BatteryEvent, StateEvent, FanSpeedEvent, WaterInfoEvent, WorkModeEvent, VolumeEvent, CleanCountEvent
from deebot_client.models import State

ACCOUNT   = "yehudamiz007@gmail.com"
PASSWORD  = md5("Ecovacs123456@")
COUNTRY   = "IL"
DEVICE_ID = md5("openclaw-ecovacs")

STATE_LABELS = {
    State.CLEANING:  "Cleaning",
    State.RETURNING: "Returning to dock",
    State.DOCKED:    "Docked",
    State.ERROR:     "Error",
    State.IDLE:      "Idle",
    State.PAUSED:    "Paused",
}

FAN_MAP = {
    'quiet': FanSpeedLevel.QUIET,
    'normal': FanSpeedLevel.NORMAL,
    'max': FanSpeedLevel.MAX,
    'max_plus': FanSpeedLevel.MAX_PLUS,
}
WATER_MAP = {
    'low': WaterAmount.LOW,
    'medium': WaterAmount.MEDIUM,
    'high': WaterAmount.HIGH,
    'ultrahigh': WaterAmount.ULTRAHIGH,
}
MODE_MAP = {
    'vacuum_mop': WorkMode.VACUUM_AND_MOP,
    'vacuum': WorkMode.VACUUM,
    'mop': WorkMode.MOP,
    'mop_after_vacuum': WorkMode.MOP_AFTER_VACUUM,
}

async def run_command(action, arg=None):
    async with aiohttp.ClientSession() as session:
        rest_config = create_rest_config(session, device_id=DEVICE_ID, alpha_2_country=COUNTRY)
        auth = Authenticator(rest_config, ACCOUNT, PASSWORD)
        api  = ApiClient(auth)

        devices = await api.get_devices()
        device_list = devices.mqtt if hasattr(devices, 'mqtt') else list(devices)
        if not device_list:
            print(json.dumps({"error": "No devices found"})); return

        bot = Device(device_list[0], auth)
        results = {}
        events_done = {k: asyncio.Event() for k in ['battery','state','fan','water','mode','volume','count']}

        def sub(ev_class, key, transform=None):
            async def handler(event):
                results[key] = transform(event) if transform else event
                events_done[key].set()
            bot.events.subscribe(ev_class, handler)

        sub(BatteryEvent,   'battery', lambda e: e.value)
        sub(StateEvent,     'state',   lambda e: e.state)
        sub(FanSpeedEvent,  'fan',     lambda e: e.speed.name)
        sub(WaterInfoEvent, 'water',   lambda e: e.amount.name)
        sub(WorkModeEvent,  'mode',    lambda e: e.mode.name)
        sub(VolumeEvent,    'volume',  lambda e: e.volume)
        sub(CleanCountEvent,'count',   lambda e: e.count)

        mqtt_config = create_mqtt_config(device_id=DEVICE_ID, country=COUNTRY)
        mqtt = MqttClient(mqtt_config, auth)
        await mqtt.connect()
        await mqtt.subscribe(bot)

        # Fetch status
        for cmd in [GetBattery(), GetChargeState(), GetCleanInfoV2(),
                    GetFanSpeed(), GetWaterInfo(), GetWorkMode(), GetVolume(), GetCleanCount()]:
            await bot.execute_command(cmd)

        # Wait for battery + state (essential)
        for key in ['battery', 'state']:
            try: await asyncio.wait_for(events_done[key].wait(), timeout=10)
            except asyncio.TimeoutError: pass

        # Wait briefly for optional fields
        await asyncio.sleep(2)

        action_msg = None

        if action == 'clean':
            await bot.execute_command(CleanV2(CleanAction.START)); action_msg = "Clean started"; await asyncio.sleep(2)
        elif action == 'stop':
            await bot.execute_command(CleanV2(CleanAction.STOP));  action_msg = "Stopped";       await asyncio.sleep(2)
        elif action == 'pause':
            await bot.execute_command(CleanV2(CleanAction.PAUSE)); action_msg = "Paused";        await asyncio.sleep(2)
        elif action == 'resume':
            await bot.execute_command(CleanV2(CleanAction.RESUME));action_msg = "Resumed";       await asyncio.sleep(2)
        elif action == 'charge':
            await bot.execute_command(Charge());                   action_msg = "Returning to dock"; await asyncio.sleep(2)
        elif action == 'sound':
            await bot.execute_command(PlaySound());                action_msg = "Playing sound"; await asyncio.sleep(2)
        elif action == 'fan_speed':
            level = FAN_MAP.get((arg or '').lower())
            if level:
                await bot.execute_command(SetFanSpeed(level)); action_msg = f"Fan speed: {arg}"; await asyncio.sleep(2)
            else:
                action_msg = f"Unknown fan level: {arg}"
        elif action == 'water':
            amount = WATER_MAP.get((arg or '').lower())
            if amount:
                await bot.execute_command(SetWaterInfo(amount)); action_msg = f"Water: {arg}"; await asyncio.sleep(2)
            else:
                action_msg = f"Unknown water level: {arg}"
        elif action == 'mode':
            mode = MODE_MAP.get((arg or '').lower())
            if mode:
                await bot.execute_command(SetWorkMode(mode)); action_msg = f"Mode: {arg}"; await asyncio.sleep(2)
            else:
                action_msg = f"Unknown mode: {arg}"
        elif action == 'volume':
            try:
                vol = int(arg)
                await bot.execute_command(SetVolume(vol)); action_msg = f"Volume: {vol}"; await asyncio.sleep(2)
            except: action_msg = "Invalid volume"
        elif action == 'count':
            try:
                cnt = int(arg)
                await bot.execute_command(SetCleanCount(cnt)); action_msg = f"Clean count: {cnt}"; await asyncio.sleep(2)
            except: action_msg = "Invalid count"

        await mqtt.disconnect()

        state_raw = results.get('state')
        output = {
            "robot":   "DEEBOT X8 PRO OMNI",
            "battery": f"{results.get('battery', '?')}%",
            "state":   STATE_LABELS.get(state_raw, str(state_raw) if state_raw else "Unknown"),
            "fan_speed": results.get('fan', '?'),
            "water":     results.get('water', '?'),
            "mode":      results.get('mode', '?'),
            "volume":    results.get('volume', '?'),
            "clean_count": results.get('count', '?'),
        }
        if action_msg:
            output["action"] = action_msg
        print(json.dumps(output, indent=2))

VALID = ['status','clean','stop','pause','resume','charge','sound','fan_speed','water','mode','volume','count']

if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'status'
    arg = sys.argv[2] if len(sys.argv) > 2 else None
    if cmd not in VALID:
        print(json.dumps({"error": f"Unknown command: {cmd}", "available": VALID})); sys.exit(1)
    asyncio.run(run_command(cmd, arg))
