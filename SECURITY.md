# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.6.x   | :white_check_mark: |
| 1.5.x   | :white_check_mark: |
| < 1.5   | :x:                |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability, please follow these steps:

### How to Report

1. **Do NOT** open a public GitHub issue for security vulnerabilities
2. Email the maintainers directly (or use GitHub's private vulnerability reporting if available)
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Any suggested fixes (optional)

### What to Expect

- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 7 days
- **Resolution Timeline**: Depends on severity, typically 30-90 days

### Severity Levels

| Level | Description | Response Time |
|-------|-------------|---------------|
| Critical | Remote code execution, data breach | 24-48 hours |
| High | Privilege escalation, sensitive data exposure | 7 days |
| Medium | Limited impact vulnerabilities | 30 days |
| Low | Minor issues, hardening suggestions | 90 days |

## Security Considerations

### Installation Safety

- Always verify you're installing from the official repository
- Review `install.sh` / `install.ps1` before running
- The installer only writes to:
  - `.claude/` in your project directory
  - `~/.wukong/` for global hooks
  - `~/.claude/settings.json` (with user confirmation)

### Data Handling

- Wukong stores context data in `~/.wukong/context/`
- Session data may contain sensitive information from your conversations
- The `.gitignore` excludes runtime data from version control

### Hooks Security

- PreCompact hooks execute Python scripts from `~/.wukong/hooks/`
- Only install hooks from trusted sources
- Review hook scripts before enabling them

### Known Security Features

- `jie.md` includes information disclosure security checks
- Path validation tests prevent accidental exposure of wrong directories
- Cross-platform path handling to avoid path traversal issues

## Security Best Practices

1. **Keep Updated**: Use the latest version for security fixes
2. **Review Before Install**: Check scripts before running
3. **Protect Sensitive Data**: Don't commit `.wukong/context/sessions/` to public repos
4. **Use Environment Variables**: For sensitive configuration, use environment variables instead of hardcoding

## Acknowledgments

We appreciate responsible disclosure and will acknowledge security researchers who report valid vulnerabilities (unless they prefer to remain anonymous).
