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


def test_parse_product_page_matches_alias_with_compact_title() -> None:
    html = """
    <html>
      <head><title>MIDEA Climatiseur PortaSplit Mobile 12000 BTU</title></head>
      <body><div>En stock</div></body>
    </html>
    """

    parsed = parse_product_page(html, aliases=["Midea Porta Split", "MMCS"])

    assert parsed.matched_name == "Midea Porta Split"


def test_parse_product_page_reads_title_from_og_meta() -> None:
    html = """
    <html>
      <head>
        <meta property="og:title" content="Climatiseur portasplit Midea reversible 3500W" />
      </head>
      <body><h1></h1></body>
    </html>
    """

    parsed = parse_product_page(html, aliases=["Midea PortaSplit"])

    assert parsed.title == "Climatiseur portasplit Midea reversible 3500W"
    assert parsed.matched_name == "Midea PortaSplit"


