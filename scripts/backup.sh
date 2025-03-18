#!/bin/bash
# Automated backup script for Virtual Assistant system
# Features: Encryption, rotation, cloud upload, and verification

set -e

# Configuration
BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
RETENTION_DAYS=30
ENCRYPT_PASSWORD="${VA_BACKUP_PASSWORD}" # Set in environment
CLOUD_STORAGE="s3://your-bucket/backups" # Change to your cloud provider

# Create backup directory structure
mkdir -p ${BACKUP_DIR}/{data,db,config}

# Database Backup
echo "[$(date)] Starting database backup..."
docker exec postgres pg_dumpall -U postgres | gzip > ${BACKUP_DIR}/db/va-db-${TIMESTAMP}.sql.gz

# Application Data Backup
echo "[$(date)] Backing up application data..."
tar czf ${BACKUP_DIR}/data/va-data-${TIMESTAMP}.tar.gz \
    --exclude='tmp/*' \
    --exclude='cache/*' \
    /app/data

# Config Backup
echo "[$(date)] Backing up configuration..."
tar czf ${BACKUP_DIR}/config/va-config-${TIMESTAMP}.tar.gz \
    /app/config/*.env \
    /app/config/*.vault

# Encrypt backups
function encrypt_backup {
    echo "[$(date)] Encrypting ${1}..."
    openssl enc -aes-256-cbc -salt -in ${1} -out ${1}.enc -pass pass:${ENCRYPT_PASSWORD}
    rm -f ${1} # Remove unencrypted original
}

if [ -n "${ENCRYPT_PASSWORD}" ]; then
    encrypt_backup ${BACKUP_DIR}/db/va-db-${TIMESTAMP}.sql.gz
    encrypt_backup ${BACKUP_DIR}/data/va-data-${TIMESTAMP}.tar.gz
    encrypt_backup ${BACKUP_DIR}/config/va-config-${TIMESTAMP}.tar.gz
fi

# Cloud Upload
echo "[$(date)] Uploading to cloud storage..."
aws s3 sync ${BACKUP_DIR} ${CLOUD_STORAGE} --delete --quiet

# Rotate local backups
echo "[$(date)] Rotating old backups (older than ${RETENTION_DAYS} days)..."
find ${BACKUP_DIR} -name '*.enc' -mtime +${RETENTION_DAYS} -exec rm -f {} \;

# Verify backup integrity
function verify_backup {
    if [ -n "${ENCRYPT_PASSWORD}" ]; then
        if ! openssl enc -d -aes-256-cbc -pass pass:${ENCRYPT_PASSWORD} -in ${1} | gunzip -t; then
            echo "Backup verification failed for ${1}"
            exit 1
        fi
    else
        if ! gunzip -t ${1}; then
            echo "Backup verification failed for ${1}"
            exit 1
        fi
    fi
}

echo "[$(date)] Verifying backups..."
verify_backup ${BACKUP_DIR}/db/va-db-${TIMESTAMP}.sql.gz*
verify_backup ${BACKUP_DIR}/data/va-data-${TIMESTAMP}.tar.gz*
verify_backup ${BACKUP_DIR}/config/va-config-${TIMESTAMP}.tar.gz*

echo "[$(date)] Backup completed successfully"
exit 0