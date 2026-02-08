"""CRUD Editor page for all database entities."""

import subprocess
import sys
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any, get_args, get_origin

import streamlit as st

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

st.set_page_config(page_title="Editor - Fusion Research", page_icon="✏️", layout="wide")


def get_running_port() -> int:
    import socket
    for port in range(8511, 8520):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.1)
                if s.connect_ex(("localhost", port)) == 0:
                    return port
        except Exception:
            continue
    return 8511


# Sidebar: entity selector + safe exit
with st.sidebar:
    st.markdown("### Editor")
    entity_types = [
        "companies", "funding", "technologies", "markets",
        "partnerships", "investors", "collaborations",
    ]
    selected_type = st.selectbox("Entity Type", entity_types, format_func=str.title)

    st.markdown("---")
    if st.button("Exit App", type="secondary"):
        port = get_running_port()
        st.warning(f"Shutting down app on port {port}...")
        subprocess.run(
            f"lsof -ti:{port} | xargs -r kill -9",
            shell=True, capture_output=True,
        )
        st.stop()

st.title("✏️ Database Editor")

try:
    from src.data.database import get_database
    from src.services.crud_service import CrudService, ENTITY_CONFIG

    db = get_database()
    crud = CrudService(db)

    model_cls = crud.get_model_class(selected_type)
    label = crud.get_label(selected_type)
    company_names = crud.get_company_names()

    # ── Helper: build form fields from Pydantic model ──

    def _get_enum_class(annotation):
        """Extract Enum class from an annotation like Optional[MyEnum]."""
        if isinstance(annotation, type) and issubclass(annotation, Enum):
            return annotation
        origin = get_origin(annotation)
        if origin is not None:
            for arg in get_args(annotation):
                if isinstance(arg, type) and issubclass(arg, Enum):
                    return arg
        return None

    def _is_optional(annotation):
        origin = get_origin(annotation)
        if origin is not None:
            args = get_args(annotation)
            return type(None) in args
        return False

    def _base_type(annotation):
        """Get the base type, unwrapping Optional."""
        origin = get_origin(annotation)
        if origin is not None:
            for arg in get_args(annotation):
                if arg is not type(None):
                    return arg
        return annotation

    def render_form(model_cls, defaults: dict | None = None, key_prefix: str = "form"):
        """Render a dynamic form based on Pydantic model fields. Returns field values dict."""
        defaults = defaults or {}
        values = {}

        for field_name, field_info in model_cls.model_fields.items():
            if field_name in ("id", "last_updated"):
                continue

            annotation = field_info.annotation
            base = _base_type(annotation)
            enum_cls = _get_enum_class(annotation)
            default_val = defaults.get(field_name, field_info.default)
            field_key = f"{key_prefix}_{field_name}"

            # FK fields with company selector
            if field_name in ("company_id", "company_id_a", "company_id_b"):
                options = list(company_names.keys())
                labels = {k: f"{v} (#{k})" for k, v in company_names.items()}

                if field_name == "company_id_b":
                    options = [None] + options
                    labels[None] = "-- None --"

                current = default_val
                if current and current in options:
                    idx = options.index(current)
                else:
                    idx = 0

                chosen = st.selectbox(
                    field_name.replace("_", " ").title(),
                    options=options,
                    index=idx,
                    format_func=lambda x: labels.get(x, str(x)),
                    key=field_key,
                )
                values[field_name] = chosen
                continue

            # Enum fields
            if enum_cls is not None:
                options_list = list(enum_cls)
                current = default_val
                if isinstance(current, str):
                    try:
                        current = enum_cls(current)
                    except ValueError:
                        current = options_list[0]
                elif current is None:
                    current = options_list[0]

                idx = options_list.index(current) if current in options_list else 0
                chosen = st.selectbox(
                    field_name.replace("_", " ").title(),
                    options=options_list,
                    index=idx,
                    format_func=lambda x: x.value if hasattr(x, "value") else str(x),
                    key=field_key,
                )
                values[field_name] = chosen
                continue

            # Date fields
            if base is date:
                val = default_val
                if isinstance(val, str):
                    try:
                        val = date.fromisoformat(val)
                    except ValueError:
                        val = None
                values[field_name] = st.date_input(
                    field_name.replace("_", " ").title(),
                    value=val,
                    key=field_key,
                )
                continue

            # Numeric fields
            if base in (int, float):
                val = default_val
                if val is None:
                    val = 0 if base is int else 0.0
                if base is int:
                    values[field_name] = st.number_input(
                        field_name.replace("_", " ").title(),
                        value=int(val), step=1, key=field_key,
                    )
                else:
                    values[field_name] = st.number_input(
                        field_name.replace("_", " ").title(),
                        value=float(val), step=0.01, format="%.2f", key=field_key,
                    )
                continue

            # Text fields
            val = default_val if default_val is not None else ""
            if isinstance(val, datetime):
                val = val.isoformat()
            val = str(val) if val else ""

            # Use text_area for long fields
            long_fields = (
                "description", "trl_justification", "competitive_positioning",
                "key_investors", "key_partnerships", "key_materials",
                "key_challenges", "growth_drivers", "regulatory_environment",
                "key_deliverables", "key_outcomes", "notes", "all_investors",
                "portfolio_focus",
            )
            if field_name in long_fields:
                values[field_name] = st.text_area(
                    field_name.replace("_", " ").title(),
                    value=val, key=field_key,
                )
            else:
                values[field_name] = st.text_input(
                    field_name.replace("_", " ").title(),
                    value=val, key=field_key,
                )

        return values

    def clean_values(values: dict, model_cls) -> dict:
        """Clean form values: convert empty strings to None, etc."""
        cleaned = {}
        for field_name, val in values.items():
            field_info = model_cls.model_fields.get(field_name)
            if field_info is None:
                continue
            annotation = field_info.annotation
            base = _base_type(annotation)
            optional = _is_optional(annotation)

            if isinstance(val, str) and val.strip() == "" and optional:
                cleaned[field_name] = None
            elif isinstance(val, Enum):
                cleaned[field_name] = val
            elif base in (int,) and optional and val == 0:
                cleaned[field_name] = None
            elif base in (float,) and optional and val == 0.0:
                cleaned[field_name] = None
            else:
                cleaned[field_name] = val
        return cleaned

    # ── Mode management ──
    mode = st.session_state.get("editor_mode", "list")
    edit_id = st.session_state.get("editor_edit_id")

    if mode == "list":
        # LIST MODE
        col1, col2 = st.columns([6, 1])
        with col1:
            st.subheader(f"{label} Records")
        with col2:
            if st.button("+ New", type="primary"):
                st.session_state.editor_mode = "create"
                st.session_state.editor_edit_id = None
                st.rerun()

        entities = crud.list_entities(selected_type)
        if not entities:
            st.info(f"No {label.lower()} records found.")
        else:
            # Build table data
            rows = []
            for e in entities:
                d = e.model_dump()
                row = {"ID": d.get("id", "")}
                # Add key display fields
                for key in ("name", "company_id", "institution_name", "partner_name",
                            "region_name", "stage", "approach"):
                    if key in d:
                        display_val = d[key]
                        if key == "company_id" and display_val in company_names:
                            display_val = company_names[display_val]
                        if isinstance(display_val, Enum):
                            display_val = display_val.value
                        row[key.replace("_", " ").title()] = display_val
                rows.append(row)

            st.dataframe(rows, use_container_width=True, hide_index=True)

            # Edit / Delete controls
            st.markdown("---")
            col_e, col_d = st.columns(2)
            with col_e:
                edit_target = st.number_input("Edit ID", min_value=1, step=1, key="edit_id_input")
                if st.button("Edit"):
                    st.session_state.editor_mode = "edit"
                    st.session_state.editor_edit_id = int(edit_target)
                    st.rerun()
            with col_d:
                del_target = st.number_input("Delete ID", min_value=1, step=1, key="del_id_input")
                if st.button("Delete", type="secondary"):
                    st.session_state.editor_mode = "confirm_delete"
                    st.session_state.editor_edit_id = int(del_target)
                    st.rerun()

    elif mode == "create":
        st.subheader(f"Create New {label}")
        if st.button("Cancel"):
            st.session_state.editor_mode = "list"
            st.rerun()

        with st.form("create_form"):
            values = render_form(model_cls, key_prefix="create")
            submitted = st.form_submit_button("Create", type="primary")

        if submitted:
            try:
                cleaned = clean_values(values, model_cls)
                new_id = crud.create_entity(selected_type, cleaned)
                st.success(f"Created {label} with ID {new_id}")
                st.session_state.editor_mode = "list"
                st.rerun()
            except Exception as e:
                st.error(f"Validation error: {e}")

    elif mode == "edit" and edit_id is not None:
        entity = crud.get_entity(selected_type, edit_id)
        if entity is None:
            st.error(f"{label} with ID {edit_id} not found.")
            if st.button("Back"):
                st.session_state.editor_mode = "list"
                st.rerun()
        else:
            st.subheader(f"Edit {label} #{edit_id}")
            if st.button("Cancel"):
                st.session_state.editor_mode = "list"
                st.rerun()

            defaults = entity.model_dump()

            with st.form("edit_form"):
                values = render_form(model_cls, defaults=defaults, key_prefix="edit")
                submitted = st.form_submit_button("Save Changes", type="primary")

            if submitted:
                try:
                    cleaned = clean_values(values, model_cls)
                    ok = crud.update_entity(selected_type, edit_id, cleaned)
                    if ok:
                        st.success(f"Updated {label} #{edit_id}")
                        st.session_state.editor_mode = "list"
                        st.rerun()
                    else:
                        st.error("Update failed.")
                except Exception as e:
                    st.error(f"Validation error: {e}")

    elif mode == "confirm_delete" and edit_id is not None:
        entity = crud.get_entity(selected_type, edit_id)
        if entity is None:
            st.error(f"{label} with ID {edit_id} not found.")
        else:
            st.warning(f"Are you sure you want to delete {label} #{edit_id}?")
            name_field = getattr(entity, "name", None) or getattr(entity, "partner_name", None) or getattr(entity, "institution_name", None)
            if name_field:
                st.write(f"**{name_field}**")

            col_y, col_n = st.columns(2)
            with col_y:
                if st.button("Yes, Delete", type="primary"):
                    ok = crud.delete_entity(selected_type, edit_id)
                    if ok:
                        st.success(f"Deleted {label} #{edit_id}")
                    else:
                        st.error("Delete failed.")
                    st.session_state.editor_mode = "list"
                    st.session_state.editor_edit_id = None
                    st.rerun()
            with col_n:
                if st.button("Cancel"):
                    st.session_state.editor_mode = "list"
                    st.session_state.editor_edit_id = None
                    st.rerun()

except Exception as e:
    st.error(f"Error: {e}")
    st.exception(e)
