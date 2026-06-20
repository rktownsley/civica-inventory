"""
Render-test harness for templates/main.html.

This stands up a minimal Flask app with stub routes matching every
url_for(...) endpoint the template references, then renders the
template with representative mock data (multiple items, multiple
locations per item, paginated, with various query-string filters
set) to catch any Jinja runtime errors (undefined vars, bad filters,
etc.) that a pure parse-only check can't catch.
"""
from flask import Flask, render_template, request
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(PROJECT_ROOT, "templates")

app = Flask(__name__, template_folder=TEMPLATES_DIR)
app.secret_key = "test"


@app.route("/")
def main_page():
    return "stub"


@app.route("/add_item")
def add_item():
    return "stub"


@app.route("/use_item/<int:item_id>", methods=["POST"])
def use_item(item_id):
    return "stub"


@app.route("/mark_removed/<int:item_id>")
def mark_removed(item_id):
    return "stub"


@app.route("/mark_restock/<int:item_id>")
def mark_restock(item_id):
    return "stub"


@app.route("/restock_inventory")
def restock_inventory():
    return "stub"


# base.html is required by {% extends %}; create a minimal stand-in
import os
# Note: this test only needs *a* base.html that defines the blocks
# main.html extends (body_class, content) -- it does not need to be
# the project's real base.html. We render with a Jinja loader that
# checks the real templates/ dir first (for main.html) and falls
# back to a temp dir holding a minimal base.html stub, so this test
# never writes into the actual templates/ deliverable folder.
import tempfile
from jinja2 import ChoiceLoader, FileSystemLoader as _FSL

_stub_dir = tempfile.mkdtemp()
_base_html_path = os.path.join(_stub_dir, "base.html")
with open(_base_html_path, "w") as f:
    f.write(
        "<!DOCTYPE html><html><head>"
        "{% block body_class %}{% endblock %}"
        "</head><body>"
        "{% block content %}{% endblock %}"
        "</body></html>"
    )

app.jinja_loader = ChoiceLoader([
    _FSL(TEMPLATES_DIR),
    _FSL(_stub_dir),
])


def make_item(item_id, name, n_locations=2, with_lot=True):
    locations = {}
    loc_names = ["Tepati", "Grove", "Knights Landing"]
    for i in range(n_locations):
        loc_id = item_id * 10 + i
        locations[loc_id] = {
            "location": loc_names[i % len(loc_names)],
            "location1": "Shelf A",
            "location2": "Bin 3",
            "location3": "",
            "location4": "",
            "quantity": str(5 + i),
            "total_quantity": str(10 + i),
            "minimum_supply": "3",
            "lot_number": f"LOT{item_id}{i}" if with_lot else "",
            "expiration_date": "12/31/2026",
            "expiration_date_iso": "2026-12-31",
            "order_quantity": "10",
            "order_number": "ON123",
            "supplier": "Acme Supply",
            "last_edit": "2026-06-01T10:00:00",
            "removed": False,
            "restock": False,
            "get": lambda k, d=None, _loc=locations: d,  # not realistic but unused directly
        }
    return {
        "id": item_id,
        "name": name,
        "aka": "",
        "category": "Medication",
        "description": "Test description",
        "dispense_as": "Tablet",
        "dispense_used": "1",
        "display_locations": "Tepati, Grove",
        "dosage": "10mg",
        "form": "Tablet",
        "instrument_type": "",
        "medication_class": "Antibiotic",
        "ndc": "12345-678-90",
        "photo_url": "img/placeholder.png",
        "prescription_type": "Rx",
        "removed": False,
        "status": "Active",
        "unit_quantity": "1",
        "locations": locations,
    }


aggregated_items = [
    make_item(1, "Amoxicillin 500mg", n_locations=2, with_lot=True),
    make_item(2, "Ibuprofen 200mg", n_locations=1, with_lot=False),
    make_item(3, "Saline Solution", n_locations=3, with_lot=True),
]

locations_list = [
    ("Tepati", 1),
    ("Grove", 2),
    ("Knights Landing", 3),
]

class FakeChoice:
    def __init__(self, value):
        self.value = value


context = dict(
    aggregated_items=aggregated_items,
    items=aggregated_items,
    locations=locations_list,
    current_date="2026-06-20",
    one_month_date="2026-07-20",
    current_sort="sort1",
    selected_location="Tepati",
    restock_count=2,
    page=1,
    total_pages=3,
    categories=[FakeChoice("Medication"), FakeChoice("Supplies")],
    suppliers=[FakeChoice("Acme Supply"), FakeChoice("MedCo")],
    medication_classes=[FakeChoice("Antibiotic"), FakeChoice("Analgesic")],
    locations1=[FakeChoice("Shelf A"), FakeChoice("Shelf B")],
    locations2=[FakeChoice("Bin 1"), FakeChoice("Bin 3")],
    locations3=[FakeChoice("Row 1")],
    locations4=[FakeChoice("Slot 1")],
    selected_categories=["Medication"],
    selected_suppliers=[],
    selected_medication_classes=[],
    selected_locations1=[],
    selected_locations2=[],
    selected_locations3=[],
    selected_locations4=[],
)

scenarios = [
    {},
    {"location": "Tepati"},
    {"location": "Grove", "category": "Medication", "supplier": "Acme Supply"},
    {"search": "amox", "sort": "sort2"},
    {"filters": ["low_stock"], "categories": ["Medication"], "suppliers": ["Acme Supply"]},
    {"location1": "Shelf A", "location2": "Bin 3"},
]

with app.test_request_context("/"):
    pass

all_ok = True
for i, qs in enumerate(scenarios):
    with app.test_request_context("/", query_string=qs):
        try:
            html = render_template("main.html", **context)
            print(f"Scenario {i} {qs}: OK ({len(html)} chars)")
        except Exception as e:
            all_ok = False
            print(f"Scenario {i} {qs}: FAILED -> {type(e).__name__}: {e}")

print()
print("ALL SCENARIOS PASSED" if all_ok else "SOME SCENARIOS FAILED")
