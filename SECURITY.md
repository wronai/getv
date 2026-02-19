# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 0.1.x   | ✅ Supported       |
| < 0.1   | ❌ Unsupported     |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

### 📧 Email (Preferred)
- Send to: tom@sapletta.com
- Subject: `Security vulnerability in getv`
- Include as much detail as possible

### 🔒 Private Issue
- Create a private issue on GitHub
- Mark as "Security vulnerability"
- Limit access to maintainers only

### What to Include
- Type of vulnerability (XSS, injection, etc.)
- Steps to reproduce
- Potential impact
- Environment details (OS, Python version)
- Any screenshots or logs

## Response Time

- **Critical**: Within 24 hours
- **High**: Within 48 hours  
- **Medium**: Within 1 week
- **Low**: Within 2 weeks

## Disclosure Policy

We follow responsible disclosure:

1. **Acknowledge** receipt within 24 hours
2. **Assess** vulnerability severity
3. **Develop** fix (typically within 1-2 weeks)
4. **Coordinate** disclosure with reporter
5. **Release** security update
6. **Public** disclosure (after fix is available)

## Security Best Practices

### For Users

- Keep getv updated to latest version
- Use encryption for sensitive data (`getv[crypto]`)
- Set proper file permissions on profile directories
- Regularly rotate encryption keys
- Audit profiles for unused sensitive data

### For Developers

```python
# Always mask sensitive values in logs
from getv.security import mask_dict

# Use encryption for transport
from getv.security import encrypt_store, generate_key

# Validate input
def validate_profile_name(name: str) -> bool:
    return bool(re.match(r'^[a-zA-Z0-9_-]+$', name))
```

## Security Features

### Built-in Protections

- **Automatic secret detection** - masks passwords, tokens, keys
- **Fernet encryption** - AES-128 for sensitive values
- **File permissions** - secure defaults for encryption keys
- **Input validation** - profile name sanitization

### Sensitive Key Patterns

Keys matching these patterns are automatically masked:
- `PASSWORD`, `PASSWD`
- `SECRET`, `TOKEN`
- `API_KEY`, `APIKEY`
- `PRIVATE_KEY`, `ACCESS_KEY`
- `AUTH`, `CREDENTIAL`

## Vulnerability Types

We consider the following as security vulnerabilities:

- **Information disclosure** - unintended exposure of sensitive data
- **Injection** - command or code injection vulnerabilities
- **Authentication bypass** - unauthorized access to profiles
- **Encryption weaknesses** - flaws in cryptographic implementation
- **Path traversal** - unauthorized file system access
- **DoS** - denial of service vulnerabilities

## Non-Security Issues

These are typically not security vulnerabilities:

- Missing input validation (unless exploitable)
- Performance issues
- UI/UX problems
- Feature requests
- Documentation errors

## Security Updates

Security updates are released as:

- **Patch versions** (x.y.Z) for security fixes
- **Security advisories** on GitHub
- **Email notifications** for critical issues

Follow these steps to stay secure:

1. **Watch** the repository for releases
2. **Subscribe** to security advisories
3. **Update** promptly when security versions are released
4. **Review** changelog for security fixes

## Security Team

- **Lead**: Tom Sapletta (tom@sapletta.com)
- **Response**: Within 24 hours for critical issues

## Acknowledgments

We thank security researchers who help us keep getv secure. All valid security
reports will be acknowledged in our security advisories (with permission).

---

For questions about this security policy, email tom@sapletta.com
