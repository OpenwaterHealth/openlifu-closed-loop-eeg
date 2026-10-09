from __future__ import annotations

from uuid import uuid4

from pylsl import StreamInlet, local_clock, resolve_byprop

from openlifu_closed_loop.video import VideoMarkerPublisher


def _make_publisher() -> tuple[VideoMarkerPublisher, str]:
    stream_name = f"VideoMarkersTest-{uuid4()}"
    publisher = VideoMarkerPublisher(
        stream_name=stream_name,
        source_id=f"openlifu-video-markers-test-{uuid4()}",
    )
    return publisher, stream_name


def _connect_inlet(stream_name: str) -> StreamInlet:
    streams = resolve_byprop("name", stream_name, timeout=5.0)
    assert streams, f"LSL stream {stream_name!r} was not discovered"

    inlet = StreamInlet(streams[0])
    inlet.open_stream(timeout=2.0)
    return inlet


def test_video_marker_stream_can_be_resolved() -> None:
    publisher, stream_name = _make_publisher()

    streams = resolve_byprop("name", stream_name, timeout=5.0)

    assert publisher is not None
    assert streams
    assert streams[0].type() == "Markers"
    assert streams[0].channel_count() == 1


def test_video_marker_round_trip() -> None:
    publisher, stream_name = _make_publisher()
    inlet = _connect_inlet(stream_name)

    assert publisher.wait_for_consumer(timeout=2.0)

    publisher.publish("frame:42")
    sample, timestamp = inlet.pull_sample(timeout=2.0)

    assert sample == ["frame:42"]
    assert timestamp is not None


def test_video_marker_uses_shared_lsl_clock() -> None:
    publisher, stream_name = _make_publisher()
    inlet = _connect_inlet(stream_name)

    assert publisher.wait_for_consumer(timeout=2.0)

    before = local_clock()
    published_at = publisher.publish("video_start")
    sample, received_at = inlet.pull_sample(timeout=2.0)
    after = local_clock()

    assert sample == ["video_start"]
    assert received_at is not None
    assert before <= published_at <= after
    assert received_at == published_at

def test_empty_marker_is_rejected() -> None:
    publisher, _ = _make_publisher()

    try:
        publisher.publish("")
    except ValueError as exc:
        assert str(exc) == "marker must be a non-empty string"
    else:
        raise AssertionError("expected ValueError")
