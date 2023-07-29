import json
import websocket
import threading
from concurrent.futures import Future
import uuid
import logging


class WebSocketClient:
    """Base class for stb8 websocket clients."""

    def __init__(self, host: str, port):
        url = f"ws://{host}:{port}"
        self._connection = websocket.create_connection(
            url,
            None,
            subprotocols=["lws-bidirectional-protocol"],
        )
        self._receive_thread = threading.Thread(
            target=self._listen_for_messages, daemon=True
        )
        self._receive_thread.start()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def close(self):
        """Close the connection to the box."""
        self._connection.close()

    def _listen_for_messages(self):
        while True:
            try:
                data = self._connection.recv()
            except websocket.WebSocketConnectionClosedException:
                break
            if not data:
                break
            message: dict() = json.loads(data)
            self._handle_message(message)

    def _handle_message(self, message: dict):
        """To be implemented by subclasses."""
        raise NotImplementedError()


class Remote(WebSocketClient):
    """Remote control for the box."""

    class RemoteTimeoutError(Exception):
        def __init__(self, payload):
            self.payload = payload
            super().__init__(f"Timeout while waiting for response. Payload: {payload}")

    class RemoteResponseError(Exception):
        def __init__(self, payload, response):
            self.payload = payload
            self.response = response
            super().__init__(
                f"Error while sending payload. Payload: {payload}, Response: {response}"
            )

    class InvalidButtonError(Exception):
        def __init__(self, button):
            self.button = button
            super().__init__(
                f"Invalid button: {button}. Valid buttons are: {', '.join(Remote.BUTTONS)}"
            )

    BUTTONS = [
        "power",
        "up",
        "right",
        "left",
        "down",
        "ok",
        "back",
        "home",
        "volDown",
        "volUp",
        "mute",
        "channelDown",
        "channelUp",
        "fastBackward",
        "fastForward",
        "playPause",
        "0",
        "1",
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "8",
        "9",
        "stop",
        "record",
    ]

    def __init__(self, host: str, port=7682, timeout=10):
        super().__init__(host, port)
        if timeout == 0:
            timeout = None
        self.timeout = timeout
        self._pending_requests: dict[str, Future[dict]] = {}

    def _send(self, payload: dict):
        """Send data to the box and wait for the response."""
        request_id = str(uuid.uuid4())
        payload["requestId"] = request_id
        self._connection.send(json.dumps(payload))
        future: Future[dict] = Future()
        self._pending_requests[request_id] = future

        try:
            response = future.result(timeout=self.timeout)
        except TimeoutError as e:
            raise self.RemoteTimeoutError(payload) from e
        finally:
            del self._pending_requests[request_id]

        if (
            "remoteResponseCode" not in response
            or response["remoteResponseCode"] != "OK"
        ):
            raise self.RemoteResponseError(payload, response)

        return response

    def press_button(self, button: str):
        """Send a button press to the box."""
        if button not in self.BUTTONS:
            raise self.InvalidButtonError(button)
        self._send({"action": "buttonEvent", "params": {"key": button}})

    def get_versions(self) -> dict:
        """Get remote control version and box type, name and mac address."""
        response = self._send({"action": "getVersions"})
        return response["data"]

    def is_power_on(self) -> bool:
        """Get the current power status of the box."""
        response = self._send({"action": "getStatus"})
        return response["data"]["power"] == "powerOn"

    def _handle_message(self, message: dict):
        if request_id := message.get("requestId"):
            self._pending_requests[request_id].set_result(message)
        else:
            logging.warning(f"Unhandled message: {message}")


class StatusListener(WebSocketClient):
    """Listen to status updates from the box."""

    def __init__(
        self,
        host: str,
        port=7684,
        on_status_change=None,
    ):
        super().__init__(host, port)
        self.on_status_change = on_status_change

    def _handle_message(self, message: dict):
        is_power_on = message["data"]["status"] == "powerOn"
        if self.on_status_change:
            self.on_status_change(is_power_on)


if __name__ == "__main__":

    host = "192.168.1.246"
    timeout = 5

    logging.warning("test")

    remote = Remote(host)
    remote.press_button('d3')
    remote.close()