from stock_alert.parser import parse_product_page


def test_parse_product_page_reads_json_ld_price_and_stock() -> None:
    html = """
    <html>
      <head>
        <title>PlayStation 5 Slim Console</title>
        <script type=\"application/ld+json\">
          {"offers": {"price": "499.99", "priceCurrency": "EUR"}}
        </script>
      </head>
      <body>
        <div>Produit en stock, livraison rapide</div>
      </body>
    </html>
    """

    parsed = parse_product_page(html, aliases=["PlayStation 5 Slim", "PS5"])

    assert parsed.title == "PlayStation 5 Slim Console"
    assert parsed.price == "499.99"
    assert parsed.currency == "EUR"
    assert parsed.in_stock is True
    assert parsed.matched_name == "PlayStation 5 Slim"


def test_parse_product_page_handles_out_of_stock() -> None:
    html = """
    <html>
      <head><title>Perceuse Bosch GSB 18V-55</title></head>
      <body>
        <p>Actuellement indisponible</p>
      </body>
    </html>
    """

    parsed = parse_product_page(html, aliases=["Bosch GSB 18V-55"])

    assert parsed.in_stock is False
    assert "Rupture" in parsed.availability_text

