#!/usr/bin/env python3
# SPDX-License-Identifier: Unlicense

# This is a script I made to replace certbot, since my domain registrar isn't supported by Certbot DNS-01.
# I'm sharing it so others can use it as example/template, nothing else.
# It intentionally lacks configurability, error handling, coding style, etc.
# Keyword spam: Python ACME client wildcard DNS-01 Let's Encrypt example

import base64, json, hashlib, os
from OpenSSL import crypto, SSL
import xmlrpc.client
try:
	from mycert_conf import *  # This is separate because it contains passwords/etc, nothing else.
except ImportError:
	conf_domains = [ "muncher.se", "*.muncher.se" ]
	conf_account_location = "https://acme-v02.api.letsencrypt.org/acme/acct/12345678" 
	conf_account_key = b"""
-----BEGIN PRIVATE KEY-----
MIIEaaAAAAAAAaaaaaaA1a1AAAAAAAAAAAaaaaAaAaAAAaAAAAA1AA1aAa1AAAAA
aaaAaAAaAAAa/1a/A1Aa11aaaaa+1A/a1AaAaAAaA+AAa+1aaaa1aaa1aAAA+a1a
1AaaAAa1AAaAaA11Aa1AaAaaAAaaaAAaAAaaaaAaaaA1A1aA1aaaAa1AaaaaaAAA
aaaaAaaaAaaa1aaaaaaA1aA1aaAAAa1aaaAaaAAaaa1aa1a1111A1aA1aAaa1aaa
11AA1aAaAAa1AaaAaaaAaA11AAAaAAa1aaaAaaAaaAAaAa1AAAaaa1aAa1aA1Aaa
AA1//aAaaaAA1AAAAa1AaAAAA1aaA1AaA1a1aa+aaAAAaaa/Aaa11+AAaaaaaaaA
AAAAaaa1AaAAAAAAaaAAAAaaaaAaaa11AAaAAAaa1AaAAaAa1aAA11AaaaaAaaaA
AaAAA1aaAA1AAAaaAAAAAaaAAa1aA1AAaaA1aaa1AA1aA1Aa/AaAAAAA1AAaAAAA
A1aaAaaaAAaa/aAAaA1aAaaaAaaa1aaa1aaAaA1Aa1aAaa1aAAA1a1AA1aaAA1aA
AAAaaaAAAaAa11aA1AAa1A1aaAaaaaaAAAAaa1AaaAAaAAa11Aaa1aaAaaaAAaAA
aAAaA11aAAAA11aA1AAAaaAa1a1aAA11AA1A1Aa1AA1aAaaAa1Aa1AaaaAaa1aAA
aAaA1aaaAaAAAAaaA1aa1aaaaaAaAAaaA+aAa/aAaaAAaAAA1AaA1aaa1AaAaA1a
AaAaAAAaAAAaAaaAAAAA1AAA1A1AaAaAaaAAaaa1AAAA+a1AAaaa/AaaAaaa1aaA
AAaAaAA1A1Aa1AaAaA11aAAaaAaaA1+a1aA1aA1Aaa/aa1AAAAA11AaAAAA111a+
11AaaAaAa1AAa1aAA1aA1/A1aaAAaAAAaAAAaAaAAAaAaaaaAAaaAA1aaA1AAAAa
+AaAaAaaA1AaAAaaAa1AAAAaAAAaAAaAA1AA11a1aAaaAaa11aaAA+aAAAAA1A1a
AAAAaAA1AAaaa1aaAAaaAaAaAAAAAAA1aA1aaaaAaaA1aAAAaAAaaaAaAAAA/aaA
aAa1AaaAAAaAaAAAaA1aaa1AaAa111+AA1aAa1a1aAa1/Aa1/1aAaa11aaaA1Aaa
AaAAaAA1aA1AA1Aa1aaaaaAAA11Aaaa1AAaaaA11aaAaaaa1AAaAA/AAAaaaA1AA
AA+aAAAa11aAA11AAAa1aaaAaAAa1Aa1aaaa1aaaaAAAAAAaaAAAAaaaAAAAaAAa
A1AAaaaA1Aa11a1Aa/aaaAaA1aaaaAAaAAaA/aa1a1AAAaAa11a1aAAAAAa1aaA1
aaaAA111aaAA/aAAAAAaa1aaA1aAaAaAaAAa1AAAAaaaAa1AaaA/aaaAAaaaA1AA
AAaAAAAAAAAaAAAa1a1Aa1aaAaAaaAA1A1A1AAAaAaAAAAaa1aaAaaAaAaa1AA1a
AAA1/aAAAaaAA11a1aa1Aaaaaaa1AaA1/1AAAaAaaAAAAAAA1Aaa/A1/A1a+1A1a
aAaaAAAa+aaaAaaa11AA1aAaaAaAaAAa1A1aAAA1aAAA1aAAAAAa1AaAA1a1aAaa
1a1a/AaAA1AAaaAAaaAAa1==
-----END PRIVATE KEY-----
"""
	conf_loopia_password = "hunter2"
	conf_loopia_id = 1234567

nonces = []
directory = None
account = None
jwk = None

def b64(b):
	return base64.urlsafe_b64encode(b).decode('utf8').replace("=", "")
def b64int(i):
	return b64(i.to_bytes((i.bit_length()+7)//8, byteorder="big"))

# returns ( code, headers, body )
def http_raw(url, body):
	print("Requesting", url)
	from urllib.request import urlopen, Request
	try:
		rsp = urlopen(Request(url, data=body, headers={"Content-Type": "application/jose+json",
		                           "User-Agent": "mycert.py +https://github.com/Alcaro/misctoys/blob/master/mycert.py"}))
		ret, code, headers = rsp.read().decode("utf8"), rsp.getcode(), rsp.headers
	except IOError as e:
		ret = e.read().decode("utf8") if hasattr(e, "read") else str(e)
		code, headers = getattr(e, "code", None), {}
	if "Replay-Nonce" in headers:
		nonces.append(headers["Replay-Nonce"])
	try:
		return ( code, headers, json.loads(ret) )
	except ValueError:
		return ( code, headers, ret )

def http(url, body=None):
	global nonces
	global directory
	
	while not nonces:
		http_raw(directory['newNonce'], None)
	nonce = nonces.pop(0)
	
	if body is None: body = ""
	else: body = b64(json.dumps(body).encode("utf-8"))
	protected = { "url": url, "alg": "RS256", "nonce": nonce }
	
	if account:
		protected["kid"] = account["Location"]
	else:
		protected["jwk"] = jwk
	
	protected = b64(json.dumps(protected).encode("utf-8"))
	signature = crypto.sign(key, (protected+"."+body).encode("utf-8"), "SHA256")
	signed_body = json.dumps({"protected": protected, "payload": body, "signature": b64(signature)}).encode("utf-8")
	code, headers, ret = http_raw(url, signed_body)
	
	if code == 400 and ret['type'] == "urn:ietf:params:acme:error:badNonce":
		return http(url, body)
	
	return ( code, headers, ret )

key = crypto.load_privatekey(crypto.FILETYPE_PEM, conf_account_key)

keynum = key.to_cryptography_key().public_key().public_numbers()
jwk = { "e": b64int(keynum.e), "kty": "RSA", "n": b64int(keynum.n) }
thumbprint = b64(hashlib.sha256(json.dumps(jwk, sort_keys=True, separators=(',', ':')).encode('utf8')).digest())

_,_,directory = http_raw("https://acme-v02.api.letsencrypt.org/directory", None)
# directory = {'VubEODguSzk': 'https://community.letsencrypt.org/t/adding-random-entries-to-the-directory/33417', 'keyChange': 'https://acme-v02.api.letsencrypt.org/acme/key-change', 'meta': {'caaIdentities': ['letsencrypt.org'], 'termsOfService': 'https://letsencrypt.org/documents/LE-SA-v1.2-November-15-2017.pdf', 'website': 'https://letsencrypt.org'}, 'newAccount': 'https://acme-v02.api.letsencrypt.org/acme/new-acct', 'newNonce': 'https://acme-v02.api.letsencrypt.org/acme/new-nonce', 'newOrder': 'https://acme-v02.api.letsencrypt.org/acme/new-order', 'revokeCert': 'https://acme-v02.api.letsencrypt.org/acme/revoke-cert'}
print(directory)
# _,account,_ = http(directory["newAccount"], { "termsOfServiceAgreed": True, "contact": [ "mailto:floating@muncher.se" ] })
account = { "Location": conf_account_location }
print(account)

_,_,order = http(directory['newOrder'], {"identifiers": [{"type": "dns", "value": d} for d in conf_domains]})
print(order)

validate_reqs = []
to_delete = []
for auth in order["authorizations"]:
	_,_,challenges = http(auth, None)
	print(challenges)
	challenges = { ch["type"] : ch for ch in challenges["challenges"] }
	chosen = challenges.get("http-01") or challenges.get("dns-01")
	token = chosen["token"] + "." + thumbprint
	
	if chosen["type"] == "http-01":
		path = "/home/alcaro/mount/muncher.se/etc/ssl/acme-challenge/"+chosen["token"]
		with open(path, "wt") as f:
			f.write(token)
		to_delete.append(path)
	elif chosen["type"] == "dns-01":
		enctoken = b64(hashlib.sha256(token.encode('utf8')).digest())
		xmlrpc.client.ServerProxy(uri="https://api.loopia.se/RPCSERV", encoding="utf-8").\
		       updateZoneRecord("floatingmunchers@loopiaapi", conf_loopia_password, "muncher.se", "_acme-challenge",
		                        { "type":"TXT", "ttl":300, "priority":0, "rdata":enctoken, "record_id":conf_loopia_id })
	else:
		1/0
	
	validate_reqs.append(chosen["url"])

for n in range(60):
	import time
	print("Waiting", 60-n, "seconds for DNS propagation")
	time.sleep(1)

for url in validate_reqs:
	_,_,status = http(url, {})
	print(status)

for n in range(60):
	import time
	print("Waiting", 60-n, "seconds for validation")
	time.sleep(1)

out_key = crypto.PKey()
out_key.generate_key(crypto.TYPE_RSA, 2048)
with open("/home/alcaro/mount/server/etc/ssl/live/privkey.pem", "wb") as f:
	f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, out_key))

csr = crypto.X509Req()
csr.get_subject().CN = conf_domains[0]
csr.add_extensions([
        # crypto.X509Extension(b"keyUsage", False, b"Digital Signature, Non Repudiation, Key Encipherment"),
        # crypto.X509Extension(b"basicConstraints", False, b"CA:FALSE"),
        crypto.X509Extension(b"subjectAltName", True, b", ".join(b"DNS:"+d.encode("utf-8") for d in conf_domains))
    ])

csr.set_pubkey(out_key)
csr.sign(out_key, "sha256")
_,_,result = http(order["finalize"], { "csr": b64(crypto.dump_certificate_request(crypto.FILETYPE_ASN1, csr)) })
print(result)

_,_,cert = http(result["certificate"], None)
print(cert)

with open("/home/alcaro/mount/server/etc/ssl/live/fullchain.pem", "wt") as f:
	f.write(cert)

print("Cleaning up")

xmlrpc.client.ServerProxy(uri="https://api.loopia.se/RPCSERV", encoding="utf-8").\
       updateZoneRecord("floatingmunchers@loopiaapi", conf_loopia_password, "muncher.se", "_acme-challenge",
                        { "type":"TXT", "ttl":300, "priority":0, "rdata":"123", "record_id":conf_loopia_id })

for fn in to_delete:
	os.remove(fn)




