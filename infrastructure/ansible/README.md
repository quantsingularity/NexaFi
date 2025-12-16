# Ansible Automation

## Prerequisites

- Ansible >= 2.14
- Python >= 3.10
- SSH access to target servers

## Directory Structure

- `playbooks/` - Ansible playbooks
- `roles/` - Ansible roles
- `inventory/` - Inventory files
- `ansible.cfg` - Ansible configuration

## Quick Start

### 1. Setup Inventory

```bash
# Copy and edit inventory
cp inventory/hosts.example inventory/hosts
vim inventory/hosts
```

### 2. Test Connectivity

```bash
# Ping all hosts
ansible all -i inventory/hosts -m ping

# Check ansible version on hosts
ansible all -i inventory/hosts -m shell -a "ansible --version"
```

### 3. Run Playbooks

```bash
# Dry run (check mode)
ansible-playbook -i inventory/hosts playbooks/configure.yml --check

# Run playbook
ansible-playbook -i inventory/hosts playbooks/configure.yml

# Run with specific tags
ansible-playbook -i inventory/hosts playbooks/configure.yml --tags "setup,config"

# Run on specific hosts
ansible-playbook -i inventory/hosts playbooks/configure.yml --limit "prod-server-1"
```

## Ansible Vault (Secrets)

### Create Encrypted Variables

```bash
# Create vault password file
cp .vault_password.example .vault_password
echo "your-secure-password" > .vault_password
chmod 600 .vault_password

# Create encrypted file
ansible-vault create group_vars/production/vault.yml --vault-password-file=.vault_password

# Edit encrypted file
ansible-vault edit group_vars/production/vault.yml --vault-password-file=.vault_password

# Run playbook with vault
ansible-playbook -i inventory/hosts playbooks/configure.yml --vault-password-file=.vault_password
```

## Validation

```bash
# Lint playbooks
ansible-lint playbooks/

# Syntax check
ansible-playbook -i inventory/hosts playbooks/configure.yml --syntax-check

# List tasks
ansible-playbook -i inventory/hosts playbooks/configure.yml --list-tasks

# List hosts
ansible-playbook -i inventory/hosts playbooks/configure.yml --list-hosts
```

## Best Practices

1. Always use `--check` mode first (dry run)
2. Use tags for selective execution
3. Keep secrets in Ansible Vault
4. Use roles for reusability
5. Test in development/staging before production
