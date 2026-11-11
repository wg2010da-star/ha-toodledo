# Toodledo for Home Assistant

Experimental custom integration that exposes Toodledo tasks as a native Home Assistant To-do list.

## Features
- Read open and completed Toodledo tasks
- Create tasks from Home Assistant
- Edit titles, due dates and descriptions
- Mark tasks completed / reopen them
- Delete tasks
- OAuth 2.0 authorization using Home Assistant's built-in callback handler
- Automatic access-token refresh

## Install from the Home Assistant Marketplace
1. Open the Marketplace and add `https://github.com/wg2010da-star/ha-toodledo` as a custom repository, category **Integration**.
2. Install **Toodledo** and restart Home Assistant.
3. Open **Settings → Devices & services → Add integration → Toodledo**.

## Toodledo app setup
Register an API app at Toodledo. Its Redirect URI must exactly match the callback URI Home Assistant uses.

For the local address `http://homeassistant:8132`, this is normally:

```
http://homeassistant:8132/auth/external/callback
```

If Home Assistant displays a different redirect URI in the generated authorization link (for example when the My Home Assistant redirect is enabled), register that exact URI instead. Do not use `http://localhost` for a Home Assistant server running on another device.

Keep the Client Secret private. Enter it only in the Home Assistant setup form. The integration requests `basic tasks write` permissions.

## Notes
- The default polling interval is 15 minutes. It can be changed in the integration options (5–60 minutes).
- Toodledo API v3 access tokens expire after two hours; refresh tokens are renewed by Toodledo and saved by Home Assistant.
- This is an experimental release. It has not yet been tested against your account or hardware. Back up Home Assistant before testing.

## References
- [Toodledo API v3 authentication](https://api.toodledo.com/3/account/index.php)
- [Toodledo API v3 tasks](https://api.toodledo.com/3/tasks/index.php)
- [Home Assistant OAuth 2.0 integration documentation](https://developers.home-assistant.io/docs/core/integration/config_flow/#configuration-via-oauth2)
