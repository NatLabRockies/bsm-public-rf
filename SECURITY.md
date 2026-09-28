# Security Policy

## Reporting a vulnerability

Please do not report security vulnerabilities through public GitHub issues.

Report suspected vulnerabilities privately using GitHub's
[private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability)
on this repository, or by contacting the maintainers directly.

Please include:

- a description of the issue and its potential impact
- the steps required to reproduce it
- the affected version or commit

We will acknowledge receipt and provide an assessment of next steps.

## Scope

This repository contains a model loader and committed model artifacts. It is
intended for research use and is not hardened as an untrusted multi-tenant
prediction service.

Model artifacts and user-provided CSV files are loaded as trusted local inputs.
Do not use artifact files from an untrusted source.
