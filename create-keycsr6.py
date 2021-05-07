from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from cryptography import x509
from cryptography.x509.oid import NameOID


def gen_rsa_key():
    return rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )


def gen_ec_key():
    return ec.generate_private_key(
        ec.SECP384R1(), default_backend()
    )


def gen_csr(key, c, s, l, o, ou, cn, domains):
    x509_name_list: typing.List[x509.GeneralName] = []
    for domain in domains:
        domain = domain.encode("idna").decode("utf-8")
        x509_name_list.append(x509.DNSName(domain))

    print(x509_name_list)
    csr = (
            x509.CertificateSigningRequestBuilder().subject_name(x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, c),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, s),
            x509.NameAttribute(NameOID.LOCALITY_NAME, l),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, o),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, ou),
            x509.NameAttribute(NameOID.COMMON_NAME, cn),
            ]))
            .add_extension(
                x509.SubjectAlternativeName(x509_name_list),
                critical=False,
            )
            .sign(key, hashes.SHA256(), default_backend())
        )
    return csr


def write_key(key, pass_phrase, path):
    pass_phrase = bytes(pass_phrase,"utf8")
    with open(path, "wb") as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.BestAvailableEncryption(
                pass_phrase),
        ))


def write_csr(csr, path):
    with open(path, "wb") as f:
        f.write(csr.public_bytes(serialization.Encoding.PEM))


# CSR using the key of the RSA
rsa_key = gen_rsa_key()

sans = ["server1.mydomain.com", "server2.mydomain.com", "server3"]

rsa_csr = gen_csr(rsa_key, "US", "Madison", "WI",
                  "Mycompany", "IT", "serverabc.domain.com", sans)

write_key(rsa_key, "password", "G:/__Code/python\SSL/CSR/rsaSANS2.key")

write_csr(rsa_csr, "G:/__Code/python\SSL/CSR/rsaSANS2.csr")
