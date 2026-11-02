"""Public toy example of negative transfer; NOT SKYNET production code."""


def choose_route(hazard_probability: float, detour_cost: int = 6, direct_cost: int = 3, hazard_penalty: int = 8) -> str:
    """Choose the cheaper expected-cost route using an illustrative probability."""
    if not 0 <= hazard_probability <= 1:
        raise ValueError("probability must be in [0, 1]")
    return "detour" if detour_cost < direct_cost + hazard_probability * hazard_penalty else "direct"


def realized_cost(route: str, hazard: bool) -> int:
    if route == "detour":
        return 6
    if route == "direct":
        return 3 + (8 if hazard else 0)
    raise ValueError("unknown route")


if __name__ == "__main__":
    learned_probability = 0.8
    route = choose_route(learned_probability)
    print("Learned route:", route)
    print("Stable environment (hazard):", realized_cost(route, True))
    print("Shifted environment (no hazard):", realized_cost(route, False))
    print("Shifted no-experience direct route:", realized_cost("direct", False))
