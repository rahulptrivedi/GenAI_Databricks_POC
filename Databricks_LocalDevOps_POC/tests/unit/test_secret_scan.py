from scripts.scan_secrets import scan_text


def test_secret_scan_detects_common_credentials() -> None:
    assert scan_text("token = 'dapi" + "a" * 32 + "'")
    assert scan_text("client_secret='" + "s" * 24 + "'")
    assert scan_text("AWS key AKIA" + "1234567890ABCDEF")


def test_secret_scan_allows_empty_or_placeholder_configuration() -> None:
    assert not scan_text("DATABRICKS_CLIENT_SECRET=")
    assert not scan_text("DATABRICKS_CLIENT_SECRET=<secret-store-reference>")
    assert not scan_text("DATABRICKS_CLIENT_SECRET=\nDATABRICKS_WAREHOUSE_ID=")
