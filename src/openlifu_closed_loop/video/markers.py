"""LSL publisher for behavioral video markers."""

from __future__ import annotations

from pylsl import StreamInfo, StreamOutlet, local_clock


class VideoMarkerPublisher:
    """Publish behavioral video markers on the shared LSL clock."""

    def __init__(
        self,
        stream_name: str = "VideoMarkers",
        stream_type: str = "Markers",
        source_id: str = "openlifu-video-markers",
    ) -> None:
        info = StreamInfo(
            name=stream_name,
            type=stream_type,
            channel_count=1,
            nominal_srate=0,
            channel_format="string",
            source_id=source_id,
        )
        self._outlet = StreamOutlet(info)

    def publish(self, marker: str, timestamp: float | None = None) -> float:
        """Publish one marker and return the LSL timestamp used."""
        if not marker:
            raise ValueError("marker must be a non-empty string")

        lsl_timestamp = local_clock() if timestamp is None else timestamp
        self._outlet.push_sample([marker], lsl_timestamp)
        return lsl_timestamp

    def wait_for_consumer(self, timeout: float = 2.0) -> bool:
        """Wait until at least one LSL consumer is connected."""
        return self._outlet.wait_for_consumers(timeout)
