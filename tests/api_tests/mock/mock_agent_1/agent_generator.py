from consortium.framework.agents import BaseAgentGenerator, BaseAgentGeneratorBuildStep


class MockBuildStep(BaseAgentGeneratorBuildStep):
    name = "Mock Build"
    description = "Blocks until the generator is stopped; no actual build occurs."

    async def build(self, parameters: dict) -> None:
        await self.stop_event.wait()


class AgentGenerator(BaseAgentGenerator):
    agent_generator_build_steps = [MockBuildStep]
