"""Robots et plan de site : aides au referencement, servis sans app Django."""
from django.http import HttpResponse
from django.views.decorators.http import require_GET

# Pages publiques a indexer (chemins racine inclus, sans le slash final inutile)
PAGES = [
    "",
    "a-propos/",
    "carte/",
    "depistage/",
    "conseils/",
    "triage/",
    "inscription/",
    "premiers-secours/",
    "politique-de-confidentialite/",
    "cgu/",
]

# Zones privees a ne PAS indexer
PRIVES = ["/admin/", "/dashboard/", "/profil/"]


@require_GET
def robots_txt(request):
    lignes = ["User-agent: *", "Allow: /"]
    lignes += [f"Disallow: {zone}" for zone in PRIVES]
    lignes += ["", f"Sitemap: https://{request.get_host()}/sitemap.xml", ""]
    return HttpResponse("\n".join(lignes), content_type="text/plain")


@require_GET
def sitemap_xml(request):
    base = f"https://{request.get_host()}"
    urls = "\n".join(
        f"  <url>\n    <loc>{base}/{page}</loc>\n    <changefreq>monthly</changefreq>\n  </url>"
        for page in PAGES
    )
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
           f"{urls}\n</urlset>\n")
    return HttpResponse(xml, content_type="application/xml")
