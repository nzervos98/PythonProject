from .models import SourceTaxonomyMapping, CanonicalTaxonomy


def resolve_canonical_taxonomy(session, supermarket_id, source_category, source_subcategory):
    source_category = (source_category or "").strip()
    source_subcategory = (source_subcategory or "").strip()

    if not source_category:
        return None

    # 1. exact pair match
    exact_mapping = (
        session.query(SourceTaxonomyMapping)
        .join(
            CanonicalTaxonomy,
            SourceTaxonomyMapping.canonical_taxonomy_id == CanonicalTaxonomy.id
        )
        .filter(
            SourceTaxonomyMapping.supermarket_id == supermarket_id,
            SourceTaxonomyMapping.source_category == source_category,
            SourceTaxonomyMapping.source_subcategory == source_subcategory,
            SourceTaxonomyMapping.is_active == 1,
            CanonicalTaxonomy.is_active == 1,
        )
        .first()
    )

    if exact_mapping:
        return exact_mapping.canonical_taxonomy

    # 2. fallback category-level match
    fallback_mapping = (
        session.query(SourceTaxonomyMapping)
        .join(
            CanonicalTaxonomy,
            SourceTaxonomyMapping.canonical_taxonomy_id == CanonicalTaxonomy.id
        )
        .filter(
            SourceTaxonomyMapping.supermarket_id == supermarket_id,
            SourceTaxonomyMapping.source_category == source_category,
            SourceTaxonomyMapping.source_subcategory.is_(None),
            SourceTaxonomyMapping.is_active == 1,
            CanonicalTaxonomy.is_active == 1,
        )
        .first()
    )

    if fallback_mapping:
        return fallback_mapping.canonical_taxonomy

    return None

#normalize text by replacing non-breaking spaces with regular spaces and collapsing multiple spaces into one
def normalize_taxonomy_text(value):
    if value is None:
        return None
    value = value.replace("\xa0", " ")
    value = " ".join(value.strip().split())
    return value