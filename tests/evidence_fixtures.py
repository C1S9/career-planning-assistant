"""Synthetic primary-source excerpts for offline request-boundary tests."""

from evidence import EvidenceBundle, Source


def ready_evidence():
    return EvidenceBundle(
        status="ready", query="career planning skills assessment", checked_at="2026-10-23T00:00:00Z",
        sources=(Source(id="S1", title="Career exploration", url="https://www.careeronestop.org/ExploreCareers/explore-careers.aspx",
                        excerpt="Identify skills and compare career options before choosing a direction.", published_date=None),),
        note="Primary-source excerpts retrieved; accuracy and personal suitability need judgment.",
    )


def no_evidence():
    return EvidenceBundle(status="unavailable", query="career planning", checked_at="2026-10-23T00:00:00Z",
                          sources=(), note="Search was unavailable. No source-grounded recommendation was generated.")
