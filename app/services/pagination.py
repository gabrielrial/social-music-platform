from fastapi import Query

class Page:
    """Pagination parameters shared by every feed. As a dependency
    (`page: Page = Depends()`), FastAPI reads them from the query string
    (?limit=20&offset=40) and validates them: limit=0 or limit=500 is a 422
    before our code runs."""

    def __init__(
        self,
        limit: int = Query(20, ge=1, le=100),
        offset: int = Query(0, ge=0),
    ):
        self.limit = limit
        self.offset = offset