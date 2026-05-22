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
