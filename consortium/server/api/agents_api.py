from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer

import consortium.server.server_singletons as server_singletons
from consortium.server.exceptions.api_exceptions.agents_api_exceptions import (
    AgentNotFoundError as AgentNotFoundAPIError,
    AgentResultNotFoundError as AgentResultNotFoundAPIError,
    AgentTaskNotFoundError as AgentTaskNotFoundAPIError,
)
from consortium.server.exceptions.api_exceptions.http_exceptions import (
    ForbiddenError,
    InternalServerErrorError,
    MethodNotAllowedError,
    UnauthorizedError,
    UnprocessableEntityError,
)
from consortium.server.exceptions.service_exceptions.agents_service_exceptions import (
    AgentNotFoundError as AgentNotFoundServiceError,
    AgentResultNotFoundError as AgentResultNotFoundServiceError,
    AgentTaskNotFoundError as AgentTaskNotFoundServiceError,
)
from consortium.server.models.agent_models import (
    AgentModel,
    AgentResultModel,
    AgentTaskModel,
)

# TODO: Move away from the request body model to an inline definition
# from consortium.server.models.request_body_models import AgentTaskRequestBodyModel
from consortium.server.objects.user_account_objects import UserPermissions
from consortium.server.server_dependencies import AuthorizeUserRequest

router = APIRouter(
    prefix="/api/agents",
    responses={
        401: {"model": UnauthorizedError().to_pydantic_model()},
        403: {"model": ForbiddenError().to_pydantic_model()},
        405: {"model": MethodNotAllowedError().to_pydantic_model()},
        500: {"model": InternalServerErrorError().to_pydantic_model()},
    },
    tags=["Agents API"],
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")
agents_service = server_singletons.agents_service


@router.get(
    "/all",
    responses={
        200: {"model": list[AgentModel]},
    },
)
def get_all_agents(
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.READ_ALL_AGENTS)),
    ],
):
    return [AgentModel(**agent.to_json()) for agent in agents_service.get_all_agents()]


@router.get(
    "/{agent_id}",
    responses={
        200: {"model": AgentModel},
        404: {
            "model": AgentNotFoundAPIError.from_service_exception(
                service_exception=AgentNotFoundServiceError(agent_id="string"),
            ).to_pydantic_model(),
        },
        422: {
            "model": UnprocessableEntityError(
                detail=[{"loc": ["string", 0], "msg": "string", "type": "string"}],
            ).to_pydantic_model(),
        },
    },
)
def get_agent_by_agent_id(
    agent_id: str,
    _: Annotated[
        None,
        Depends(
            AuthorizeUserRequest(UserPermissions.READ_AGENT_BY_AGENT_ID),
        ),
    ],
):
    try:
        return AgentModel(
            **agents_service.get_agent_by_agent_id(agent_id).to_json(),
        )
    except AgentNotFoundServiceError as exc:
        raise AgentNotFoundAPIError.from_service_exception(service_exception=exc)


# TODO: Implement the rest of the API resources under the new exception system.
# @router.get(
#     "/{agent_id}/tasks",
#     responses={
#         200: {"model": list[AgentTaskModel]},
#         404: {"model": AgentNotFoundError(agent_id="string").to_pydantic_model()},
#     },
# )
# def get_all_agent_tasks_by_agent_id(
#     agent_id: str,
#     _: Annotated[
#         None,
#         Depends(
#             AuthorizeUserRequest(UserPermissions.READ_ALL_AGENT_TASKS_BY_AGENT_ID),
#         ),
#     ],
# ) -> list[AgentTaskModel]:
#     try:
#         agent = agents_service.get_agent_by_agent_id(agent_id)
#     except ValueError:
#         raise AgentNotFoundError(agent_id=agent_id)
#
#     return agent.get_all_tasks()
#
#
# @router.get(
#     "/{agent_id}/tasks/queued",
#     responses={
#         200: {"model": list[AgentTaskModel]},
#         404: {"model": AgentNotFoundError(agent_id="string").to_pydantic_model()},
#     },
# )
# def get_all_queued_agent_tasks_by_agent_id(
#     agent_id: str,
#     _: Annotated[
#         None,
#         Depends(
#             AuthorizeUserRequest(UserPermissions.READ_ALL_AGENT_TASKS_BY_AGENT_ID),
#         ),
#     ],
# ) -> list[AgentTaskModel]:
#     try:
#         agent = agents_service.get_agent_by_agent_id(agent_id)
#     except ValueError:
#         raise AgentNotFoundError(agent_id=agent_id)
#
#     return agent.peek_all_queued_tasks()
#
#
# @router.get(
#     "/{agent_id}/tasks/running",
#     responses={
#         200: {"model": list[AgentTaskModel]},
#         404: {"model": AgentNotFoundError(agent_id="string").to_pydantic_model()},
#     },
# )
# def get_all_running_agent_tasks_by_agent_id(
#     agent_id: str,
#     _: Annotated[
#         None,
#         Depends(
#             AuthorizeUserRequest(UserPermissions.READ_ALL_AGENT_TASKS_BY_AGENT_ID),
#         ),
#     ],
# ) -> list[AgentTaskModel]:
#     try:
#         agent = agents_service.get_agent_by_agent_id(agent_id)
#     except ValueError:
#         raise AgentNotFoundError(agent_id=agent_id)
#
#     return agent.get_all_running_tasks()
#
#
# @router.get(
#     "/{agent_id}/tasks/completed",
#     responses={
#         200: {"model": list[AgentTaskModel]},
#         404: {"model": AgentNotFoundError(agent_id="string").to_pydantic_model()},
#     },
# )
# def get_all_completed_agent_tasks_by_agent_id(
#     agent_id: str,
#     _: Annotated[
#         None,
#         Depends(
#             AuthorizeUserRequest(UserPermissions.READ_ALL_AGENT_TASKS_BY_AGENT_ID),
#         ),
#     ],
# ) -> list[AgentTaskModel]:
#     try:
#         agent = agents_service.get_agent_by_agent_id(agent_id)
#     except ValueError:
#         raise AgentNotFoundError(agent_id=agent_id)
#
#     return agent.get_all_completed_tasks()
#
#
# @router.get(
#     "/{agent_id}/tasks/{task_id}",
#     responses={
#         200: {"model": AgentTaskModel},
#         404: {
#             "model": AgentNotFoundError(agent_id="string").to_pydantic_model()
#             | AgentTaskNotFoundError(
#                 task_id="string",
#             ).to_pydantic_model(),
#         },
#     },
# )
# def get_agent_tasks_by_agent_id_and_task_id(
#     agent_id: str,
#     task_id: str,
#     _: Annotated[
#         None,
#         Depends(
#             AuthorizeUserRequest(UserPermissions.READ_ALL_AGENT_TASKS_BY_AGENT_ID),
#         ),
#     ],
# ) -> AgentTaskModel:
#     try:
#         agent = agents_service.get_agent_by_agent_id(agent_id)
#     except ValueError:
#         raise AgentNotFoundError(agent_id=agent_id)
#
#     try:
#         task = agent.get_task_by_task_id(task_id)
#     except ValueError:
#         raise AgentTaskNotFoundError(task_id=task_id)
#
#     return task
#
#
# @router.post(
#     "/{agent_id}/tasks",
#     responses={
#         200: {"model": AgentTaskModel},
#         404: {"model": AgentNotFoundError(agent_id="string").to_pydantic_model()},
#     },
# )
# def task_agent_by_agent_id(
#     agent_id: str,
#     agent_task_request_body: AgentTaskRequestBodyModel,
#     _: Annotated[
#         None,
#         Depends(
#             AuthorizeUserRequest(UserPermissions.TASK_AGENT_BY_AGENT_ID),
#         ),
#     ],
# ) -> AgentTaskModel:
#     try:
#         agent = agents_service.get_agent_by_agent_id(agent_id)
#     except ValueError:
#         raise AgentNotFoundError(agent_id=agent_id)
#
#     agent_task = AgentTaskModel(**agent_task_request_body.dict())
#     agent.add_task(agent_task)
#
#     return agent_task
#
#
# @router.get(
#     "/{agent_id}/results",
#     responses={
#         200: {"model": list[AgentResultModel]},
#         404: {"model": AgentNotFoundError(agent_id="string").to_pydantic_model()},
#     },
# )
# def get_all_agent_results_by_agent_id(
#     agent_id: str,
#     _: Annotated[
#         None,
#         Depends(
#             AuthorizeUserRequest(UserPermissions.READ_ALL_AGENT_RESULTS_BY_AGENT_ID),
#         ),
#     ],
# ) -> list[AgentResultModel]:
#     try:
#         agent = agents_service.get_agent_by_agent_id(agent_id)
#     except ValueError:
#         raise AgentNotFoundError(agent_id=agent_id)
#
#     return agent.get_all_results()
#
#
# @router.get(
#     "/{agent_id}/results/{task_id_or_result_id}",
#     responses={
#         200: {"model": AgentResultModel},
#         404: {
#             "model": AgentNotFoundError(agent_id="string").to_pydantic_model()
#             | AgentResultNotFoundError(
#                 task_id_or_result_id="string",
#             ).to_pydantic_model(),
#         },
#     },
# )
# def get_agent_result_by_agent_id_and_task_id_or_result_id(
#     agent_id: str,
#     task_id_or_result_id: str,
#     _: Annotated[
#         None,
#         Depends(
#             AuthorizeUserRequest(
#                 UserPermissions.READ_AGENT_RESULT_BY_AGENT_ID_AND_TASK_ID_OR_RESULT_ID,
#             ),
#         ),
#     ],
# ) -> AgentResultModel:
#     try:
#         agent = agents_service.get_agent_by_agent_id(agent_id)
#     except ValueError:
#         raise AgentNotFoundError(agent_id=agent_id)
#
#     try:
#         result = agent.get_result_by_task_id(
#             agent_id=agent_id,
#             task_id_or_result_id=task_id_or_result_id,
#         )
#     except ValueError:
#         try:
#             result = agent.get_result_by_result_id(
#                 agent_id=agent_id,
#                 task_id_or_result_id=task_id_or_result_id,
#             )
#         except ValueError:
#             raise AgentResultNotFoundError(
#                 task_id_or_result_id=task_id_or_result_id,
#             )
#
#     return result
#
#
# @router.get(
#     "/{agent_id}/results/success",
#     responses={
#         200: {"model": AgentResultModel},
#         404: {
#             "model": AgentNotFoundError(agent_id="string").to_pydantic_model(),
#         },
#     },
# )
# def get_all_successful_agent_results_by_agent_id(
#     agent_id: str,
#     _: Annotated[
#         None,
#         Depends(
#             AuthorizeUserRequest(
#                 UserPermissions.READ_ALL_AGENT_RESULTS_BY_AGENT_ID,
#             ),
#         ),
#     ],
# ) -> list[AgentResultModel]:
#     try:
#         agent = agents_service.get_agent_by_agent_id(agent_id)
#     except ValueError:
#         raise AgentNotFoundError(agent_id=agent_id)
#
#     return agent.get_all_successful_results()
#
#
# @router.get(
#     "/{agent_id}/results/fail",
#     responses={
#         200: {"model": AgentResultModel},
#         404: {
#             "model": AgentNotFoundError(agent_id="string").to_pydantic_model(),
#         },
#     },
# )
# def get_all_failed_agent_results_by_agent_id(
#     agent_id: str,
#     _: Annotated[
#         None,
#         Depends(
#             AuthorizeUserRequest(
#                 UserPermissions.READ_ALL_AGENT_RESULTS_BY_AGENT_ID,
#             ),
#         ),
#     ],
# ) -> list[AgentResultModel]:
#     try:
#         agent = agents_service.get_agent_by_agent_id(agent_id)
#     except ValueError:
#         raise AgentNotFoundError(agent_id=agent_id)
#
#     return agent.get_all_failed_results()
#
#
# @router.get(
#     "/{agent_id}/results/error",
#     responses={
#         200: {"model": AgentResultModel},
#         404: {
#             "model": AgentNotFoundError(agent_id="string").to_pydantic_model(),
#         },
#     },
# )
# def get_all_errored_agent_results_by_agent_id(
#     agent_id: str,
#     _: Annotated[
#         None,
#         Depends(
#             AuthorizeUserRequest(
#                 UserPermissions.READ_ALL_AGENT_RESULTS_BY_AGENT_ID,
#             ),
#         ),
#     ],
# ) -> list[AgentResultModel]:
#     try:
#         agent = agents_service.get_agent_by_agent_id(agent_id)
#     except ValueError:
#         raise AgentNotFoundError(agent_id=agent_id)
#
#     return agent.get_all_errored_results()
