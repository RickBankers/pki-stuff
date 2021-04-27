
from cryptography import x509
from cryptography.hazmat.backends import default_backend

def get_sans_from_csr(data):
    """
    Fetches SubjectAlternativeNames from CSR.
    Works with any kind of SubjectAlternativeName
    :param data: PEM-encoded string with CSR
    :return: List of LemurAPI-compatible subAltNames
    """
    sub_alt_names = []
    try:
        request = x509.load_pem_x509_csr(data.encode("utf-8"), default_backend())
    except Exception:
        raise ValidationError("CSR presented is not valid.")

    try:
        alt_names = request.extensions.get_extension_for_class(
            x509.SubjectAlternativeName
        )
        for alt_name in alt_names.value:
            sub_alt_names.append(
                {"nameType": type(alt_name).__name__, "value": alt_name.value}
            )
    except x509.ExtensionNotFound:
        pass

    return sub_alt_names


def get_cn_from_csr(data):
    try:
        request = x509.load_pem_x509_csr(data.encode("utf-8"), default_backend())
    except Exception:
        raise ValidationError("CSR presented is not valid.")

    try:
        common_name = request.subject.get_attributes_for_oid(x509.oid.NameOID.COMMON_NAME)
    except x509.ExtensionNotFound:
        pass

    return common_name


def get_data_from_csr(data):
    """
    Fetches SubjectAlternativeNames from CSR.
    Works with any kind of SubjectAlternativeName
    :param data: PEM-encoded string with CSR
    :return: List of LemurAPI-compatible subAltNames
    """
    cert_data = []
    try:
        request = x509.load_pem_x509_csr(data.encode("utf-8"), default_backend())
    except Exception:
        raise ValidationError("CSR presented is not valid.")

    try:
        common_name = request.subject.get_attributes_for_oid(x509.oid.NameOID.COMMON_NAME)[0].value
        cert_data.append(
                {"nameType": "common_name", "value": common_name}
            )
    except x509.ExtensionNotFound:
        pass


    try:
        alt_names = request.extensions.get_extension_for_class(
            x509.SubjectAlternativeName
        )
        for alt_name in alt_names.value:
            cert_data.append(
                {"nameType": type(alt_name).__name__, "value": alt_name.value}
            )
    except x509.ExtensionNotFound:
        pass

    return cert_data




pem_req_data = """-----BEGIN NEW CERTIFICATE REQUEST-----
MIID7TCCAtUCAQAwazELMAkGA1UEBhMCVVMxCzAJBgNVBAgMAldJMRAwDgYDVQQH
DAdNYWRpc29uMRIwEAYDVQQKDAlNeUNvbXBhbnkxCzAJBgNVBAsMAklUMRwwGgYD
VQQDDBN0ZXN0c2VydmVyLnRlc3QuY29tMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8A
MIIBCgKCAQEAtn+zY7u1BnKeRHeIAhZQEnD061m1bE9XIXCGDQDuWDUHqIvbloic
sq1ysVF0Uw/L6kKCcjRQxRZzPWbyT4QqwCjKUhBrmpD8gYnULnGensWnKKCjIktR
gRD0aTozP5x+fqFkkir6P9msDCNq0xTZQsdGdtpZoLUyjuPLXtxKcUkS/uMfTeI5
oHPrIopmcAMl9JzuHaCbBGidETAwAWQdXZ6TmQwejEJBXuZVHgtfuWiF9JYw63E7
ptBPWI0KCKEobtpDsI6TvmbcxvJgVUkxrI4tWw1RyVFK66ut1BVZhKHoVjV4VJjI
aLl/hfd1B/ttuYvKiWkvGWwJBkCZKJz08QIDAQABoIIBOzAcBgorBgEEAYI3DQID
MQ4WDDEwLjAuMTc3NjMuMjA7BgkrBgEEAYI3FRQxLjAsAgEJDAhOSUNUT0FNRAwQ
TklDVE9BTURcV29ybG9jawwLY2VydHJlcS5leGUwagYJKoZIhvcNAQkOMV0wWzAq
BgNVHREEIzAhggp0ZXN0c2VydmVyghN0ZXN0c2VydmVyLnRlc3QuY29tMB0GA1Ud
DgQWBBTcQ0QYfLZfz3gi16G0Y6uhHMcBHTAOBgNVHQ8BAf8EBAMCBSAwcgYKKwYB
BAGCNw0CAjFkMGICAQEeWgBNAGkAYwByAG8AcwBvAGYAdAAgAFIAUwBBACAAUwBD
AGgAYQBuAG4AZQBsACAAQwByAHkAcAB0AG8AZwByAGEAcABoAGkAYwAgAFAAcgBv
AHYAaQBkAGUAcgMBADANBgkqhkiG9w0BAQsFAAOCAQEAEF+1wOI0EQbHNQ0+vwlJ
7jTd2+OSdCUCWFwmje1uOu0ClHjq2bjPMdyHqxeJIi62ercoimtF8qmeqV+shrnF
ZpVZH5hzEsw7P8ygU0a2CS9kiWZOkRNHqoJDFjNaBbD5/i8D2iQJLAC1KeI/RE3/
QLtvAK7c9qvtNbIcIIaGJzeczxYxSBJS7l8oLW//p0HayKv0JsH/6CLQezIB2fpb
/EmlJP7UMj/PiKxVgqRbx09kbolwYkd4lelttrEZNe9SMtcvCI4Vl7UFYhmLon2b
lg0awcCXlpXmPtw2xy28Np3Gvmfqbkr/UZElmubxGoK/3cGopoYpFuxLsoUpeoTV
AQ==
-----END NEW CERTIFICATE REQUEST-----"""


#print(get_sans_from_csr(pem_req_data))

#print(get_cn_from_csr(pem_req_data))

print(get_data_from_csr(pem_req_data))

