# Security Documentation

## Overview
This document outlines the security measures implemented in the Smart Attendance Monitoring System and best practices for maintaining a secure deployment.

## Security Improvements Implemented

### 1. Password Hashing & Authentication
✅ **Status: IMPLEMENTED**

- All passwords are now hashed using bcrypt (12 rounds)
- Password verification happens securely without plaintext comparison
- Password strength validation enforced (8+ chars, uppercase, lowercase, digits, special chars)
- Use `setup_admin_password.py` to create secure admin accounts

**Usage:**
```bash
python setup_admin_password.py
```

### 2. Secrets Management
✅ **Status: IMPLEMENTED**

- All sensitive configurations moved to `.env` file
- Environment variables loaded via `python-dotenv`
- Template provided: `.env.template`

**Setup:**
```bash
cp .env.template .env
# Edit .env with your values
```

**⚠️ CRITICAL:** Never commit `.env` to version control!

### 3. CSRF Protection
✅ **Status: IMPLEMENTED**

- Flask-WTF integrated for CSRF token validation
- All POST/PUT/DELETE endpoints protected with `@csrf.protect` decorator
- Tokens generated per session

**For Frontend Forms:**
Include in HTML forms:
```html
{{ csrf_token() }}
```

### 4. Rate Limiting
✅ **Status: IMPLEMENTED**

- Login endpoint rate-limited to 5 requests per minute
- API endpoints rate-limited to 100 requests per hour
- Uses Flask-Limiter with in-memory storage

**Configuration (`.env`):**
```
RATE_LIMIT_LOGIN=5/minute
RATE_LIMIT_API=100/hour
```

### 5. Session Security
✅ **Status: IMPLEMENTED**

- Session cookies marked as HttpOnly (prevents JavaScript access)
- Session lifetime limit: 2 hours
- Session permanent flag set on login

**Configuration (`.env`):**
```
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SECURE=False  # Set True in production with HTTPS
SESSION_COOKIE_SAMESITE=Lax
```

### 6. Security Headers
✅ **Status: IMPLEMENTED**

- Flask-Talisman adds security headers:
  - X-Frame-Options: DENY (prevents clickjacking)
  - X-Content-Type-Options: nosniff
  - X-XSS-Protection: 1; mode=block
  - Strict-Transport-Security (on HTTPS)

### 7. Database Security
✅ **Status: PARTIALLY IMPLEMENTED**

- Connection pooling for efficient resource management
- Parameterized queries prevent SQL injection
- Autocommit disabled for transaction safety

**Still needs:**
- Implement SQLAlchemy ORM (currently using raw SQL)
- Add database encryption for sensitive fields
- Regular database backups

### 8. Error Handling
✅ **Status: IMPLEMENTED**

- Generic error messages prevent information leakage
- No stack traces exposed to users
- All errors logged server-side

## Configuration Files

### `.env` File Structure
```
# Database
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_secure_password
DB_NAME=smart_monitoring

# Flask
FLASK_ENV=development          # Change to 'production'
FLASK_DEBUG=False              # Critical: Keep False in production
FLASK_SECRET_KEY=your_secret_key

# Security
SESSION_COOKIE_SECURE=False    # True in production with HTTPS
CSRF_ENABLED=True

# JWT
JWT_SECRET=your_jwt_secret
JWT_EXPIRATION_HOURS=2

# Rate Limiting
RATE_LIMIT_LOGIN=5/minute
RATE_LIMIT_API=100/hour

# Email
SENDER_EMAIL=your_email@institution.edu
SENDER_PASSWORD=your_app_password
```

### `config.py` Structure
- Centralized configuration management
- Environment-based configurations (Development, Production, Testing)
- Secure defaults for all security settings

## Deployment Checklist

### Before Production Deployment

- [ ] Generate strong `FLASK_SECRET_KEY` (use `secrets` module)
- [ ] Generate strong `JWT_SECRET`
- [ ] Update admin password using `setup_admin_password.py`
- [ ] Set `FLASK_ENV=production`
- [ ] Set `FLASK_DEBUG=False`
- [ ] Set `SESSION_COOKIE_SECURE=True` (requires HTTPS)
- [ ] Enable HTTPS/SSL certificate
- [ ] Set `FLASK_PREFERRED_URL_SCHEME=https`
- [ ] Update database credentials
- [ ] Rotate all default/placeholder credentials
- [ ] Enable request logging
- [ ] Set up monitoring and alerting
- [ ] Review and restrict allowed origins in CORS
- [ ] Test rate limiting
- [ ] Verify CSRF protection
- [ ] Backup database encryption keys
- [ ] Review logs/app.log location and access

### Production Environment Setup

**Use a production WSGI server (e.g., Gunicorn):**
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

**Enable HTTPS with Nginx reverse proxy:**
```nginx
server {
    listen 443 ssl http2;
    server_name your_domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header X-Forwarded-For $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Incident Response

### Suspicious Activity
- Monitor `/logs/app.log` for authentication failures
- Rate limiting will automatically block brute force attempts
- Review session logs for unauthorized access

### Password Compromise
```bash
# Reset admin password
python setup_admin_password.py
```

### Database Breach
- Change all credentials in `.env`
- Force password reset for all users
- Review access logs
- Consider enabling audit logging

## Security Best Practices

### For Developers
- Never commit `.env` or secrets to version control
- Use parameterized queries (avoid string concatenation in SQL)
- Validate all user inputs
- Log security events
- Keep dependencies updated: `pip install --upgrade -r requirements.txt`
- Use strong passwords (test with `PasswordValidator`)

### For Administrators
- Regular security audits
- Enable firewall rules for database port (3306)
- Restrict admin access to trusted IP ranges
- Monitor system resources and logs
- Regular database backups
- Keep OS and dependencies patched
- Use fail2ban or similar for brute-force protection

### For Users
- Change default passwords immediately
- Use strong, unique passwords
- Report suspicious activity
- Don't share credentials
- Log out when finished

## Known Limitations & Future Improvements

### Current (v1.0)
- Passwords hashed with bcrypt
- Basic rate limiting
- CSRF protection enabled
- Session security configured

### Planned (v2.0+)
- [ ] Two-factor authentication (2FA)
- [ ] Comprehensive audit logging
- [ ] Database encryption at rest
- [ ] API key authentication (service-to-service)
- [ ] OAuth2 integration
- [ ] IP whitelisting for admin
- [ ] DDoS protection
- [ ] Web Application Firewall (WAF)
- [ ] Security vulnerability scanning
- [ ] SIEM integration

## Security Contacts & Resources

- Report security issues to: `security@institution.edu`
- Follow responsible disclosure: Wait 30 days before public disclosure
- OWASP Top 10: https://owasp.org/www-project-top-ten/
- Flask Security: https://flask.palletsprojects.com/
- Python Security: https://python.readthedocs.io/en/latest/library/security_warnings.html

## Version History

- **v1.0** (April 2026): Initial security hardening
  - Password hashing with bcrypt
  - CSRF protection
  - Rate limiting
  - Session security
  - Secrets management

---

**Last Updated:** April 5, 2026
**Maintained By:** Security Team
