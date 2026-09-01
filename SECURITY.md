# Security Policy

**Supported versions** | Only the latest release branch receives security patches.

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a vulnerability

Found a security issue? Please **do not open a public GitHub Issue**.

Email the report directly to the maintainer:

```
mitunmanav933@gmail.com
```

Include as much context as possible:
- Description of the vulnerability
- Steps to reproduce
- Affected file(s) and line number(s)
- Any suggested fix (optional)

Expected response time: **within 72 hours** on business days.

## What to expect after reporting

1. **Acknowledgement** — within 72 hours, you'll receive confirmation the report was received.
2. **Severity assessment** — I'll classify the issue (Critical / High / Medium / Low) and share the timeline for a fix.
3. **Fix & disclosure** — once the patch is ready, I'll credit you in the CHANGELOG (unless you prefer anonymity) and publish a fixed release.

## Out of scope

- Compiling zero-day exploits or weaponizing any vulnerability
- Denial-of-service attacks against the Play Store API or Google infrastructure
- Social engineering against Google Play Console support

## Scope

This plugin operates entirely in your local development environment and communicates with:
- Your device over `adb`
- Google's Play Store API (for publishing)
- Your local Gradle/SDK installation

No telemetry, no third-party analytics, no remote code execution.
