"""CLI: clean exports → data/warehouse + DQ report."""

from wwe_data.warehouse.quality import write_data_quality_report


def main() -> None:
    write_data_quality_report()


if __name__ == "__main__":
    main()
