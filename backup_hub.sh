#!/bin/bash

# Configuration
SOURCE_URL="https://yehudamiz007.github.io/mindmap/hub.html"
BACKUP_DIR="C:\Users\YEHUDA\.openclaw\workspace\backups\hub"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}\hub_${TIMESTAMP}.html"

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_DIR}"

# Download and save the hub page
curl -s "${SOURCE_URL}" -o "${BACKUP_FILE}"

# Verify the backup was created
if [ -f "${BACKUP_FILE}" ]; then
    echo "Backup successful: ${BACKUP_FILE}"
else
    echo "Backup failed: ${BACKUP_FILE}"
    exit 1
fi