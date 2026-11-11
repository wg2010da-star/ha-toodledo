# Toodledo for Home Assistant

Experimental custom integration that exposes your Toodledo tasks as a native Home Assistant To-do list.

## Features
- Read open and completed Toodledo tasks
- Create tasks from Home Assistant
- Edit titles, due dates and descriptions
- Mark tasks completed / reopen them
- Delete tasks
- OAuth 2.0 access and automatic refresh-token renewal

## Install with HACS
1. Open **HACS → Integrations → ⋮ → Custom repositories**.
2. Add `https://github.com/wg2010da-star/ha-toodledo` with category **Integration**.
3. Find **Toodledo** in HACS and install it.
4. Restart Home Assistant.
5. Go to **Settings → Devices & services → Add integration → Toodledo**.

## Toodledo app setup
Register an API app at Toodledo and set its Redirect URI to exactly `http://localhost`.
Keep the Client Secret private. Enter it only in the Home Assistant setup form.

During setup, Home Assistant displays an authorization URL:
1. Open that URL in a browser and approve access.
2. Toodledo redirects to `http://localhost/?code=...&state=...`. The page itself may fail to load; that is okay if the address bar contains the query parameters.
3. Copy the **entire address** from the browser address bar and paste it into the next Home Assistant form.

If your browser does not show a `code` and `state` in the address bar, stop and report what happened; do not share your Client Secret.

## Notes
- The integration requests `basic tasks write` permissions.
- The default polling interval is 15 minutes. It can be changed in the integration options (5–60 minutes).
- Toodledo API v3 access tokens expire after two hours; refresh tokens are rotated by Toodledo and saved by Home Assistant.
- This is an initial experimental release. It has not yet been tested against your account or hardware. Back up Home Assistant before testing, and report issues in the repository.

## References
- [Toodledo API v3 authentication](https://api.toodledo.com/3/account/index.php)
- [Toodledo API v3 tasks](https://api.toodledo.com/3/tasks/index.php)
- [Home Assistant To-do entity developer docs](https://developers.home-assistant.io/docs/core/entity/todo/)
