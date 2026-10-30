"""Offline DonutSMP coordinate, spawner-cost, and estimate utilities."""

from __future__ import annotations

import argparse
import json
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any


RATES: dict[str, tuple[str, Decimal, Decimal | None, str]] = {
    "skelly": ("Skeleton", Decimal("121.76"), Decimal("2922.32"), "bones"),
    "skeleton": ("Skeleton", Decimal("121.76"), Decimal("2922.32"), "bones"),
    "iron golem": ("Iron Golem", Decimal("595.98"), None, "iron ingots"),
    "irongolem": ("Iron Golem", Decimal("595.98"), None, "iron ingots"),
    "zombified piglin": ("Zombified Piglin", Decimal("447"), None, "gold nuggets"),
    "zombifiedpiglin": ("Zombified Piglin", Decimal("447"), None, "gold nuggets"),
    "creeper": ("Creeper", Decimal("238.38"), None, "gunpowder"),
    "spider": ("Spider", Decimal("238.38"), None, "string"),
    "pig": ("Pig", Decimal("35.76"), None, "porkchops"),
}


def _finite_decimal(value: str, label: str) -> Decimal:
    try:
        result = Decimal(value)
    except InvalidOperation as error:
        raise ValueError(f"{label} must be a valid number.") from error
    if not result.is_finite():
        raise ValueError(f"{label} must be finite.")
    return result


def _format_decimal(value: Decimal, places: int | None = None) -> str:
    if places is not None:
        value = value.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def convert_coordinates(direction: str, x: str, y: str, z: str) -> dict[str, Any]:
    x_value, y_value, z_value = (
        _finite_decimal(value, name) for name, value in (("x", x), ("y", y), ("z", z))
    )
    if direction == "overworld-to-nether":
        def round_block(value: Decimal) -> Decimal:
            return (value / Decimal(8)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

        result = (round_block(x_value), y_value, round_block(z_value))
    elif direction == "nether-to-overworld":
        result = (x_value * 8, y_value, z_value * 8)
    else:
        raise ValueError("Direction must be overworld-to-nether or nether-to-overworld.")
    return {
        "direction": direction,
        "input": [_format_decimal(value) for value in (x_value, y_value, z_value)],
        "output": [_format_decimal(value) for value in result],
        "note": "Coordinate conversion only; verify portal placement in-game.",
    }


def parse_price(raw: str) -> Decimal:
    text = raw.strip().lower().replace(",", "").replace("$", "")
    multiplier = Decimal(1)
    if text.endswith("k"):
        multiplier, text = Decimal(1000), text[:-1]
    elif text.endswith("m"):
        multiplier, text = Decimal(1_000_000), text[:-1]
    elif text.endswith("b"):
        multiplier, text = Decimal(1_000_000_000), text[:-1]
    value = _finite_decimal(text, "Price") * multiplier
    if value < 0:
        raise ValueError("Price must be non-negative.")
    return value


def calculate_spawners(quantity: int, price_each: str) -> dict[str, Any]:
    if isinstance(quantity, bool) or quantity <= 0:
        raise ValueError("Quantity must be a positive whole number.")
    price = parse_price(price_each)
    total = price * quantity
    return {
        "quantity": quantity,
        "price_each": f"${price.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):,.2f}",
        "total": f"${total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):,.2f}",
        "note": "Calculation only; prices are supplied by you and are not live market data.",
    }


def spawner_rate(name: str) -> dict[str, Any]:
    normalized = " ".join(name.casefold().split())
    if normalized not in RATES:
        raise ValueError("Unknown spawner. Supported: " + ", ".join(sorted(RATES)))
    display_name, hourly, daily_override, item = RATES[normalized]
    daily = daily_override if daily_override is not None else hourly * Decimal(24)
    return {
        "spawner": display_name,
        "per_minute": f"{hourly / Decimal(60):,.2f} {item}",
        "per_hour": f"{hourly:,.2f} {item}",
        "per_day": f"{daily:,.2f} {item}",
        "note": "These are built-in estimates from the supplied script, not verified live DonutSMP rates.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    convert = commands.add_parser("convert", help="Convert Overworld/Nether coordinates.")
    convert.add_argument("direction", choices=("overworld-to-nether", "nether-to-overworld"))
    convert.add_argument("x")
    convert.add_argument("y")
    convert.add_argument("z")

    calc = commands.add_parser("calc", help="Calculate spawner purchase cost.")
    calc.add_argument("quantity", type=int)
    calc.add_argument("price_each")

    rate = commands.add_parser("rate", help="Show a built-in per-spawner estimate.")
    rate.add_argument("spawner", nargs="+")

    args = parser.parse_args(argv)
    try:
        if args.command == "convert":
            result = convert_coordinates(args.direction, args.x, args.y, args.z)
        elif args.command == "calc":
            result = calculate_spawners(args.quantity, args.price_each)
        else:
            result = spawner_rate(" ".join(args.spawner))
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
