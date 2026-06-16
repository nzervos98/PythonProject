from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

try:
    import yaml
except ImportError as exc:
    raise RuntimeError(exc) from exc

# Το import γίνεται tolerant για να δουλεύει και ως module και ως απλό script.
try:
    from .models import init_db, Supermarket, CanonicalTaxonomy, SourceTaxonomyMapping
except ImportError:
    try:
        from marketscraper.models import init_db, Supermarket, CanonicalTaxonomy, SourceTaxonomyMapping
    except ImportError:
        from marketscraper.marketscraper.models import (
            init_db,
            Supermarket,
            CanonicalTaxonomy,
            SourceTaxonomyMapping,
        )

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG_PATH = BASE_DIR / "taxonomy.yaml"
DEFAULT_DB_PATH = BASE_DIR / "market_product.db"


@dataclass(frozen=True)
class CanonicalRow:
    category_code: str
    category_label: str
    subcategory_code: str | None
    subcategory_label: str | None
    sort_order: int


@dataclass(frozen=True)
class SourceMappingRow:
    supermarket_name: str
    source_category: str
    source_subcategory: str | None
    canonical_category_code: str
    canonical_subcategory_code: str | None
    mapping_type: str
    notes: str | None


def normalize_optional_text(value: Any) -> str | None:
    """Κρατάει το None ως None και καθαρίζει κείμενο από έξτρα κενά."""
    if value is None:
        return None
    value = str(value).replace("\xa0", " ")
    value = " ".join(value.strip().split())
    return value or None


def load_yaml_config(config_path: str | os.PathLike[str]) -> dict[str, Any]:
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Δεν βρέθηκε το taxonomy YAML: {path}")

    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}

    if not isinstance(data, dict):
        raise ValueError("Το taxonomy YAML πρέπει να έχει root object/dict.")

    return data


def parse_canonical_reference(value: Any) -> tuple[str, str | None]:
    """
    Δέχεται είτε string τύπου "category/subcategory" είτε dict:
        canonical: fresh_food/fruits
    ή:
        canonical:
          category: fresh_food
          subcategory: fruits
    """
    if isinstance(value, str):
        parts = value.split("/", 1)
        category_code = normalize_optional_text(parts[0])
        subcategory_code = normalize_optional_text(parts[1]) if len(parts) == 2 else None
    elif isinstance(value, dict):
        category_code = normalize_optional_text(value.get("category") or value.get("category_code"))
        subcategory_code = normalize_optional_text(value.get("subcategory") or value.get("subcategory_code"))
    else:
        raise ValueError(f"Άκυρο canonical reference: {value!r}")

    if not category_code:
        raise ValueError(f"Λείπει canonical category στο reference: {value!r}")

    return category_code, subcategory_code


def iter_canonical_rows(data: dict[str, Any]) -> Iterable[CanonicalRow]:
    for category in data.get("canonical_taxonomy", []):
        category_code = normalize_optional_text(category.get("code") or category.get("category_code"))
        category_label = normalize_optional_text(category.get("label") or category.get("category_label"))

        if not category_code or not category_label:
            raise ValueError(f"Canonical category με ελλιπή στοιχεία: {category!r}")

        for subcategory in category.get("subcategories", []):
            subcategory_code = normalize_optional_text(subcategory.get("code") or subcategory.get("subcategory_code"))
            subcategory_label = normalize_optional_text(subcategory.get("label") or subcategory.get("subcategory_label"))
            sort_order = int(subcategory.get("sort_order") or 0)

            if not subcategory_code or not subcategory_label:
                raise ValueError(
                    f"Canonical subcategory με ελλιπή στοιχεία στην κατηγορία {category_code}: {subcategory!r}"
                )

            yield CanonicalRow(
                category_code=category_code,
                category_label=category_label,
                subcategory_code=subcategory_code,
                subcategory_label=subcategory_label,
                sort_order=sort_order,
            )


def iter_source_mapping_rows(data: dict[str, Any]) -> Iterable[SourceMappingRow]:
    source_mappings = data.get("source_mappings", {})
    if not isinstance(source_mappings, dict):
        raise ValueError("Το source_mappings πρέπει να είναι dict με κλειδιά τα supermarket names.")

    for supermarket_name, category_groups in source_mappings.items():
        supermarket_name = normalize_optional_text(supermarket_name)
        if not supermarket_name:
            raise ValueError("Βρέθηκε source_mappings entry χωρίς supermarket name.")

        for category_group in category_groups or []:
            source_category = normalize_optional_text(category_group.get("source_category"))
            if not source_category:
                raise ValueError(f"Mapping group χωρίς source_category στο {supermarket_name}: {category_group!r}")

            for mapping in category_group.get("mappings", []):
                source_subcategory = normalize_optional_text(mapping.get("source_subcategory"))
                canonical_category_code, canonical_subcategory_code = parse_canonical_reference(mapping.get("canonical"))

                yield SourceMappingRow(
                    supermarket_name=supermarket_name,
                    source_category=source_category,
                    source_subcategory=source_subcategory,
                    canonical_category_code=canonical_category_code,
                    canonical_subcategory_code=canonical_subcategory_code,
                    mapping_type=normalize_optional_text(mapping.get("type")) or "exact_pair",
                    notes=normalize_optional_text(mapping.get("notes")),
                )


def validate_config(data: dict[str, Any]) -> tuple[list[str], list[CanonicalRow], list[SourceMappingRow]]:
    supermarkets = [normalize_optional_text(name) for name in data.get("supermarkets", [])]
    supermarkets = [name for name in supermarkets if name]
    if not supermarkets:
        raise ValueError("Το YAML πρέπει να έχει τουλάχιστον ένα supermarket στο `supermarkets`.")

    canonical_rows = list(iter_canonical_rows(data))
    if not canonical_rows:
        raise ValueError("Το YAML πρέπει να έχει τουλάχιστον μία canonical taxonomy γραμμή.")

    mapping_rows = list(iter_source_mapping_rows(data))

    canonical_keys: set[tuple[str, str | None]] = set()
    for row in canonical_rows:
        key = (row.category_code, row.subcategory_code)
        if key in canonical_keys:
            raise ValueError(f"Διπλό canonical taxonomy key: {row.category_code}/{row.subcategory_code}")
        canonical_keys.add(key)

    mapping_keys: set[tuple[str, str, str | None]] = set()
    for row in mapping_rows:
        if row.supermarket_name not in supermarkets:
            raise ValueError(
                f"Το source_mappings έχει supermarket `{row.supermarket_name}` που δεν υπάρχει στη λίστα supermarkets."
            )

        canonical_key = (row.canonical_category_code, row.canonical_subcategory_code)
        if canonical_key not in canonical_keys:
            raise ValueError(
                f"Το mapping `{row.supermarket_name}: {row.source_category} / {row.source_subcategory}` "
                f"δείχνει σε άγνωστο canonical `{row.canonical_category_code}/{row.canonical_subcategory_code}`."
            )

        mapping_key = (row.supermarket_name, row.source_category, row.source_subcategory)
        if mapping_key in mapping_keys:
            raise ValueError(
                f"Διπλό source mapping: {row.supermarket_name} / {row.source_category} / {row.source_subcategory}"
            )
        mapping_keys.add(mapping_key)

    return supermarkets, canonical_rows, mapping_rows


def upsert_supermarkets(session, supermarket_names: list[str]) -> dict[str, int]:
    for supermarket_name in supermarket_names:
        supermarket = session.query(Supermarket).filter_by(name=supermarket_name).first()
        if supermarket is None:
            session.add(Supermarket(name=supermarket_name))

    session.commit()

    return {
        supermarket.name: supermarket.id
        for supermarket in session.query(Supermarket).filter(Supermarket.name.in_(supermarket_names)).all()
    }


def upsert_canonical_taxonomy(session, rows: list[CanonicalRow]) -> dict[tuple[str, str | None], int]:
    inserted = 0
    updated = 0

    for row in rows:
        taxonomy = session.query(CanonicalTaxonomy).filter_by(
            category_code=row.category_code,
            subcategory_code=row.subcategory_code,
        ).first()

        if taxonomy is None:
            taxonomy = CanonicalTaxonomy(
                category_code=row.category_code,
                subcategory_code=row.subcategory_code,
            )
            session.add(taxonomy)
            inserted += 1
        else:
            updated += 1

        taxonomy.category_label = row.category_label
        taxonomy.subcategory_label = row.subcategory_label
        taxonomy.sort_order = row.sort_order
        taxonomy.is_active = 1

    session.commit()

    print(f"Canonical taxonomy: {inserted} inserts, {updated} updates.")

    return {
        (taxonomy.category_code, taxonomy.subcategory_code): taxonomy.id
        for taxonomy in session.query(CanonicalTaxonomy).filter(CanonicalTaxonomy.is_active == 1).all()
    }


def upsert_source_mappings(
    session,
    rows: list[SourceMappingRow],
    supermarkets_index: dict[str, int],
    taxonomy_index: dict[tuple[str, str | None], int],
) -> None:
    inserted = 0
    updated = 0

    for row in rows:
        supermarket_id = supermarkets_index[row.supermarket_name]
        canonical_id = taxonomy_index[(row.canonical_category_code, row.canonical_subcategory_code)]

        mapping = session.query(SourceTaxonomyMapping).filter_by(
            supermarket_id=supermarket_id,
            source_category=row.source_category,
            source_subcategory=row.source_subcategory,
        ).first()

        if mapping is None:
            mapping = SourceTaxonomyMapping(
                supermarket_id=supermarket_id,
                source_category=row.source_category,
                source_subcategory=row.source_subcategory,
            )
            session.add(mapping)
            inserted += 1
        else:
            updated += 1

        mapping.canonical_taxonomy_id = canonical_id
        mapping.mapping_type = row.mapping_type
        mapping.notes = row.notes
        mapping.is_active = 1

    session.commit()

    print(f"Source mappings: {inserted} inserts, {updated} updates.")


def seed_taxonomy(config_path: str | os.PathLike[str], db_path: str | os.PathLike[str], validate_only: bool = False) -> None:
    data = load_yaml_config(config_path)
    supermarket_names, canonical_rows, mapping_rows = validate_config(data)

    print(
        "Loaded taxonomy YAML: "
        f"{len(supermarket_names)} supermarkets, "
        f"{len(canonical_rows)} canonical rows, "
        f"{len(mapping_rows)} source mappings."
    )

    if validate_only:
        print("Validation OK. Δεν έγινε καμία αλλαγή στη βάση.")
        return

    db_path = Path(db_path)
    init_db(str(db_path))

    engine = create_engine(f"sqlite:///{db_path}")
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        supermarkets_index = upsert_supermarkets(session, supermarket_names)
        taxonomy_index = upsert_canonical_taxonomy(session, canonical_rows)
        upsert_source_mappings(session, mapping_rows, supermarkets_index, taxonomy_index)
    finally:
        session.close()

    print("Taxonomy seed completed.")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Seed taxonomy tables from taxonomy.yaml")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="Path στο taxonomy.yaml")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="Path στο SQLite DB file")
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Κάνει μόνο validation στο YAML χωρίς να γράψει στη βάση.",
    )
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    seed_taxonomy(config_path=args.config, db_path=args.db, validate_only=args.validate_only)


if __name__ == "__main__":
    main()
