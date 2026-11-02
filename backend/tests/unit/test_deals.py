"""Unit tests for deal schemas and defaults (no DB required). Access rules are tested against the live API."""

import pytest
from pydantic import ValidationError

from app.api.v1.endpoints.deals import router
from app.schemas.deal import DealCreate, DealItemCreate, DealUpdate
from app.services.auth_service import get_current_user
from app.services.deal_service import DEFAULT_ITEMS


def test_default_items_cover_documents_and_advisors():
    kinds = [kind for kind, _ in DEFAULT_ITEMS]
    assert kinds.count("document") == 7
    assert kinds.count("advisor") == 5


def test_rejects_unknown_stage_and_kind():
    with pytest.raises(ValidationError):
        DealUpdate(stage="maybe")
    with pytest.raises(ValidationError):
        DealItemCreate(kind="other", title="x")


def test_rejects_blank_name():
    with pytest.raises(ValidationError):
        DealCreate(name="")


def test_update_tells_cleared_fields_from_unset():
    assert DealUpdate(notes=None).model_dump(exclude_unset=True) == {"notes": None}
    assert DealUpdate().model_dump(exclude_unset=True) == {}


def test_every_deal_route_requires_login():
    for route in router.routes:
        assert any(d.call is get_current_user for d in route.dependant.dependencies), route.path
