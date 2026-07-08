import inspect
import textwrap
from itertools import islice
import json
from pathlib import Path

VALID_VIEWS = {
    "summary",
    "public",
    "private",
    "grouped",
    "all",
    "methods",
    "properties",
    "errors",
    "preview",
}

VALID_SEARCH_TARGETS = {
    "name",
    "signature",
    "docstring",
    "type",
    "module",
}

ANSI_STYLES = {
    "yellow": ("\033[93m", "\033[0m"),
    "green": ("\033[92m", "\033[0m"),
    "cyan": ("\033[96m", "\033[0m"),
    "red": ("\033[91m", "\033[0m"),
    "none": ("", ""),
}


def parse_signature(callable_obj):
    signature = inspect.signature(callable_obj)

    parameters = []

    for name, param in signature.parameters.items():
        parameters.append({
            "name": name,
            "kind": str(param.kind),
            "annotation": (
                None
                if param.annotation is inspect.Parameter.empty
                else str(param.annotation)
            ),
            "default": (
                None
                if param.default is inspect.Parameter.empty
                else repr(param.default)
            ),
        })

    return_annotation = (
        None
        if signature.return_annotation is inspect.Signature.empty
        else str(signature.return_annotation)
    )

    return {
        "signature": str(signature),
        "parameters": parameters,
        "return_annotation": return_annotation,
    }


def inspect_object(
    obj,
    include_signatures=True,
    include_docstrings=False,
    include_property_values=False,
    preview_iterable=False,
    preview_limit=5,
):
    info = {
        "object": {
            "type": type(obj).__name__,
            "module": type(obj).__module__,
            "class_name": obj.__class__.__name__,
            "repr": repr(obj),
        },
        "properties": [],
        "methods": [],
        "preview": {
            "enabled": preview_iterable,
            "type": None,
            "items": [],
            "truncated": False,
            "limit": preview_limit,
            "error": None,
        },
        "counts": {
            "properties": 0,
            "methods": 0,
            "errors": 0,
        },
        "errors": [],
    }

    for name in dir(obj):
        is_private = name.startswith("_")

        property_info = {
            "name": name,
            "is_private": is_private,
            "type": None,
            "value_preview": None,
            "accessed": False,
            "error": None,
        }

        method_info = {
            "name": name,
            "is_private": is_private,
            "signature": None,
            "parameters": [],
            "return_annotation": None,
            "docstring": None,
            "error": None,
        }

        try:
            static_attr = inspect.getattr_static(obj, name)
            is_method = callable(static_attr)

            if not is_method:
                try:
                    runtime_attr = getattr(obj, name)
                    is_method = callable(runtime_attr)
                except Exception:
                    is_method = False

            if is_method:
                if include_signatures or include_docstrings:
                    try:
                        runtime_attr = getattr(obj, name)

                        if include_signatures:
                            try:
                                signature_info = parse_signature(runtime_attr)

                                method_info["signature"] = signature_info["signature"]
                                method_info["parameters"] = signature_info["parameters"]
                                method_info["return_annotation"] = signature_info[
                                    "return_annotation"
                                ]

                            except Exception as e:
                                method_info["error"] = f"Signature error: {e}"

                        if include_docstrings:
                            try:
                                method_info["docstring"] = inspect.getdoc(runtime_attr)
                            except Exception as e:
                                method_info["error"] = f"Docstring error: {e}"

                    except Exception as e:
                        method_info["error"] = f"Runtime access error: {e}"

                info["methods"].append(method_info)

            else:
                if include_property_values:
                    try:
                        runtime_attr = getattr(obj, name)
                        property_info["type"] = type(runtime_attr).__name__
                        property_info["value_preview"] = repr(runtime_attr)
                        property_info["accessed"] = True
                    except Exception as e:
                        property_info["error"] = f"Property access error: {e}"
                        info["errors"].append({"name": name, "error": str(e)})
                else:
                    property_info["type"] = type(static_attr).__name__

                info["properties"].append(property_info)

        except Exception as e:
            info["errors"].append({"name": name, "error": str(e)})

    if preview_iterable:
        try:
            iterator = iter(obj)
            preview_items = list(islice(iterator, preview_limit + 1))

            info["preview"]["type"] = "iterable"
            info["preview"]["items"] = preview_items[:preview_limit]
            info["preview"]["truncated"] = len(preview_items) > preview_limit

        except Exception as e:
            info["preview"]["error"] = str(e)

    info["counts"]["properties"] = len(info["properties"])
    info["counts"]["methods"] = len(info["methods"])
    info["counts"]["errors"] = len(info["errors"])

    return info


def shorten(value, max_length=120):
    text = repr(value)
    if len(text) > max_length:
        return text[:max_length] + "..."
    return text


def is_safe_iterable(obj):
    return hasattr(obj, "__iter__") and not isinstance(
        obj, (str, bytes, dict, list, tuple, set)
    )


def print_field(label, value, width=100):
    """
    Print a label/value pair using a hanging indent.

    Wrapped lines start under the value column instead of under the label.
    """
    prefix = f"{label:<10}: "

    wrapped = textwrap.fill(
        str(value),
        width=width,
        initial_indent=prefix,
        subsequent_indent=" " * len(prefix),
    )

    print(wrapped)


def highlight_match(value, query, style="yellow"):
    if value is None:
        return ""

    text = str(value)

    if not query:
        return text

    start, end = ANSI_STYLES.get(style, ANSI_STYLES["yellow"])

    return text.replace(query, f"{start}{query}{end}")


def print_report(info, view="grouped", verbosity="full"):
    if view not in VALID_VIEWS:
        raise ValueError(
            f"Invalid view '{view}'. "
            f"Choose from: {', '.join(sorted(VALID_VIEWS))}"
        )

    valid_verbosity = {"compact", "full"}

    if verbosity not in valid_verbosity:
        raise ValueError(
            f"Invalid verbosity '{verbosity}'. "
            f"Choose from: {', '.join(sorted(valid_verbosity))}"
        )

    obj = info.get("object", {})
    counts = info.get("counts", {})
    preview = info.get("preview", {})
    errors = info.get("errors", [])

    properties = sorted(
        info.get("properties", []),
        key=lambda item: item.get("name", ""),
    )

    methods = sorted(
        info.get("methods", []),
        key=lambda item: item.get("name", ""),
    )

    public_properties = [p for p in properties if not p.get("is_private")]
    private_properties = [p for p in properties if p.get("is_private")]

    public_methods = [m for m in methods if not m.get("is_private")]
    private_methods = [m for m in methods if m.get("is_private")]

    def format_signature(signature):
        """
        Format a method signature based on the selected verbosity.

        compact -> Hide signatures entirely.
        full    -> Show complete signatures.
        """
        if verbosity == "compact":
            return None

        return signature

    def print_header():
        print("\n" + "=" * 80)
        print("OBJECT INSPECTION REPORT")
        print("=" * 80)
        print(f"Type:       {obj.get('type')}")
        print(f"Module:     {obj.get('module')}")
        print(f"Class:      {obj.get('class_name')}")
        print(f"Repr:       {obj.get('repr')}")

    def print_summary():
        print("\nSUMMARY")
        print("-" * 80)
        print(f"Properties: {counts.get('properties', 0)}")
        print(f"Methods:    {counts.get('methods', 0)}")
        print(f"Errors:     {counts.get('errors', 0)}")

    def print_properties(title, items):
        print(f"\n{title} ({len(items)})")
        print("-" * 80)

        if not items:
            print("No properties found.")
            return

        for prop in items:
            print(f"{prop['name']}  ({prop.get('type')})")

            if prop.get("accessed"):
                print(f"    accessed: {prop.get('accessed')}")
                print(f"    preview:  {prop.get('value_preview')}")

            if prop.get("error"):
                print(f"    error:    {prop.get('error')}")

    def print_methods(title, items):
        print(f"\n{title} ({len(items)})")
        print("-" * 80)

        if not items:
            print("No methods found.")
            return

        # ------------------------------------------------------------------
        # Method Summary
        # ------------------------------------------------------------------
        method_names = [method["name"] for method in items]

        wrapper = textwrap.TextWrapper(
            width=76,
            initial_indent="    ",
            subsequent_indent="    ",
        )

        print()
        print("{")

        summary = ", ".join(method_names)

        for line in wrapper.wrap(summary):
            print(line)

        print("}")
        print()
        print("-" * 80)

        # ------------------------------------------------------------------
        # Detailed Method Information
        # ------------------------------------------------------------------
        for method in items:
            print()

            print_field("name", method.get("name"))

            if verbosity == "full":
                parameters = method.get("parameters", [])

                if parameters:
                    print("parameters:")

                    for param in parameters:
                        name = param.get("name")
                        annotation = param.get("annotation")
                        default = param.get("default")
                        kind = param.get("kind")

                        line = name

                        if annotation:
                            line += f": {annotation}"

                        if default:
                            line += f" = {default}"

                        if kind and kind != "POSITIONAL_OR_KEYWORD":
                            line += f"  [{kind}]"

                        print_field("", line)

                elif method.get("signature"):
                    print_field("signature", method.get("signature"))

                if method.get("return_annotation"):
                    print_field("returns", method.get("return_annotation"))

                if method.get("docstring"):
                    print_field("docstring", method.get("docstring"))

            if method.get("error"):
                print_field("error", method.get("error"))

    def print_preview():
        print("\nITERABLE PREVIEW")
        print("-" * 80)

        if not preview.get("enabled"):
            print("Preview disabled.")
            return

        if preview.get("error"):
            print(f"Preview error: {preview.get('error')}")
            return

        print(f"Type:      {preview.get('type')}")
        print(f"Limit:     {preview.get('limit')}")
        print(f"Truncated: {preview.get('truncated')}")

        items = preview.get("items", [])

        if not items:
            print("No preview items found.")
            return

        for index, item in enumerate(items, start=1):
            print(f"{index}. {item}")

    def print_errors():
        print("\nERRORS")
        print("-" * 80)

        if not errors:
            print("No errors reported.")
            return

        for error in errors:
            print(f"{error.get('name')}: {error.get('error')}")

    print_header()

    if view == "summary":
        print_summary()

    elif view == "public":
        print_summary()
        print_properties("PUBLIC PROPERTIES", public_properties)
        print_methods("PUBLIC METHODS", public_methods)

    elif view == "private":
        print_summary()
        print_properties("PRIVATE PROPERTIES", private_properties)
        print_methods("PRIVATE METHODS", private_methods)

    elif view == "grouped":
        print_summary()
        print_properties("PUBLIC PROPERTIES", public_properties)
        print_methods("PUBLIC METHODS", public_methods)
        print_properties("PRIVATE PROPERTIES", private_properties)
        print_methods("PRIVATE METHODS", private_methods)
        print_preview()
        print_errors()

    elif view == "all":
        print_summary()
        print_properties("ALL PROPERTIES", properties)
        print_methods("ALL METHODS", methods)
        print_preview()
        print_errors()

    elif view == "methods":
        print_summary()
        print_methods("PUBLIC METHODS", public_methods)
        print_methods("PRIVATE METHODS", private_methods)

    elif view == "properties":
        print_summary()
        print_properties("PUBLIC PROPERTIES", public_properties)
        print_properties("PRIVATE PROPERTIES", private_properties)

    elif view == "errors":
        print_summary()
        print_errors()

    elif view == "preview":
        print_summary()
        print_preview()

    print("=" * 80)


def print_object(info, view="grouped", verbosity="full"):
    print_report(info, view=view, verbosity=verbosity)


def explore(obj, view="grouped", verbosity="full", **kwargs):
    info = inspect_object(obj, **kwargs)
    print_report(info, view=view, verbosity=verbosity)
    return info


def search_report(
    info,
    query,
    search_in=("name", "signature", "docstring"),
    include_private=True,
):
    invalid_targets = set(search_in) - VALID_SEARCH_TARGETS

    if invalid_targets:
        raise ValueError(
            f"Invalid search targets: {sorted(invalid_targets)}. "
            f"Choose from: {sorted(VALID_SEARCH_TARGETS)}"
        )

    query = query.lower()

    matches = {
        "properties": [],
        "methods": [],
    }

    def matches_query(item):
        for target in search_in:
            value = item.get(target)

            if value is not None and query in str(value).lower():
                return True

        return False

    for prop in info.get("properties", []):
        if not include_private and prop.get("is_private"):
            continue

        if matches_query(prop):
            matches["properties"].append(prop)

    for method in info.get("methods", []):
        if not include_private and method.get("is_private"):
            continue

        if matches_query(method):
            matches["methods"].append(method)

    return matches


def print_search_results(
    results,
    query,
    search_in=("name", "signature", "docstring"),
    verbosity="compact",
    highlight_style="yellow",
    width=100,
):
    properties = results.get("properties", [])
    methods = results.get("methods", [])

    print("\n" + "=" * 80)
    print("SEARCH RESULTS")
    print("=" * 80)
    print(f"Search For : {query}")
    print(f"Search In  : {', '.join(search_in)}")
    print(f"Properties : {len(properties)}")
    print(f"Methods    : {len(methods)}")
    print("=" * 80)

    print(f"\nPROPERTIES ({len(properties)})")
    print("-" * 80)

    if properties:
        for prop in properties:
            print()

            if "name" in search_in:
                name = highlight_match(
                    prop.get("name"),
                    query,
                    style=highlight_style,
                )
                print_field("name", name, width=width)

            if "type" in search_in:
                obj_type = highlight_match(
                    prop.get("type"),
                    query,
                    style=highlight_style,
                )
                print_field("type", obj_type, width=width)

            if "module" in search_in:
                module = highlight_match(
                    prop.get("module"),
                    query,
                    style=highlight_style,
                )
                print_field("module", module, width=width)

            if verbosity == "full" and prop.get("value_preview"):
                value = highlight_match(
                    prop.get("value_preview"),
                    query,
                    style=highlight_style,
                )
                print_field("value", value, width=width)
    else:
        print("No matching properties found.")

    print(f"\nMETHODS ({len(methods)})")
    print("-" * 80)

    if methods:
        for method in methods:
            print()

            if "name" in search_in:
                name = highlight_match(
                    method.get("name"),
                    query,
                    style=highlight_style,
                )
                print_field("name", name, width=width)

            if "signature" in search_in and verbosity == "full":
                signature = highlight_match(
                    method.get("signature"),
                    query,
                    style=highlight_style,
                )
                print_field("signature", signature, width=width)

            if "docstring" in search_in and verbosity == "full":
                docstring = highlight_match(
                    method.get("docstring"),
                    query,
                    style=highlight_style,
                )
                print_field("docstring", docstring, width=width)

            if "module" in search_in:
                module = highlight_match(
                    method.get("module"),
                    query,
                    style=highlight_style,
                )
                print_field("module", module, width=width)
    else:
        print("No matching methods found.")

    print("=" * 80)


def print_report_and_return_public_methods(info, view="public", verbosity="full"):
    print_report(info, view=view, verbosity=verbosity)
    return get_public_methods(info)


def print_method_report(method):
    print("\n" + "=" * 80)
    print(f"METHOD REPORT: {method.get('name')}")
    print("=" * 80)

    print_field("name", method.get("name"))

    parameters = method.get("parameters", [])

    if parameters:
        print("parameters:")

        for param in parameters:
            name = param.get("name")
            annotation = param.get("annotation")
            default = param.get("default")
            kind = param.get("kind")

            line = name

            if annotation:
                line += f": {annotation}"

            if default:
                line += f" = {default}"

            if kind and kind != "POSITIONAL_OR_KEYWORD":
                line += f"  [{kind}]"

            print_field("", line)

    elif method.get("signature"):
        print_field("signature", method.get("signature"))

    if method.get("return_annotation"):
        print_field("returns", method.get("return_annotation"))

    if method.get("docstring"):
        print_field("docstring", method.get("docstring"))

    if method.get("error"):
        print_field("error", method.get("error"))

    print("=" * 80)


def print_method_tree(info, include_private=False):
    tree = build_method_tree(info, include_private=include_private)

    print("\n" + "=" * 80)
    print("METHOD TREE")
    print("=" * 80)

    obj = tree["object"]

    print(f"{obj.get('class_name')}  ({obj.get('module')})")
    print("|")

    methods = tree.get("methods", [])

    for index, method in enumerate(methods):
        is_last = index == len(methods) - 1
        branch = "└──" if is_last else "├──"

        print(f"{branch} {method.get('name')}")

        if method.get("return_annotation"):
            child_branch = "    " if is_last else "│   "
            print(f"{child_branch}returns -> {method.get('return_annotation')}")

    print("=" * 80)

    return tree


def run_method_discovery(info):
    public_methods = print_report_and_return_public_methods(
        info,
        view="public",
        verbosity="full",
    )

    for method in public_methods:
        print_method_report(method)

    tree = print_method_tree(info)

    return tree


def get_public_methods(info):
    return [
        method
        for method in info.get("methods", [])
        if not method.get("is_private")
    ]


def normalize_annotation(annotation):
    if annotation is None:
        return None

    text = str(annotation)

    if text == "None":
        return "None"

    if text in {"typing.Self", "Self"}:
        return "Self"

    if text.startswith("<class '") and text.endswith("'>"):
        full_name = text.removeprefix("<class '").removesuffix("'>")
        return full_name.split(".")[-1]

    if text.startswith("typing."):
        return text.replace("typing.", "")

    if "." in text:
        return text.split(".")[-1]

    return text


def build_method_tree(info):
    obj = info.get("object", {})
    methods = info.get("methods", [])

    public_methods = {}
    private_methods = {}

    for method in methods:

        method_info = {
            "signature": method.get("signature"),
            "parameters": [
                {
                    "name": param.get("name"),
                    "kind": param.get("kind"),
                    "annotation": param.get("annotation"),
                    "type": normalize_annotation(
                        param.get("annotation")
                    ),
                    "default": param.get("default"),
                    "required": (
                        param.get("default") is None
                        and param.get("kind") not in {
                            "VAR_POSITIONAL",
                            "VAR_KEYWORD",
                        }
                    ),
                }
                for param in method.get("parameters", [])
            ],
            "return": {
                "annotation": method.get("return_annotation"),
                "type": normalize_annotation(
                    method.get("return_annotation")
                ),
                "category": categorize_return_annotation(
                    method.get("return_annotation")
                ),
            },
        }

        if method.get("is_private"):
            private_methods[method["name"]] = method_info
        else:
            public_methods[method["name"]] = method_info

    return {
        "object": {
            "type": obj.get("type"),
            "module": obj.get("module"),
            "class_name": obj.get("class_name"),
        },
        "methods": {
            "public": public_methods,
            "private": private_methods,
        },
    }


def save_json(storage_map, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(storage_map, file, indent=4, ensure_ascii=False)

    print(f"✓ Saved storage map to: {output_path}")


def to_hierarchy(data):
    """
    Convert explorer data into a labeled hierarchy.

    Any list of dictionaries that all contain a "name" key becomes
    a dictionary keyed by each item's name.

    Example:
        [{"name": "upload_blob", "returns": "..."}]

    becomes:
        {"upload_blob": {"returns": "..."}}
    """

    if isinstance(data, dict):
        return {
            key: to_hierarchy(value)
            for key, value in data.items()
        }

    if isinstance(data, list):
        if all(isinstance(item, dict) and "name" in item for item in data):
            return {
                item["name"]: to_hierarchy({
                    key: value
                    for key, value in item.items()
                    if key != "name"
                })
                for item in data
            }

        return [
            to_hierarchy(item)
            for item in data
        ]

    return data


def build_azure_blob_storage_map(blob, container_name, blob_path):
    storage_map = {}

    service_info = inspect_object(blob)
    storage_map["BlobServiceClient"] = build_method_tree(service_info)

    container = blob.get_container_client(container_name)
    container_info = inspect_object(container)
    storage_map["ContainerClient"] = build_method_tree(container_info)

    blob_client = blob.get_blob_client(
        container=container_name,
        blob=blob_path,
    )
    blob_info = inspect_object(blob_client)
    storage_map["BlobClient"] = build_method_tree(blob_info)

    save_json(
        storage_map,
        "data/object_explorer/azure_blob_storage_map.json",
    )

    hierarchy = to_hierarchy(storage_map)

    save_json(
        hierarchy,
        "data/object_explorer/azure_blob_storage_hierarchy.json",
    )

    return storage_map, hierarchy


def build_object_map(*objects, map_output_path=None, hierarchy_output_path=None, ):
    object_map = {}

    for obj in objects:
        info = inspect_object(obj)
        object_name = type(obj).__name__

        object_map[object_name] = build_method_tree(info)

    if map_output_path:
        save_json(object_map, map_output_path)

    hierarchy = to_hierarchy(object_map)

    if hierarchy_output_path:
        save_json(hierarchy, hierarchy_output_path)

    return object_map, hierarchy


def categorize_return_annotation(annotation):
    if annotation is None:
        return "not_annotated"

    text = str(annotation)

    if text == "None":
        return "void"

    if text in {"typing.Self", "Self"}:
        return "self"

    if text in {"<class 'str'>", "<class 'int'>", "<class 'float'>", "<class 'bool'>", "<class 'bytes'>"}:
        return "primitive"

    if "typing.Dict" in text or text.startswith("Dict["):
        return "dictionary"

    if "typing.List" in text or text.startswith("List["):
        return "list"

    if "typing.Tuple" in text or text.startswith("Tuple["):
        return "tuple"

    if "typing.Iterator" in text or text.startswith("Iterator["):
        return "iterator"

    if "ItemPaged" in text:
        return "paged_collection"

    if "typing.Union" in text or text.startswith("Union["):
        return "union"

    if text.startswith("<class '") and text.endswith("'>"):
        return "object"

    return "object"


# Under imports add this: from src.utils.object_explorer import build_object_map
# Run this to Create the object map and hierarchy for the given objects.
# build_object_map(
#         s3,
#         map_output_path="data/object_explorer/s3_map.json",
#         hierarchy_output_path="data/object_explorer/s3_hierarchy.json",
#     )
# S3 is the object being explored to build the object map and hierarchy.
# Then you can define the output location for the object map and hierarchy JSON files.
