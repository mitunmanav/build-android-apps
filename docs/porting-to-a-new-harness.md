# Porting to a New Harness

Invariants (from inspiration/superpowers docs/porting-to-a-new-harness.md):
1. Skills name actions, not tools. Never edit skill bodies; add references/<harness>-tools.md.
2. Bootstrap is the entire integration. Without session-start injection the skills are inert.
3. Ship through the harness install mechanism. Never edit user home config.
4. Prove with live transcript: clean session + "make a habit tracker" triggers build-android-apps before code.
