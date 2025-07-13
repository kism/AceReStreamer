"""XC Category Mapping."""

import csv
from pathlib import Path

from bidict import bidict

from acerestreamer.utils.logger import get_logger

from .models import XCCategory

logger = get_logger(__name__)


class CategoryXCCategoryIDMapping:
    """A class to manage the mapping between category names and XC category IDs."""

    def __init__(self) -> None:
        """Initialize the mapping."""
        self.category_id_mapping: bidict[str, int] = bidict()
        self.config_path: Path | None = None

    def load_config(self, instance_path: str | Path) -> None:
        """Load the category name to XC category ID mapping from a csv file."""
        if isinstance(instance_path, str):
            instance_path = Path(instance_path)
        self.config_path = instance_path / "category_xc_id_map.csv"

        if not self.config_path.exists():
            return

        with self.config_path.open("r", encoding="utf-8") as file:
            reader = csv.reader(file)
            for row in reader:
                if len(row) == 2:  # noqa: PLR2004
                    category_name, xc_category_id = row
                    if xc_category_id.isdigit():
                        self.category_id_mapping[category_name] = int(xc_category_id)
                    else:
                        logger.warning(
                            "Invalid XC ID in mapping: %s, %s",
                            category_name,
                            xc_category_id,
                        )

    def _save_config(self) -> None:
        """Save the category name to XC category ID mapping to a CSV file."""
        if self.config_path is None:
            logger.error("Instance path is not set. Cannot save configuration.")
            return

        with self.config_path.open("w", encoding="utf-8") as file:
            writer = csv.writer(file)
            for category_name, xc_id in self.category_id_mapping.items():
                writer.writerow([category_name, xc_id])

    def _get_next_xc_category_id(self) -> int:
        """Get the next available XC category ID."""
        if not self.category_id_mapping:
            return 1
        return max(self.category_id_mapping.values()) + 1

    def get_xc_category_id(self, category_name: str) -> int:
        """Get the XC category ID for a given category name."""
        if category_name in self.category_id_mapping:
            return self.category_id_mapping[category_name]

        # If the category name is not found, create a new XC category ID
        new_xc_category_id = self._get_next_xc_category_id()
        self.category_id_mapping[category_name] = new_xc_category_id
        self._save_config()
        return new_xc_category_id

    def get_category_name(self, xc_category_id: int) -> str | None:
        """Get the category name for a given XC category ID."""
        if xc_category_id in self.category_id_mapping.inverse:
            return self.category_id_mapping.inverse[xc_category_id]
        return None

    def get_all_categories_api(self, categories_in_use: set[int] | None) -> list[XCCategory]:
        """Get all categories as a list of XCCategory objects."""
        if categories_in_use is None:
            categories_in_use = set()


        logger.info("Fetching all categories with IDs in use: %s", categories_in_use)
        # return [
        #     XCCategory(category_name=category_name, category_id=str(xc_category_id))
        #     for category_name, xc_category_id in self.category_id_mapping.items()
        #     if not categories_in_use or xc_category_id in categories_in_use
        # ]

        returnt = []
        for category_name, xc_category_id in self.category_id_mapping.items():
            condition_1 = categories_in_use is None
            condition_2 = xc_category_id in categories_in_use
            logger.info(
                "Checking category '%s' with ID '%s': condition_1=%s, condition_2=%s",
                category_name,
                xc_category_id,
                condition_1,
                condition_2,
            )
            if condition_1 or condition_2:
                returnt.append(XCCategory(category_name=category_name, category_id=str(xc_category_id)))
        return returnt
