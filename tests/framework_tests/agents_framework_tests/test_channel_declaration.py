import pytest

from consortium.framework._core.framework_exceptions.agent_capabilities_framework_exceptions import (
    DuplicateAgentCapabilityChannelNameError,
    EmptyAgentCapabilityChannelNameError,
    InvalidAgentCapabilityChannelConfigurationParameterTypeError,
    InvalidAgentCapabilityConfigurationParameterTypeError,
)
from consortium.framework.agents.base_agent_capability import BaseAgentCapability
from consortium.framework.agents.channels import Channel, ChannelDirection

# A channel declaration is inert: everything here is about what a capability class says
# it offers, resolved at definition time. Nothing in this module runs a capability or
# touches the buffers the declarations produce.


def test_a_channel_defaults_to_a_plain_text_content_type():
    channel = Channel(name="stdout", direction=ChannelDirection.OUTPUT)

    assert channel.name == "stdout"
    assert channel.direction is ChannelDirection.OUTPUT
    assert channel.content_type == "text/plain"


def test_a_direction_given_as_its_string_value_is_normalized():
    # Declarations are written by hand, so the string form is accepted, but everything
    # downstream compares against the enum.
    channel = Channel(name="stdout", direction="OUTPUT")

    assert channel.direction is ChannelDirection.OUTPUT


def test_an_empty_channel_name_is_rejected():
    with pytest.raises(EmptyAgentCapabilityChannelNameError):
        Channel(name="", direction=ChannelDirection.OUTPUT)


def test_a_parameter_of_the_wrong_type_is_rejected():
    with pytest.raises(InvalidAgentCapabilityChannelConfigurationParameterTypeError):
        Channel(name=1, direction=ChannelDirection.OUTPUT)

    with pytest.raises(InvalidAgentCapabilityChannelConfigurationParameterTypeError):
        Channel(name="stdout", direction=ChannelDirection.OUTPUT, content_type=1)


def test_a_direction_outside_the_enum_is_rejected():
    with pytest.raises(InvalidAgentCapabilityChannelConfigurationParameterTypeError):
        Channel(name="stdout", direction="SIDEWAYS")


def test_to_json_reports_the_declaration():
    channel = Channel(
        name="download",
        direction=ChannelDirection.OUTPUT,
        content_type="application/octet-stream",
    )

    assert channel.to_json() == {
        "name": "download",
        "direction": "OUTPUT",
        "content_type": "application/octet-stream",
    }


def test_declared_channels_become_a_name_keyed_dict():
    stdout = Channel(name="stdout", direction=ChannelDirection.OUTPUT)
    stdin = Channel(name="stdin", direction=ChannelDirection.INPUT)

    class _Interactive(BaseAgentCapability):
        name = "interactive_cmd"
        channels = {stdout, stdin}

    assert _Interactive.channels == {"stdout": stdout, "stdin": stdin}


def test_a_capability_declaring_no_channels_gets_an_empty_mapping():
    class _Plain(BaseAgentCapability):
        name = "plain_cmd"

    assert _Plain.channels == {}
    assert _Plain.to_json()["channels"] == {}


def test_duplicate_channel_names_are_rejected():
    with pytest.raises(DuplicateAgentCapabilityChannelNameError):

        class _Duplicated(BaseAgentCapability):
            name = "duplicated_cmd"
            channels = {
                Channel(name="stdout", direction=ChannelDirection.OUTPUT),
                Channel(name="stdout", direction=ChannelDirection.INPUT),
            }


def test_channels_of_the_wrong_type_are_rejected():
    with pytest.raises(InvalidAgentCapabilityConfigurationParameterTypeError):

        class _NotChannels(BaseAgentCapability):
            name = "not_channels_cmd"
            channels = {"stdout"}


def test_a_capability_subclass_inherits_the_parent_declarations():
    # The parent's set has already been rewritten into a dict by the time the subclass is
    # defined, so the declarations have to be taken back off it rather than iterated as
    # names.
    stdout = Channel(name="stdout", direction=ChannelDirection.OUTPUT)

    class _Parent(BaseAgentCapability):
        name = "parent_cmd"
        channels = {stdout}

    class _Child(_Parent):
        name = "child_cmd"

    assert _Child.channels == {"stdout": stdout}


def test_to_json_surfaces_the_declarations_for_discovery():
    class _Streaming(BaseAgentCapability):
        name = "streaming_cmd"
        channels = {Channel(name="stdout", direction=ChannelDirection.OUTPUT)}

    assert _Streaming.to_json()["channels"] == {
        "stdout": {
            "name": "stdout",
            "direction": "OUTPUT",
            "content_type": "text/plain",
        }
    }
