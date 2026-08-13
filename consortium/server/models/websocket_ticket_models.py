from pydantic import BaseModel


# The response body of the websocket ticket issuing endpoint (POST /api/ws/ticket). The
# time to live travels with the ticket so a client is told how long the ticket stays
# redeemable rather than hardcoding a window that the server is free to retune. The value
# is always sourced from `TICKET_TIME_TO_LIVE_SECONDS` in the websocket tickets service.
class WebsocketTicketModel(BaseModel):
    ticket: str
    time_to_live_seconds: int
