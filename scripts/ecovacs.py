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
"""
import aiohttp
import asyncio
import sys
import json

from deebot_client.api_client import ApiClient
from deebot_client.authentication import Authenticator, create_rest_config
from deebot_client.mqtt_client import MqttClient, create_mqtt_config
from deebot_client.device import Device
from deebot_client.util import md5
from deebot_client.commands.json.clean import Clean, CleanV2, CleanAction, GetCleanInfoV2
from deebot_client.commands.json.charge import Charge
from deebot_client.commands.json.battery import GetBattery
from deebot_client.commands.json.charge_state import GetChargeState
from deebot_client.commands.json.play_sound import PlaySound
from deebot_client.events import BatteryEvent, StateEvent
from deebot_client.models import State

ACCOUNT  = "yehudamiz007@gmail.com"
PASSWORD = md5("Ecovacs123456@")
COUNTRY  = "IL"
DEVICE_ID = md5("openclaw-ecovacs")

STATE_LABELS = {
    State.CLEANING:  "Cleaning",
    State.RETURNING: "Returning to dock",
    State.DOCKED:    "Docked / Charging",
    State.ERROR:     "Error",
    State.IDLE:      "Idle",
    State.PAUSED:    "Paused",
}

async def run_command(action):
    async with aiohttp.ClientSession() as session:
        rest_config = create_rest_config(session, device_id=DEVICE_ID, alpha_2_country=COUNTRY)
        auth = Authenticator(rest_config, ACCOUNT, PASSWORD)
        api  = ApiClient(auth)

        devices = await api.get_devices()
        device_list = devices.mqtt if hasattr(devices, 'mqtt') else list(devices)
        if not device_list:
            print(json.dumps({"error": "No devices found"}))
            return

        device_info = device_list[0]
        bot = Device(device_info, auth)

        results = {}
        battery_done = asyncio.Event()
        state_done   = asyncio.Event()

        async def on_battery(event: BatteryEvent):
            results['battery'] = event.value
            battery_done.set()

        async def on_state(event: StateEvent):
            results['state'] = event.state
            state_done.set()

        bot.events.subscribe(BatteryEvent, on_battery)
        bot.events.subscribe(StateEvent,   on_state)

        mqtt_config = create_mqtt_config(device_id=DEVICE_ID, country=COUNTRY)
        mqtt = MqttClient(mqtt_config, auth)
        await mqtt.connect()
        await mqtt.subscribe(bot)

        # Get current status
        await bot.execute_command(GetBattery())
        await bot.execute_command(GetChargeState())
        await bot.execute_command(GetCleanInfoV2())

        try:
            await asyncio.wait_for(battery_done.wait(), timeout=10)
        except asyncio.TimeoutError:
            pass
        try:
            await asyncio.wait_for(state_done.wait(), timeout=10)
        except asyncio.TimeoutError:
            pass

        action_msg  = None
        action_ok   = True

        if action == 'clean':
            result = await bot.execute_command(CleanV2(CleanAction.START))
            action_msg = "Clean started"
            await asyncio.sleep(2)

        elif action == 'stop':
            result = await bot.execute_command(CleanV2(CleanAction.STOP))
            action_msg = "Stopped"
            await asyncio.sleep(2)

        elif action == 'pause':
            result = await bot.execute_command(CleanV2(CleanAction.PAUSE))
            action_msg = "Paused"
            await asyncio.sleep(2)

        elif action == 'resume':
            result = await bot.execute_command(CleanV2(CleanAction.RESUME))
            action_msg = "Resumed"
            await asyncio.sleep(2)

        elif action == 'charge':
            result = await bot.execute_command(Charge())
            action_msg = "Returning to dock"
            await asyncio.sleep(2)

        elif action == 'sound':
            result = await bot.execute_command(PlaySound())
            action_msg = "Playing sound"
            await asyncio.sleep(2)

        await mqtt.disconnect()

        state_raw = results.get('state')
        output = {
            "robot":   device_info.api.get('deviceName', 'DEEBOT X8 PRO OMNI'),
            "battery": f"{results.get('battery', '?')}%",
            "state":   STATE_LABELS.get(state_raw, str(state_raw) if state_raw else "Unknown"),
        }
        if action_msg:
            output["action"] = action_msg

        print(json.dumps(output, indent=2))

VALID = ['status', 'clean', 'stop', 'pause', 'resume', 'charge', 'sound']

if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'status'
    if cmd not in VALID:
        print(json.dumps({"error": f"Unknown command: {cmd}", "available": VALID}))
        sys.exit(1)
    asyncio.run(run_command(cmd))
