"""Generate a synthetic real-estate dataset for Florianópolis and load it.

Deterministic (fixed seed) so the dataset is reproducible. The generated records
are also written to ``data/properties.json`` as the versioned source of truth.

Usage:
    uv run python -m scripts.seed_properties            # generate + load (skip if not empty)
    uv run python -m scripts.seed_properties --reset    # wipe table first
    uv run python -m scripts.seed_properties --count 80
    uv run python -m scripts.seed_properties --json-only # only refresh data/properties.json
"""

import argparse
import json
import random
from pathlib import Path

from sqlalchemy import delete, func, select

from realestate_rag_agent.core.db import SessionLocal
from realestate_rag_agent.repositories.models import Property

SEED = 42
DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "properties.json"

# neighborhood -> (lat, lon, price tier 1..3, typical amenities bias)
NEIGHBORHOODS: dict[str, tuple[float, float, int]] = {
    "Centro": (-27.5954, -48.5480, 2),
    "Trindade": (-27.5905, -48.5222, 2),
    "Córrego Grande": (-27.6010, -48.5090, 2),
    "Itacorubi": (-27.5820, -48.5090, 2),
    "João Paulo": (-27.5680, -48.5150, 3),
    "Agronômica": (-27.5790, -48.5420, 2),
    "Lagoa da Conceição": (-27.6040, -48.4670, 3),
    "Campeche": (-27.6790, -48.4880, 2),
    "Rio Tavares": (-27.6640, -48.4930, 2),
    "Ingleses": (-27.4360, -48.3960, 2),
    "Jurerê": (-27.4390, -48.4960, 3),
    "Canasvieiras": (-27.4280, -48.4620, 2),
    "Santo Antônio de Lisboa": (-27.5070, -48.5230, 3),
    "Coqueiros": (-27.6110, -48.5760, 2),
    "Estreito": (-27.5940, -48.5850, 1),
    "Capoeiras": (-27.6060, -48.5900, 1),
}

STREETS = [
    "Rua das Araucárias",
    "Rua João Pio Duarte Silva",
    "Servidão dos Coqueiros",
    "Avenida das Rendeiras",
    "Rua Lauro Linhares",
    "Rua Deputado Antônio Edu Vieira",
    "Rua Delfino Conti",
    "Avenida Madre Benvenuta",
    "Rua Jornalista Manoel de Menezes",
    "Rua das Gaivotas",
    "Rodovia Armação",
    "Rua Intendente João Nunes Vieira",
]

PROPERTY_TYPES = ["apartment", "house", "studio", "condo", "commercial"]
TYPE_WEIGHTS = [46, 26, 12, 12, 4]

ALL_AMENITIES = [
    "piscina",
    "churrasqueira",
    "academia",
    "salão de festas",
    "playground",
    "portaria 24h",
    "elevador",
    "sacada",
    "vista para o mar",
    "mobiliado",
    "ar-condicionado",
    "aceita pet",
    "energia solar",
    "coworking",
    "quadra",
]

VIEWS = ["vista para o mar", "vista para a lagoa", "vista para o morro", "vista para a cidade"]


def _price(rng: random.Random, operation: str, ptype: str, area: float, tier: int) -> float:
    base_m2 = {1: 6500, 2: 9500, 3: 15000}[tier]
    base_m2 *= {"apartment": 1.0, "condo": 1.05, "house": 0.9, "studio": 1.15, "commercial": 0.8}[
        ptype
    ]
    sale = area * base_m2 * rng.uniform(0.85, 1.2)
    if operation == "sale":
        return round(sale, -3)
    # monthly rent ~ 0.4%–0.6% of sale value
    return round(sale * rng.uniform(0.004, 0.006), -1)


def _description(
    rng: random.Random,
    ptype: str,
    operation: str,
    neighborhood: str,
    bedrooms: int,
    area: float,
    amenities: list[str],
) -> str:
    kind = {
        "apartment": "Apartamento",
        "house": "Casa",
        "studio": "Studio",
        "condo": "Casa em condomínio",
        "commercial": "Sala comercial",
    }[ptype]
    op_txt = "à venda" if operation == "sale" else "para locação"
    intro = rng.choice(
        [
            f"{kind} {op_txt} no bairro {neighborhood}, Florianópolis.",
            f"Excelente {kind.lower()} {op_txt} em {neighborhood}.",
            f"{kind} bem localizado {op_txt}, coração de {neighborhood}.",
        ]
    )
    if ptype == "commercial":
        rooms = f"Espaço de {area:.0f} m² com {bedrooms or 1} ambiente(s)."
    else:
        rooms = rng.choice(
            [
                f"São {bedrooms} dormitório(s) e {area:.0f} m² de área privativa.",
                f"{bedrooms} quarto(s), {area:.0f} m², planta bem aproveitada.",
            ]
        )
    extras = ""
    if amenities:
        extras = " Conta com " + ", ".join(amenities[:-1])
        extras += f" e {amenities[-1]}." if len(amenities) > 1 else f"{amenities[0]}."
        extras = extras.replace("com e", "com")
    closing = rng.choice(
        [
            " Próximo a comércio, praias e linhas de ônibus.",
            " Região tranquila, com boa infraestrutura no entorno.",
            " Ótima oportunidade para morar ou investir.",
        ]
    )
    return f"{intro} {rooms}{extras}{closing}".strip()


def generate(count: int) -> list[dict]:
    rng = random.Random(SEED)
    records: list[dict] = []
    names = list(NEIGHBORHOODS)

    for i in range(count):
        neighborhood = names[i % len(names)] if i < len(names) else rng.choice(names)
        lat, lon, tier = NEIGHBORHOODS[neighborhood]
        ptype = rng.choices(PROPERTY_TYPES, weights=TYPE_WEIGHTS)[0]
        operation = rng.choices(["sale", "rent"], weights=[62, 38])[0]

        if ptype == "studio":
            bedrooms, area = 1, rng.uniform(28, 45)
        elif ptype == "commercial":
            bedrooms, area = 0, rng.uniform(25, 160)
        elif ptype == "house" or ptype == "condo":
            bedrooms, area = rng.randint(2, 5), rng.uniform(90, 320)
        else:
            bedrooms, area = rng.randint(1, 4), rng.uniform(40, 160)
        area = round(area, 1)

        bathrooms = max(1, bedrooms - rng.randint(0, 1)) if ptype != "commercial" else 1
        parking = 0 if ptype == "studio" else min(bedrooms, rng.randint(0, 3))

        n_amen = rng.randint(0, 6)
        amenities = sorted(rng.sample(ALL_AMENITIES, k=n_amen))
        if tier == 3 and rng.random() < 0.6:
            view = rng.choice(VIEWS)
            if view not in amenities:
                amenities.append(view)

        price = _price(rng, operation, ptype, area, tier)
        condo_fee = (
            round(rng.uniform(300, 1600), -1) if ptype in {"apartment", "condo", "studio"} else None
        )
        iptu = round(price * rng.uniform(0.002, 0.006) / (12 if operation == "rent" else 1), -1)

        kind_pt = {
            "apartment": "Apartamento",
            "house": "Casa",
            "studio": "Studio",
            "condo": "Casa em condomínio",
            "commercial": "Sala comercial",
        }[ptype]
        op_pt = "à venda" if operation == "sale" else "para alugar"
        title = (
            f"{kind_pt} {bedrooms}Q {op_pt} em {neighborhood}"
            if bedrooms
            else f"{kind_pt} {op_pt} em {neighborhood}"
        )

        records.append(
            {
                "title": title,
                "description": _description(
                    rng, ptype, operation, neighborhood, bedrooms, area, amenities
                ),
                "operation": operation,
                "property_type": ptype,
                "price": float(price),
                "condo_fee": condo_fee,
                "iptu": float(iptu),
                "bedrooms": bedrooms,
                "bathrooms": bathrooms,
                "parking_spaces": parking,
                "area_m2": area,
                "neighborhood": neighborhood,
                "city": "Florianópolis",
                "state": "SC",
                "latitude": round(lat + rng.uniform(-0.01, 0.01), 6),
                "longitude": round(lon + rng.uniform(-0.01, 0.01), 6),
                "amenities": amenities,
                "street": rng.choice(STREETS),
            }
        )
    return records


def write_json(records: list[dict]) -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load(records: list[dict], *, reset: bool) -> int:
    with SessionLocal() as session:
        if reset:
            session.execute(delete(Property))
            session.commit()
        existing = session.scalar(select(func.count()).select_from(Property))
        if existing:
            print(
                f"properties table already has {existing} rows; skipping load "
                f"(use --reset to overwrite)"
            )
            return 0
        for rec in records:
            payload = {k: v for k, v in rec.items() if k != "street"}
            session.add(Property(**payload))
        session.commit()
        return len(records)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=75)
    parser.add_argument("--reset", action="store_true", help="wipe table before load")
    parser.add_argument("--json-only", action="store_true", help="only refresh data file")
    args = parser.parse_args()

    records = generate(args.count)
    write_json(records)
    print(f"wrote {len(records)} records to {DATA_FILE.relative_to(Path.cwd())}")

    if args.json_only:
        return

    inserted = load(records, reset=args.reset)
    if inserted:
        print(f"inserted {inserted} properties")


if __name__ == "__main__":
    main()
