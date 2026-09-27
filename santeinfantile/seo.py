"""Robots, plan de site et fichiers pour assistants IA (llms.txt), servis sans app Django."""
from django.http import HttpResponse
from django.views.decorators.http import require_GET

from . import llms

# Pages publiques a indexer (chemins racine inclus, sans le slash final inutile)
PAGES = [
    "",
    "a-propos/",
    "carte/",
    "depistage/",
    "conseils/",
    "conseils/nutrition/",
    "triage/",
    "inscription/",
    "premiers-secours/",
    "politique-de-confidentialite/",
    "politique-des-cookies/",
    "cgu/",
]

# Zones privees a ne PAS indexer ni explorer
PRIVES = [
    "/admin/",
    "/dashboard/",
    "/profil/",
    "/triage/chat/",
    "/carte/osm/",
    "/phone/",
    "/hors-ligne/",
]

# Assistants IA et moteurs de recherche : explicitement les bienvenus sur les
# pages publiques. Les zones privees restent interdites a tous.
BOTS_IA = [
    "GPTBot",
    "OAI-SearchBot",
    "ChatGPT-User",
    "ClaudeBot",
    "Claude-User",
    "Claude-SearchBot",
    "anthropic-ai",
    "PerplexityBot",
    "Perplexity-User",
    "Google-Extended",
    "Applebot-Extended",
    "CCBot",
    "Amazonbot",
    "meta-externalagent",
    "YouBot",
    "DuckAssistBot",
    "MistralAI-User",
]


@require_GET
def robots_txt(request):
    sitemap = f"https://{request.get_host()}/sitemap.xml"
    llms_url = f"https://{request.get_host()}/llms.txt"

    lignes = [
        "# Santé Infantile Bénin — robots.txt",
        "# Les assistants IA (LLM) sont les bienvenus sur les pages publiques.",
        f"# Sommaire du site pour les modèles de langage : {llms_url}",
        "# Contenu intégral : https://" + request.get_host() + "/llms-full.txt",
        "",
        "# Règles communes à tous les robots",
        "User-agent: *",
        "Allow: /",
    ]
    lignes += [f"Disallow: {zone}" for zone in PRIVES]

    # Blocs explicites pour les crawlers d'assistants IA
    for bot in BOTS_IA:
        lignes += ["", f"User-agent: {bot}", "Allow: /"]
        lignes += [f"Disallow: {zone}" for zone in PRIVES]

    lignes += ["", f"Sitemap: {sitemap}", ""]
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


@require_GET
def llms_txt(request):
    """Sommaire du site pour les modèles de langage (format llmstxt.org)."""
    return HttpResponse(llms.llms_txt(request), content_type="text/plain; charset=utf-8")


@require_GET
def llms_full_txt(request):
    """Contenu intégral du site pour les modèles de langage (format llmstxt.org)."""
    return HttpResponse(llms.llms_full_txt(request), content_type="text/plain; charset=utf-8")
