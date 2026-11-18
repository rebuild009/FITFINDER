"""Command line helpers.

    python -m app.cli init-db              create tables
    python -m app.cli seed [real|demo]     load the real-store catalog (default) or the synthetic demo
    python -m app.cli ingest FILE [FILE]   load scraper output
    python -m app.cli stats                product counts
"""

import sys

from sqlalchemy import func, select

from .db import SessionLocal, init_db
from .ingest import CATALOGS, ingest_file
from .models import Product


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 1
    cmd, args = argv[0], argv[1:]
    init_db()
    with SessionLocal() as session:
        if cmd == "init-db":
            print("Tables ready.")
        elif cmd == "seed":
            print(ingest_file(session, CATALOGS[args[0] if args else "real"]))
        elif cmd == "ingest":
            for path in args:
                print(path, ingest_file(session, path))
        elif cmd == "stats":
            rows = session.execute(
                select(Product.source, Product.store, func.count()).group_by(Product.source, Product.store)
            ).all()
            for source, store, n in rows:
                print(f"{source:8} {store:30} {n}")
        else:
            print(__doc__)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
