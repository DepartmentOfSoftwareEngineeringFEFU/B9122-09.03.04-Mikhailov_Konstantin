from typing import Protocol, Optional, runtime_checkable

@runtime_checkable

class ListingParser(Protocol):

    def collect(

        self,

        rooms: int | str | tuple,

        start_page: int,

        end_page: int,

    ) -> None: ...

@runtime_checkable

class DetailParser(Protocol):

    def parse(self, html: str) -> dict: ...

@runtime_checkable

class StorageProtocol(Protocol):

    def upsert_from_listing(self, flat_dict: dict) -> bool: ...

    def bulk_upsert_from_listing(

        self, flats: list[dict]

    ) -> tuple[int, int]: ...

    def get_next_for_detail(

        self,

        max_attempts: int = 3,

        cooldown_minutes: int = 30,

        source: Optional[str] = None,

    ) -> Optional[dict]: ...

    def update_detail(self, flat_id: int, details: dict) -> None: ...

    def mark_failed(self, flat_id: int) -> None: ...

    def mark_blocked(self, flat_id: int) -> None: ...

    def get_stats(self) -> dict: ...

    def get_coverage(self) -> dict: ...

    def close(self) -> None: ...
