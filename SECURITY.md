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

This repository contains research configuration, committed model artifacts, and
reproduction scripts. It is intended for scientific reproduction rather than
production deployment, and it is not hardened against untrusted input.

In particular, configuration files and model artifacts are loaded as trusted
inputs. Do not run this code against configuration or artifact files from an
untrusted source.
