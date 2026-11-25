from types import SimpleNamespace

import pytest

from app.streams.shares import split_evenly, rebalance


def offer(share=0, pinned=False, removed=False):
    return SimpleNamespace(share=share, pinned=pinned, removed=removed)


@pytest.mark.parametrize("count", range(1, 13))
def test_shares_sum_to_100(count):
    shares = split_evenly(count)
    assert sum(shares) == 100
    assert max(shares) - min(shares) <= 1


def test_remainder_goes_to_first():
    assert split_evenly(3) == [34, 33, 33]


def test_split_custom_total():
    assert split_evenly(2, 75) == [38, 37]


def test_rebalance_keeps_pinned_share():
    offers = [offer(), offer(25, pinned=True), offer()]
    rebalance(offers)
    assert [o.share for o in offers] == [38, 25, 37]


def test_rebalance_zeroes_removed():
    offers = [offer(50), offer(50, removed=True)]
    rebalance(offers)
    assert [o.share for o in offers] == [100, 0]


def test_rebalance_pinned_over_100():
    offers = [offer(70, pinned=True), offer(60, pinned=True), offer(5)]
    rebalance(offers)
    assert [o.share for o in offers] == [70, 60, 0]
