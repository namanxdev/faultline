"""pagination: the list tool returns pages of two items and a cursor."""

from dataclasses import replace

from faultline.drifts.base import Drift, ToolFailure
from faultline.toolspec import Param

PAGE_SIZE = 2


class Pagination(Drift):
    name = "pagination"
    rationale = "Real list endpoints page; an agent that reads only page one misses records."

    def specs(self, service, specs):
        tool, _ = service.LIST
        return [
            replace(
                s,
                params=(*s.params, Param("cursor", required=False)),
                description=s.description + " Results are paged; pass next_cursor to continue.",
            )
            if s.name == tool
            else s
            for s in specs
        ]

    def before(self, service, name, args):
        if name == service.LIST[0]:
            cursor = args.pop("cursor", None) or "0"
            if not cursor.isdigit():
                raise ToolFailure(f"Invalid cursor: {cursor}")
            service.cursor = int(cursor)
        return args

    def after(self, service, name, args, result):
        tool, key = service.LIST
        if name != tool:
            return result
        start, items = service.cursor, result[key]
        more = start + PAGE_SIZE < len(items)
        return {
            key: items[start : start + PAGE_SIZE],
            "next_cursor": str(start + PAGE_SIZE) if more else None,
        }


DRIFT = Pagination()
