# Security Configuration Guide

## Kubernetes Secrets Setup

This project uses Kubernetes secrets to manage sensitive configuration. Follow these steps to set up secure credentials:

### 1. Generate Secure Secrets

```bash
# Generate a secure PostgreSQL password
POSTGRES_PASSWORD=$(openssl rand -base64 32)

# Generate a Flask secret key
FLASK_SECRET=$(python -c "import secrets; print(secrets.token_hex(32))")

# Create database URL
DB_URL="postgresql://financeuser:${POSTGRES_PASSWORD}@postgres-service:5432/financedb"
```

### 2. Create Kubernetes Secrets File

```bash
# Copy the template
cp k8s/secrets.yaml.template k8s/secrets.yaml

# Base64 encode your secrets
echo -n "$POSTGRES_PASSWORD" | base64
echo -n "$FLASK_SECRET" | base64
echo -n "$DB_URL" | base64
```

### 3. Update secrets.yaml

Replace the placeholder values in `k8s/secrets.yaml` with your base64-encoded secrets:

```yaml
data:
  postgres-password: <YOUR_BASE64_POSTGRES_PASSWORD>
  secret-key: <YOUR_BASE64_FLASK_SECRET>
  database-url: <YOUR_BASE64_DATABASE_URL>
```

### 4. Security Best Practices

- **Never commit secrets.yaml to version control**
- **Use different secrets for each environment**
- **Rotate secrets regularly**
- **Use external secret management in production** (AWS Secrets Manager, HashiCorp Vault)
- **Enable RBAC in Kubernetes clusters**
- **Use network policies to restrict pod communication**

### 5. Production Recommendations

For production deployments, consider:

- **External Secrets Operator**: Integrate with cloud secret managers
- **Sealed Secrets**: Encrypt secrets that can be stored in Git
- **SOPS**: Encrypt YAML files with age or PGP
- **Helm with values files**: Separate secret management

### 6. Environment Variables

For local development, create a `.env` file (not committed to Git):

```bash
# .env (local development only)
POSTGRES_PASSWORD=your-local-password
FLASK_SECRET_KEY=your-local-secret-key
DATABASE_URL=postgresql://financeuser:password@localhost:5432/financedb
```

## Security Checklist

- [ ] Generated unique, strong passwords
- [ ] Created secrets.yaml from template
- [ ] Verified secrets.yaml is in .gitignore
- [ ] Tested deployment with new secrets
- [ ] Documented secret rotation process
- [ ] Configured RBAC for production
- [ ] Set up monitoring for secret access
