from safe_pipe.cost import expected_cost
from safe_pipe.grid import get_config, load_grid
from safe_pipe.memory import parse_gb


def test_grid_has_exactly_eight_declared_ids() -> None:
    ids = [s.config_id for s in load_grid()]
    assert ids == [
        "w1_t1_1g",
        "w1_t2_1g",
        "w1_t1_2g",
        "w1_t2_2g",
        "w2_t1_1g",
        "w2_t2_1g",
        "w2_t1_2g",
        "w2_t2_2g",
    ]


def test_allocated_resources_match_native_knobs() -> None:
    spec = get_config("w2_t2_2g")
    assert spec.allocated_vcpus == 4.0
    assert spec.allocated_gb == 2 * parse_gb("2GB")
    assert expected_cost(spec, 10.0) == spec.allocated_vcpus * 10 + spec.allocated_gb * 10
