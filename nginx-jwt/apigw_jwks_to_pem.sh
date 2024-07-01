#!/bin/sh

set -eo pipefail

command -v curl >/dev/null || { echo >&2 "error: curl not found";  exit 3; }
command -v jq >/dev/null || {  echo >&2 "error: jq not found";  exit 3; }
command -v fold &>/dev/null || { echo >&2 "ERROR: fold not found"; exit 3; }
command -v openssl &>/dev/null || { echo >&2 "ERROR: openssl not found"; exit 3; }

extract_keys() {
    jwks_url=$1
    keyprefix=$2

    for k in $(curl -s "${jwks_url}" | jq -r '.keys[] .kid'); do
        echo "Exporting KID: ${k}"
        cert_file="${keyprefix}-apigw-${k}-certificate.pem"
        public_key_file="${keyprefix}-apigw-${k}-public_key.pem"

        echo "  cert_file: ${cert_file}"
        echo "  public_key_file: ${public_key_file}"

        x5c=$(curl -s "${jwks_url}" | jq -r ".keys [] | select(.kid==\"${k}\") |  .x5c [0]")
        echo '-----BEGIN CERTIFICATE-----' >"${cert_file}"
        echo "$x5c" | fold -w64 >>"${cert_file}"
        echo '-----END CERTIFICATE-----' >>"${cert_file}"

        openssl x509 -in "${cert_file}" -pubkey -noout >"${public_key_file}"
    done
}

extract_keys "https://api.cpas.cz/openid/connect/jwks.json" "prod"
extract_keys "https://api-test.cpas.cz/openid/connect/jwks.json" "test"