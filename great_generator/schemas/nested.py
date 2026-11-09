"""Flatten nested relational specifications into flat tables and relationships."""

from collections.abc import Mapping
from typing import Any


def flatten_nested_spec(nested_spec: Mapping[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """
    Flatten a hierarchical nested dictionary into a flat tables dictionary
    and a list of relationships.

    Args:
        nested_spec: The nested specification.

    Returns:
        A tuple of (tables_dict, relationships_list).

    Raises:
        ValueError: If a table specification is missing the 'schema' key.
    """
    tables = {}
    relationships = []

    def walk(node: Mapping[str, Any], parent_name: str | None = None):
        for table_name, spec in node.items():
            if not isinstance(spec, dict):
                raise ValueError(f"Table specification for '{table_name}' must be a dictionary.")

            if "schema" not in spec:
                raise ValueError(f"Table '{table_name}' is missing the required 'schema' key.")

            # Copy spec to avoid mutating the input
            table_spec = dict(spec)
            children = table_spec.pop("children", {})

            # Handle FK and Schema Injection
            if parent_name:
                # Determine FK column name
                fk_col = table_spec.get("fk", f"{parent_name}_id")

                # Inject FK into schema if not present
                schema = table_spec["schema"]
                # Simple check for presence of column name in schema string
                # (e.g. "id int, name string")
                if fk_col not in schema:
                    # Append the FK column.
                    # We assume 'int' as a safe default for ID columns.
                    # In a real system, we might look at the parent's PK type.
                    schema = f"{schema}, {fk_col} int"
                    table_spec["schema"] = schema

                # Add relationship
                # Format: "parent_table.pk -> child_table.fk"
                # We assume the parent PK is {parent_name}_id or the primary key defined.
                # For generate_relational, the format is often "parent_table.pk -> child_table.fk"
                # or a dict. Let's use the simple string format.
                # Note: the parent PK is typically inferred by great-generator
                # from the schema if not explicit.
                # We'll use the convention: "parent_table.pk -> child_table.fk"
                # where .pk is often omitted or implied.
                # Actually, generate_relational's relationships list can take
                # "parent_table.id -> child_table.parent_id".
                # We'll use a simple "parent -> child" if the system supports it,
                # but the prompt says "wire to the parent's primary key".
                # Let's use the format: "parent_table.pk -> child_table.fk"
                # We'll assume the parent's PK is its own id (e.g. faculty_id).
                parent_pk = f"{parent_name}_id"
                relationships.append(f"{parent_name}.{parent_pk} -> {table_name}.{fk_col}")

            # Store the flattened table spec
            tables[table_name] = table_spec

            # Recurse into children
            walk(children, parent_name=table_name)

    walk(nested_spec)
    return tables, relationships
