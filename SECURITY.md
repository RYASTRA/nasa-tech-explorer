# Security Policy

## Scope

This project is a static website plus a scheduled GitHub Actions pipeline. It has no
runtime backend, stores no user data, and uses no API keys. The attack surface is the
Actions workflows, the published static site, and the data pipeline's handling of
untrusted API text (which is HTML-escaped at render time).

## Supported Versions

Only the latest state of `main` (and the site deployed from it) is supported.

## Reporting a Vulnerability

Please use GitHub's private vulnerability reporting on this repository
(Security → "Report a vulnerability"). You can expect an acknowledgement within a week.
Please do not open public issues for suspected vulnerabilities.
