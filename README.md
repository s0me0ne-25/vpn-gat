## VPN Google Anti-Teleport (GAT)

### 0) Why?
Because fuck heuristic GeoIP, that's why. THY SHALL OBEY WHAT WHOIS PROPHECIED

### 1) ADJUST FIRST for country of your VPN service
- Dicts pre-shipped for Amsterdam and Paris
- If needed, use any top-grade LLM AI (Grok, Gemini, Claude etc.) to generate the national dict you need, then feel free to contribute it to project github.
- Enter your WAN IP to be cleaned up into the corresponding variable
- Measure the target city lat/lon rectangle using any online map and populate the corresponding config vars

### 2) Run either in cron, or in infinite loop with delay. Recommended intervals:
- 2-5m for cleaning already misteleported IP
- 10-15m for clean IP to prevent further teleportation

### 3) Credits
- Vibecoded in Grok 4 by `@s0me0ne-25`
- Non-Copyrighted: AI Work
- Creative Commons CC0, if above is not applicable in your jurisdiction

## Installation

1) Install Debian 13 onto a virtual machine:
  - choose LXDE desktop environment
  - name the default user `user`
  - enable LXDE autologin as `user`
  - install `chromium-browser`
  - install the means of accessing internet via the target WAN IP
2) Clone the repo and deploy its contents over the `/` filesystem

3) Adjust settings as said above
4) `systemctl enable vpngat && systemctl start vpngat`
5) First launches may pop up some captchas, keep solving until gone