#!/usr/bin/env bash

#############################################
# Rollback Script
#
# Restores a previous deployment backup.
#############################################

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

DEPLOY_PATH="${DEPLOY_PATH:-/var/www/oneal-api}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups}"
BACKUP_PREFIX="${BACKUP_PREFIX:-oneal-api}"

echo -e "${YELLOW}🔙 Rollback Tool${NC}\n"

echo -e "${GREEN}Available backups:${NC}"
mapfile -t BACKUPS < <(ls -t "$BACKUP_DIR" | grep "^${BACKUP_PREFIX}-" || true)

if [ "${#BACKUPS[@]}" -eq 0 ]; then
  echo -e "${RED}❌ No backups found${NC}"
  exit 1
fi

for i in "${!BACKUPS[@]}"; do
  BACKUP="${BACKUPS[$i]}"
  SIZE=$(du -sh "$BACKUP_DIR/$BACKUP" | cut -f1)
  echo -e "  ${GREEN}[$i]${NC} $BACKUP (Size: $SIZE)"
done

echo -ne "\n${YELLOW}Enter backup number to restore (0-$((${#BACKUPS[@]}-1))): ${NC}"
read -r SELECTION

if ! [[ "$SELECTION" =~ ^[0-9]+$ ]] || [ "$SELECTION" -ge ${#BACKUPS[@]} ]; then
  echo -e "${RED}❌ Invalid selection${NC}"
  exit 1
fi

SELECTED_BACKUP="${BACKUPS[$SELECTION]}"
BACKUP_PATH="$BACKUP_DIR/$SELECTED_BACKUP"

echo -e "\n${YELLOW}⚠️  You are about to rollback to: $SELECTED_BACKUP${NC}"
echo -ne "${YELLOW}Continue? (y/n): ${NC}"
read -r CONFIRM

if [[ "$CONFIRM" != "y" ]]; then
  echo -e "${RED}❌ Rollback cancelled${NC}"
  exit 0
fi

TIMESTAMP=$(date +%Y%m%d-%H%M%S)
CURRENT_BACKUP="$BACKUP_DIR/${BACKUP_PREFIX}-pre-rollback-$TIMESTAMP"

echo -e "${YELLOW}💾 Backing up current state...${NC}"
cp -r "$DEPLOY_PATH" "$CURRENT_BACKUP"

echo -e "${YELLOW}🔙 Rolling back to $SELECTED_BACKUP...${NC}"
rsync -av --delete "$BACKUP_PATH/" "$DEPLOY_PATH/"

echo -e "${YELLOW}🔒 Setting permissions...${NC}"
chown -R www-data:www-data "$DEPLOY_PATH"
chmod -R 755 "$DEPLOY_PATH"

echo -e "${GREEN}✅ Rollback completed successfully!${NC}"
echo -e "${GREEN}📍 Restored from: $BACKUP_PATH${NC}"
echo -e "${GREEN}💾 Current state saved: $CURRENT_BACKUP${NC}"
