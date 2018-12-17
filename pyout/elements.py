"""Style elements and schema validation.
"""

from __future__ import unicode_literals

from collections import Mapping

schema = {
    "definitions": {
        # Plain style elements
        "align": {
            "description": "Alignment of text",
            "type": "string",
            "enum": ["left", "right", "center"],
            "default": "left",
            "scope": "column"},
        "bold": {
            "description": "Whether text is bold",
            "oneOf": [{"type": "boolean"},
                      {"$ref": "#/definitions/lookup"},
                      {"$ref": "#/definitions/interval"}],
            "default": False,
            "scope": "field"},
        "color": {
            "description": "Foreground color of text",
            "oneOf": [{"type": "string",
                       "enum": ["black", "red", "green", "yellow",
                                "blue", "magenta", "cyan", "white"]},
                      {"$ref": "#/definitions/lookup"},
                      {"$ref": "#/definitions/interval"}],
            "default": "black",
            "scope": "field"},
        "underline": {
            "description": "Whether text is underlined",
            "oneOf": [{"type": "boolean"},
                      {"$ref": "#/definitions/lookup"},
                      {"$ref": "#/definitions/interval"}],
            "default": False,
            "scope": "field"},
        "width": {
            "description": "Width of field",
            "oneOf": [{"type": "integer"},
                      {"type": "string",
                       "enum": ["auto"]},
                      {"type": "object",
                       "properties": {
                           "max": {"type": ["integer", "null"]},
                           "min": {"type": ["integer", "null"]},
                           "width": {"type": "integer"},
                           "marker": {"type": ["string", "boolean"]}},
                       "additionalProperties": False}],
            "default": "auto",
            "scope": "column"},
        # Other style elements
        "aggregate": {
            "description": """A function that produces a summary value.  This
            function will be called with all of the column's the (unprocessed)
            field values and should return a single value to be displayed.""",
            "scope": "column"},
        "delayed": {
            "description": """Don't wait for this column's value.
            The accessor will be wrapped in a function and called
            asynchronously.  This can be set to a string to mark columns as
            part of a "group".  All columns within a group will be accessed
            within the same callable.  True means to access the column's value
            in its own callable (i.e. independently of other columns).""",
            "type": ["boolean", "string"],
            "scope": "field"},
        "missing": {
            "description": "Text to display for missing values",
            "type": "string",
            "default": "",
            "scope": "column"
        },
        "transform": {
            "description": """An arbitrary function.
            This function will be called with the (unprocessed) field value as
            the single argument and should return a transformed value.  Note:
            This function should not have side-effects because it may be called
            multiple times.""",
            "scope": "field"},
        # Complete list of column style elements
        "styles": {
            "type": "object",
            "properties": {"aggregate": {"$ref": "#/definitions/aggregate"},
                           "align": {"$ref": "#/definitions/align"},
                           "bold": {"$ref": "#/definitions/bold"},
                           "color": {"$ref": "#/definitions/color"},
                           "delayed": {"$ref": "#/definitions/delayed"},
                           "missing": {"$ref": "#/definitions/missing"},
                           "transform": {"$ref": "#/definitions/transform"},
                           "underline": {"$ref": "#/definitions/underline"},
                           "width": {"$ref": "#/definitions/width"}},
            "additionalProperties": False},
        # Mapping elements
        "interval": {
            "description": "Map a value within an interval to a style",
            "type": "object",
            "properties": {"interval":
                           {"type": "array",
                            "items": [
                                {"type": "array",
                                 "items": [{"type": ["number", "null"]},
                                           {"type": ["number", "null"]},
                                           {"type": ["string", "boolean"]}],
                                 "additionalItems": False}]}},
            "additionalProperties": False},
        "lookup": {
            "description": "Map a value to a style",
            "type": "object",
            "properties": {"lookup": {"type": "object"}},
            "additionalProperties": False}
    },
    "type": "object",
    "properties": {
        "aggregate_": {
            "description": "Shared attributes for the summary rows",
            "oneOf": [{"type": "object",
                       "properties":
                       {"color": {"$ref": "#/definitions/color"},
                        "bold": {"$ref": "#/definitions/bold"},
                        "underline": {"$ref": "#/definitions/underline"}}},
                      {"type": "null"}],
            "default": {},
            "scope": "table"},
        "default_": {
            "description": "Default style of columns",
            "oneOf": [{"$ref": "#/definitions/styles"},
                      {"type": "null"}],
            "default": {"align": "left",
                        "width": "auto"},
            "scope": "table"},
        "header_": {
            "description": "Attributes for the header row",
            "oneOf": [{"type": "object",
                       "properties":
                       {"color": {"$ref": "#/definitions/color"},
                        "bold": {"$ref": "#/definitions/bold"},
                        "underline": {"$ref": "#/definitions/underline"}}},
                      {"type": "null"}],
            "default": None,
            "scope": "table"},
        "separator_": {
            "description": "Separator used between fields",
            "type": "string",
            "default": " ",
            "scope": "table"},
        "width_": {
            "description": """Total width of table.
            This is typically not set directly by the user.""",
            "default": 90,
            "type": "integer",
            "scope": "table"}
    },
    # All other keys are column names.
    "additionalProperties": {"$ref": "#/definitions/styles"}
}


def default(prop):
    """Return the default value schema property.

    Parameters
    ----------
    prop : str
        A key for schema["properties"]
    """
    return schema["properties"][prop]["default"]


def adopt(style, new_style):
    if new_style is None:
        return style

    combined = {}
    for key, value in style.items():
        if isinstance(value, Mapping):
            combined[key] = dict(value, **new_style.get(key, {}))
        else:
            combined[key] = new_style.get(key, value)
    return combined


class StyleError(Exception):
    """Style is invalid or mispecified in some way.
    """
    pass


class StyleValidationError(StyleError):
    """Exception raised if the style schema does not validate.
    """
    def __init__(self, original_exception):
        msg = ("Invalid style\n\n{}\n\n\n"
               "See pyout.schema for style definition."
               .format(original_exception))
        super(StyleValidationError, self).__init__(msg)


def validate(style):
    """Check `style` against pyout.styling.schema.

    Parameters
    ----------
    style : dict
        Style object to validate.

    Raises
    ------
    StyleValidationError if `style` is not valid.
    """
    try:
        import jsonschema
    except ImportError:
        return

    try:
        jsonschema.validate(style, schema)
    except jsonschema.ValidationError as exc:
        new_exc = StyleValidationError(exc)
        # Don't dump the original jsonschema exception because it is already
        # included in the StyleValidationError's message.
        new_exc.__cause__ = None
        raise new_exc
