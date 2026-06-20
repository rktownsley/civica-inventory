/* inventory_item_init.js
 *
 * Wiring for the handful of behaviors in main.html's `aggregated_items`
 * loop that genuinely differ per item (as opposed to the shared,
 * item-agnostic functions in inventory_item_actions.js).
 *
 * In the original template, each of these was a separate inline
 * <script> block re-emitted once per item inside the Jinja
 * `{% for item in aggregated_items %}` loop, each one binding a
 * listener to that one item's specific element IDs (e.g.
 * `confirmTransferButton-42`). With potentially hundreds of items,
 * that meant hundreds of near-identical listener registrations.
 *
 * Here the same end behavior is achieved with event delegation on
 * `document`, matching elements by ID prefix and extracting the
 * item id from the suffix. This is behaviorally equivalent (clicking
 * any item's button still does exactly what it did before) without
 * needing one listener per item.
 *
 * One per-item block from the original is intentionally NOT ported:
 * a listener that did `document.getElementById('view-button-' + id)
 * .addEventListener(...)`. main.html never renders any element with
 * an id matching `view-button-<id>`, so in the original this call
 * always threw a TypeError as soon as it ran, for every item, and
 * the click handler it tried to attach never existed in practice.
 * Since nothing in the app depends on that handler ever firing,
 * omitting it changes nothing observable.
 */

document.addEventListener('DOMContentLoaded', function () {

    /* ---------------------------------------------------------------
     * Confirm Transfer button (per item: confirmTransferButton-<id>)
     * ------------------------------------------------------------- */
    document.addEventListener('click', function (event) {
        const transferBtn = event.target.closest('[id^="confirmTransferButton-"]');
        if (!transferBtn) return;

        const itemId = transferBtn.id.slice('confirmTransferButton-'.length);

        const transferQtyInput = document.getElementById(`transferQty-${itemId}`);
        const transferLocInput = document.getElementById(`transferLoc-${itemId}`);
        const quantitySelect = document.getElementById(`quantitySelect-${itemId}`);
        const transferSelect = document.getElementById(`transferSelect-${itemId}`);
        const transferForm = document.getElementById(`transferForm-${itemId}`);
        const locationSelect = document.getElementById(`locationSelect-${itemId}`);

        const selectedQty = quantitySelect.value;
        const selectedDest = transferSelect.value;
        const selectedSrc = locationSelect.value;

        if (selectedQty && selectedDest && selectedSrc) {
            transferQtyInput.value = selectedQty;
            transferLocInput.value = selectedDest;

            // Set the correct action with source location ID
            transferForm.action = `/transfer_item/${selectedSrc}`;

            transferForm.submit();
        } else {
            alert("Please select both quantity and destination to proceed with transfer.");
        }
    });

    /* ---------------------------------------------------------------
     * Confirm Remove button (per item: confirmRemoveButton-<id>)
     * ------------------------------------------------------------- */
    document.addEventListener('click', function (event) {
        const removeBtn = event.target.closest('[id^="confirmRemoveButton-"]');
        if (!removeBtn) return;

        const itemId = removeBtn.id.slice('confirmRemoveButton-'.length);

        const removeForm = document.getElementById(`removeForm-${itemId}`);
        const locationSelect = document.getElementById(`locationSelect-${itemId}`);
        const selectedSrc = locationSelect.value;

        if (selectedSrc) {
            // Set the correct action with source location ID
            removeForm.action = `/mark_removed/${selectedSrc}`;
            removeForm.submit();
        } else {
            alert("Please select source lot number to proceed with remove.");
        }
    });

    /* ---------------------------------------------------------------
     * Confirm Restock button (per item: confirmRestockButton-<id>)
     * ------------------------------------------------------------- */
    document.addEventListener('click', function (event) {
        const restockBtn = event.target.closest('[id^="confirmRestockButton-"]');
        if (!restockBtn) return;

        const itemId = restockBtn.id.slice('confirmRestockButton-'.length);

        const restockForm = document.getElementById(`restockForm-${itemId}`);
        const locationSelect = document.getElementById(`locationSelect-${itemId}`);
        const selectedSrc = locationSelect.value;

        if (selectedSrc) {
            // Set the correct action with source location ID
            restockForm.action = `/mark_restock/${selectedSrc}`;
            restockForm.submit();
        } else {
            alert("Please select source lot number to proceed with restock request.");
        }
    });

    /* ---------------------------------------------------------------
     * Remove-form submit: stash current scroll position before posting
     * (per item: remove-form-<id> / current_hash_<id>)
     * ------------------------------------------------------------- */
    document.addEventListener('submit', function (event) {
        const form = event.target;
        if (!form.id || !form.id.startsWith('remove-form-')) return;

        const itemId = form.id.slice('remove-form-'.length);
        const hash = window.location.hash;
        const hiddenInput = document.getElementById(`current_hash_${itemId}`);
        if (!hiddenInput) return;

        if (hash && hash.startsWith('#scroll=')) {
            const scrollValue = hash.split('=')[1];  // Capture the value after 'scroll='
            console.log('Captured scroll position:', scrollValue);  // Debugging log
            hiddenInput.value = 'scroll=' + scrollValue;  // Set the value of the unique hidden input
            console.log('Current hash value:', hiddenInput.value); // Debugging
        } else {
            // If no hash or no scroll parameter, set it to empty string
            hiddenInput.value = "scroll=0";
        }
    });

    /* ---------------------------------------------------------------
     * Auto-select the location when an item has exactly one location
     * (per item: locationSelect-<id>)
     * ------------------------------------------------------------- */
    document.querySelectorAll('[id^="locationSelect-"]').forEach(function (locationSelect) {
        if (locationSelect.options.length === 2) {  // disabled "Select a location" + 1 real option
            const itemId = locationSelect.id.slice('locationSelect-'.length);
            locationSelect.selectedIndex = 1;
            updateLocationActions(itemId);
        }
    });

});
