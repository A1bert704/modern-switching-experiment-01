from src.metrics import summarize
from src.models import Arrival, Config
from src.utils import simulate


def test_packet_at_observation_window_end_is_backlog():
    cfg = Config(ticks=1, header_bits=32)
    raw = simulate([Arrival(0, 0, 200)], cfg, 'packet')
    metrics = summarize(raw, cfg)

    assert raw['wire_sent_bits'] == 128
    assert raw['delivered_payload_bits'] == 0
    assert raw['dropped_payload_bits'] == 0
    assert metrics['backlog_payload_bits'] == 200
    assert metrics['payload_utilization'] == 0
    assert metrics['wire_utilization'] == 1
    assert metrics['mean_delay_ms'] is None
    assert metrics['max_delay_ms'] is None