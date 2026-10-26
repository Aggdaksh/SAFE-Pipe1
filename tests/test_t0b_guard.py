from experiments.t0b_probe import main


def test_t0b_refuses_without_16gb_flag() -> None:
    assert main([]) == 2
