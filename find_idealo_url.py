#!/usr/bin/env python3
"""
Helper script to manually find and update idealo.fr URLs in watchlist.yaml

Usage:
    python3 find_idealo_url.py "Midea PortaSplit climatiseur"

This will print the URL to add to config/watchlist.yaml
"""
import sys
import urllib.parse


def generate_idealo_search_url(product_query: str) -> str:
    """Generate idealo.fr search URL from product query."""
    encoded = urllib.parse.quote_plus(product_query)
    return f"https://www.idealo.fr/search.html?q={encoded}"


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nExemple:")
        print(f"  python3 find_idealo_url.py 'Climatiseur Midea PortaSplit'")
        print(f"\n  Génère: {generate_idealo_search_url('Climatiseur Midea PortaSplit')}")
        return 1

    query = " ".join(sys.argv[1:])
    url = generate_idealo_search_url(query)

    print(f"Produit: {query}")
    print(f"\nURL idealo.fr:")
    print(url)
    print("\nÀ copier dans config/watchlist.yaml pour darty, leroy_merlin, manomano")

    return 0


if __name__ == "__main__":
    sys.exit(main())

