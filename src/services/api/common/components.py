from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    ClassVar,
    TypeVar,
    final,
    override,
)

from dmr.components import BodyComponent, QueryComponent

if TYPE_CHECKING:
    from dmr.controller import Controller
    from dmr.endpoint import Endpoint
    from dmr.serializer import BaseSerializer

_DocsT = TypeVar("_DocsT")


@final
class BodyDocsComponent(BodyComponent):
    """Show the body model in the API docs, never parse or check the body."""

    __slots__ = ()
    context_name: ClassVar[str] = "body_docs"

    @override
    def provide_context_data(
        self,
        endpoint: Endpoint,
        controller: Controller[BaseSerializer],
        *,
        field_model: Any,
    ) -> Any:
        """Give the defaults: OpenRouter alone judges the raw bytes."""
        return {}


@final
class QueryDocsComponent(QueryComponent):
    """Show the query model in the API docs, never parse or check the query."""

    __slots__ = ()
    context_name: ClassVar[str] = "query_docs"

    @override
    def provide_context_data(
        self,
        endpoint: Endpoint,
        controller: Controller[BaseSerializer],
        *,
        field_model: Any,
    ) -> Any:
        """Give the defaults: OpenRouter alone judges the raw query."""
        return {}


# The model must have defaults only: it is filled with nothing
BodyDocs = Annotated[_DocsT, BodyDocsComponent()]
QueryDocs = Annotated[_DocsT, QueryDocsComponent()]
