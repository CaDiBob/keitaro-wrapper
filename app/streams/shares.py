def split_evenly(count: int, total: int = 100) -> list[int]:
    if count <= 0:
        return []
    base, rest = divmod(total, count)
    return [base + (1 if i < rest else 0) for i in range(count)]


def rebalance(offers: list) -> None:
    active = [offer for offer in offers if not offer.removed]
    free = [offer for offer in active if not offer.pinned]
    pinned = sum(offer.share for offer in active if offer.pinned)
    shares = split_evenly(len(free), max(100 - pinned, 0))
    for offer, share in zip(free, shares):
        offer.share = share
    for offer in offers:
        if offer.removed:
            offer.share = 0
