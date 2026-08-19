from consortium.framework.options import SingleValueOption

# The metadata every mock component declares, in the form an author writes it. The tests
# assert against these constants rather than repeating literals, so that a test failure
# reads as "the framework changed what it does with this declaration" rather than "a
# literal drifted".
DECLARED_DESCRIPTION = (
    "Mock component used to exercise the metadata declaration system."
)
DECLARED_VERSION = "0.1.0"
DECLARED_FRAMEWORK_VERSION = ">=0.1.0a1"
DECLARED_DEPENDENCY = "consortium.plugins.mock_dependency==1.0.0"
DECLARED_AUTHORS = frozenset({"test"})
DECLARED_OPTION_NAME = "timeout"
DECLARED_OPTION_DEFAULT = 30
# A real technique ID: the capability metadata resolves declared IDs against the MITRE
# data set at class definition time, so an unknown ID would fail to resolve.
DECLARED_MITRE_TECHNIQUE = "T1082"


# Returned from a function rather than shared as a module level constant: each domain
# rebinds `cls.options` during validation, and a per-component set keeps one domain's
# normalization from being visible to another.
def declared_options() -> set[SingleValueOption]:
    return {
        SingleValueOption(
            name=DECLARED_OPTION_NAME,
            description="Mock option used to exercise options normalization.",
            required=True,
            default_value=DECLARED_OPTION_DEFAULT,
            value_type=int,
        ),
    }


# Declared with exactly one parameter: the templates and capabilities check the signature
# and reject anything else.
def declared_validating_function(parameters) -> None:
    return None
