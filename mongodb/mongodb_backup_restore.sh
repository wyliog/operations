#!/bin/bash
set -e

export PATH="$PATH:/usr/local/bin"
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo $DIR
# Store the current date in YYYY-mm-DD-HHMMSS
DATE=$(date -u "+%F-%H%M%S")
MONGODB_USER=
MONGODB_PASSWORD=
MINIO_ACCESS_KEY=
MINIO_SECRET_KEY=
MINIO_BUCKET=
MINIO_HOST=
function usage()
{
cat << EOF
usage: $0 options

This script dumps the current mongo database, tars it, then sends it to an Amazon S3 bucket.

OPTIONS:
   -h      Show this message
   -n      Namespace
   -u      Mongodb user
   -p      Mongodb password
   -d      Mongodb Database
   -k      Minio Access Key
   -s      Minio Secret Key
   -b      Minio  bucket name
   -host   Minio host
EOF
}

while getopts “h:u:p:k:s:b:” OPTION
do
  case $OPTION in
    h)
      usage
      exit 1
      ;;
    u)
      MONGODB_USER=$OPTARG
      ;;
    p)
      MONGODB_PASSWORD=$OPTARG
      ;;
    d)
      MONGODB_DATABASE=$OPTARG
      ;;
    k)
      MINIO_ACCESS_KEY=$OPTARG
      ;;
    s)
      MINIO_SECRET_KEY=$OPTARG
      ;;
    b)
      MINIO_BUCKET=$OPTARG
      ;;
    host)
      MINIO_HOST=$OPTARG
      ;;
    n)
      NAMESPACE=$OPTARG
      ;;
    ?)
      usage
      exit
    ;;
  esac
done

FILE_NAME="${NAMESPACE}-backup-$DATE"
ARCHIVE_NAME="$FILE_NAME.tar.gz"
MONGODB_BACKUP_FILE=$DIR/backup/$ARCHIVE_NAME

function mongo_dump()
{
  if [[ -z $MONGODB_USER ]] || [[ -z $MONGODB_PASSWORD ]]
  then
    usage
    exit 1
  fi

  # Lock the database
  mongo --ssl --sslAllowInvalidCertificate  -username "$MONGODB_USER" -password "$MONGODB_PASSWORD" admin --eval "var databaseNames = db.getMongo().getDBNames(); for (var i in databaseNames) { printjson(db.getSiblingDB(databaseNames[i]).getCollectionNames()) }; printjson(db.fsyncLock());"

  # Dump the database
  mongodump --ssl --sslAllowInvalidCertificate  -username "$MONGODB_USER" -password "$MONGODB_PASSWORD" --out $DIR/backup/$FILE_NAME

  # Unlock the database
  mongo --ssl --sslAllowInvalidCertificate -username "$MONGODB_USER" -password "$MONGODB_PASSWORD" admin --eval "printjson(db.fsyncUnlock());"

  # Tar Gzip the file
  tar -C $DIR/backup/ -zcvf ${MONGODB_BACKUP_FILE} $FILE_NAME/

  # Remove the backup directory
  rm -r $DIR/backup/$FILE_NAME
}

function mongo_restore()
{
    echo ""
}

function push_to_minio()
{
  # Send the file to the backup drive or S3
  MINIO_HOST=$1
  MINIO_BUCKET=$2
  MINIO_SECRET_KEY=$3
  MONGODB_BACKUP_FILE=$4
  HEADER_DATE=$(date -u "+%a, %d %b %Y %T %z")
  CONTENT_MD5=$(openssl dgst -md5 -binary ${MONGODB_BACKUP_FILE} | openssl enc -base64)
  CONTENT_TYPE="application/x-download"
  STRING_TO_SIGN="PUT\n$CONTENT_MD5\n$CONTENT_TYPE\n$HEADER_DATE\n/$MINIO_BUCKET/$ARCHIVE_NAME"
  SIGNATURE=$(echo -e -n $STRING_TO_SIGN | openssl dgst -sha1 -binary -hmac $MINIO_SECRET_KEY | openssl enc -base64)

  curl -X PUT \
  --header "Host: ${MINIO_HOST} " \
  --header "Date: $HEADER_DATE" \
  --header "content-type: $CONTENT_TYPE" \
  --header "Content-MD5: $CONTENT_MD5" \
  --header "Authorization: AWS $MINIO_ACCESS_KEY:$SIGNATURE" \
  --upload-file $DIR/backup/$ARCHIVE_NAME \
  https:/${MINIO_HOST}/$ARCHIVE_NAME
}

mongo_dump
push_to_minio ${MINIO_HOST} ${MINIO_BUCKET} ${MINIO_SECRET_KEY} ${MONGODB_BACKUP_FILE}