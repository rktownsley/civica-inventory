/* inventory_item_actions.js
 *
 * Item-row action handlers shared by every row rendered in main.html's
 * `aggregated_items` loops (table rows, use-overlay, remove-overlay).
 *
 * These functions are written once here instead of being re-emitted inside
 * every Jinja `{% for item in aggregated_items %}` iteration. They all take
 * an `itemId` (and sometimes a `locationId`/`location` name) and look up the
 * relevant DOM nodes by the `<id>-<itemId>` naming convention already used
 * throughout main.html, so no behavior changes are required to use them.
 */

/* ---------------------------------------------------------------------
 * Overlay visibility helpers
 * ------------------------------------------------------------------- */

function isOverlayVisible() {
    // Check if the overlay is visible by inspecting the style
    const isOverlayVisible = (document.querySelector('.use-overlay[style*="display: flex"]') !== null) ||
                             (document.querySelector('.overlay[style*="display: flex"]') !== null);

    // Check if confirmDelete is being called (indicating an active overlay)
    if (isOverlayVisible || window.confirmDialogActive) {
        return true;
    }
    return false;
}

function handleRowClick(itemId) {
    if (isOverlayVisible()) return;

    const container = document.querySelector(`#lotOptions-${itemId}`);
    if (!container) {
        console.log("Debug line ??? main: pre toggle_use_overlay_1");
        toggleUseOverlay(itemId);
        return;
    }

    // A lot is selected if it has the "selected" class OR its radio is checked
    const selectedLot = container.querySelector('.lot-pill.selected, .lot-pill input[type="radio"]:checked');

    const firstLot = container.querySelector('.lot-pill');

    // CASE 1: No lot selected but lots exist → simulate clicking first lot
    if (!selectedLot && firstLot) {
        firstLot.click();  // triggers your existing event handlers
        console.log("Hello line 1593 main");
        return;
    }

    // CASE 2: Lots exist but one is already selected → normal behavior
    // CASE 3: No lots exist → normal behavior
    console.log("Debug line ??? main: pre toggle_use_overlay_2");
    toggleUseOverlay(itemId);
    console.log("Hello line 1600 main");
}

function toggleOverlay(itemId) {
    event.stopPropagation();
    var overlay = document.getElementById('overlay-' + itemId);
    var isVisible = overlay.style.display === 'flex';
    overlay.style.display = isVisible ? 'none' : 'flex';
}

function toggleUseOverlay(itemId, location) {
    console.log(`Ln 5146: TOGGLE USE OVERLAY ( ${itemId} , ${location} )`);
    event.stopPropagation();
    // Set the location in the form or dropdown
    let locationSelect = document.getElementById(`locationSelect-${itemId}`);
    if (locationSelect) {

        for (let option of locationSelect.options) {
            if (option.text === location) {
                option.selected = true;
                break;
            }
        }

        updateLocationActions(itemId)
    }
    var overlay = document.getElementById('use-overlay-' + itemId);
    var isVisible = overlay.style.display === 'flex';
    overlay.style.display = isVisible ? 'none' : 'flex';
}

// NEW:1-10-26
function closeUseModal(event, itemId) {
    console.log("Debug line 5179 main, item id:", itemId);
    event.stopPropagation();
    const overlay = document.getElementById(`use-overlay-${itemId}`);
    overlay.style.display = 'none';
    overlay.innerHTML = ''; // clear content
    overlay.innerHTML = overlay.dataset.originalHtml;
    overlay.onclick = null;
}

function updateUseAction(itemId) {
    let selectElement = document.getElementById(`locationSelect-${itemId}`);
    let selectedLocationId = selectElement.value;
    let form = document.getElementById(`use-form-${itemId}`);

    // Set the form action dynamically based on the selected location
    if (selectedLocationId) {
        form.action = `/use_item/${selectedLocationId}`;
    } else {
        // Reset the action if no location is selected
        form.action = `/use_item/${itemId}`;
    }
}

/* ---------------------------------------------------------------------
 * Location detail popup (the small floating card with lot info)
 * ------------------------------------------------------------------- */

function openLocationDetails(event, itemId, locationName, itemName) {
    event.stopPropagation();

    const overlay = document.getElementById(`use-overlay-${itemId}`);

    // Map Knights Landing → KL
    const displayLocation = locationName === "Knights Landing" ? "KL" : locationName;

    // Save original overlay content if not already saved
    if (!overlay.dataset.originalHtml) {
        overlay.dataset.originalHtml = overlay.innerHTML;
    }

    // Get the hidden select for this item
    const select = document.getElementById(`locationSelect-${itemId}`);

    //New:5-5-26
    let options = Array.from(select.options)
        .filter(opt => opt.getAttribute('data-location') === locationName);
    if (!options.length) return;


    // // Pull sublocation data from the <option>

    // `;

    let lotsHtml = options.map(opt => {
        const location1 = opt.getAttribute('data-location1');
        const location2 = opt.getAttribute('data-location2');
        const location3 = opt.getAttribute('data-location3');
        const location4 = opt.getAttribute('data-location4');
        const quantity = opt.getAttribute('data-quantity');

        return `
            <div class="mb-2 border-bottom pb-1">
                <div><strong>Qty:</strong> ${quantity}</div>
                <div>${location1}</div>
                <div>${location2}</div>
                <div>${location3}</div>
                <div>${location4}</div>
            </div>
        `;
    }).join('');

    //         ${lotsHtml}
    // `;
    overlay.innerHTML = `
        <div class="loc-popup">
            <button class="loc-popup-close" onclick="closeLocationDetails(event, '${itemId}')">×</button>
            
            <div class="loc-popup-title fw-bold">${itemName}</div>
            <div class="mb-2">Site: ${displayLocation}</div>

            <hr class="my-2">

            ${lotsHtml}
        </div>
    `;


    overlay.style.display = 'flex';

    // Click outside to close
    overlay.onclick = function(e) {
        if (!e.target.closest('.loc-popup')) {
            closeLocationDetails(e, itemId);
        }
    };
}

function closeLocationDetails(event, itemId) {
    event.stopPropagation();
    const overlay = document.getElementById(`use-overlay-${itemId}`);
    overlay.style.display = 'none';
    overlay.innerHTML = ''; // clear content
    overlay.innerHTML = overlay.dataset.originalHtml;
    overlay.onclick = null;
}

/* ---------------------------------------------------------------------
 * Lot / location selection (compact pill list + custom location list)
 * ------------------------------------------------------------------- */

function handleLocationChange(itemId, locationId) {
    console.log(`Ln 3275: HANDLE LOCATION CHANGE ( ${itemId} , ${locationId} )`);
    const hiddenInput = document.getElementById(`locationSelect-${itemId}`);
    hiddenInput.value = locationId;

    // Clear previous highlight
    document.querySelectorAll(`#lotOptions-${itemId} .lot-option`).forEach(label => {
        label.classList.remove('active');
    });

    // Highlight the label containing the selected radio button
    const selectedLabel = document.querySelector(`#lotOptions-${itemId} input[value='${locationId}']`)?.closest('label');
    if (selectedLabel) {
        selectedLabel.classList.add('active');
    }

    updateLocationActions(itemId);
}

function handleLocationClick(itemId, locationId) {
    const hiddenInput = document.getElementById(`locationSelect-${itemId}`);
    hiddenInput.value = locationId;

    // Clear previous highlight
    document.querySelectorAll(`#locationList-${itemId} .location-option`).forEach(el => {
        el.classList.remove('selected-location');
    });

    // Highlight newly selected
    const selectedEl = document.querySelector(`#locationList-${itemId} .location-option[data-location-id='${locationId}']`);
    if (selectedEl) {
        selectedEl.classList.add('selected-location');
    }

    updateLocationActions(itemId);
}

/* ---------------------------------------------------------------------
 * Use / Transfer panel toggles
 * ------------------------------------------------------------------- */

function toggleUseControls(itemId) {
    const useWrapper = document.getElementById(`useControls-${itemId}`);
    const useToggleBtn = document.getElementById(`toggleUseBtn-${itemId}`);

    const transferWrapper = document.getElementById(`transferControls-${itemId}`);
    const transferToggleBtn = document.getElementById(`toggleTransferBtn-${itemId}`);

    const quantityWrapper = document.getElementById(`quantityWrapper-${itemId}`);
    const quantitySelect = document.getElementById(`quantitySelect-${itemId}`);
    const quantityLabel = document.querySelector(`label[for="quantitySelect-${itemId}"]`);

    const isHidden = useWrapper.classList.contains("d-none");

    if (isHidden) {
        // Show Use section
        useWrapper.classList.remove("d-none");
        quantityWrapper.classList.remove("d-none");
        useToggleBtn.textContent = "Cancel";

        // Hide Transfer section + hide its toggle button
        transferWrapper.classList.add("d-none");
        transferToggleBtn.style.display = "none";

        // Update label text
        quantityLabel.textContent = "Select Quantity";

        // Autofocus and attempt to open dropdown
        // quantitySelect.focus();
        // quantitySelect.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));

    } else {
        // Hide Use section
        useWrapper.classList.add("d-none");
        quantityWrapper.classList.add("d-none");
        useToggleBtn.textContent = "Use Item";
        quantitySelect.value = "1";

        // Show Transfer toggle button again
        transferToggleBtn.style.display = "inline-block";
    }
}

function toggleTransferControls(itemId) {
    const transferWrapper = document.getElementById(`transferControls-${itemId}`);
    const transferToggleBtn = document.getElementById(`toggleTransferBtn-${itemId}`);

    const useWrapper = document.getElementById(`useControls-${itemId}`);
    const useToggleBtn = document.getElementById(`toggleUseBtn-${itemId}`);

    const quantityWrapper = document.getElementById(`quantityWrapper-${itemId}`);
    const quantitySelect = document.getElementById(`quantitySelect-${itemId}`);
    const quantityLabel = document.querySelector(`label[for="quantitySelect-${itemId}"]`);

    const isHidden = transferWrapper.classList.contains("d-none");

    if (isHidden) {
        // Show Transfer section (Cancel Transfer)
        transferWrapper.classList.remove("d-none");
        quantityWrapper.classList.remove("d-none");
        transferToggleBtn.textContent = "Cancel";

        // Hide Use section + hide its toggle button
        useWrapper.classList.add("d-none");
        useToggleBtn.style.display = "none";

        // Update label text
        quantityLabel.textContent = "Select Quantity";

        // Autofocus and attempt to open dropdown
        // quantitySelect.focus();
        // quantitySelect.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));

    } else {
        // Hide Transfer section
        transferWrapper.classList.add("d-none");
        quantityWrapper.classList.add("d-none");
        transferToggleBtn.textContent = "Transfer";
        quantitySelect.value = "1";

        // Show Use toggle button again
        useToggleBtn.style.display = "inline-block";
    }
}

/* ---------------------------------------------------------------------
 * Remove / Restock form action wiring
 * ------------------------------------------------------------------- */

function updateRemoveAction(itemId) {
    let selectElement = document.getElementById(`RemovelocationSelect-${itemId}`);
    let selectedLocationId = selectElement.value;
    let form = document.getElementById(`remove-form-${itemId}`);

    // Set the form action dynamically based on the selected location
    if (selectedLocationId) {
        form.action = `/mark_removed/${selectedLocationId}`;
    } else {
        // Reset the action if no location is selected
        form.action = window.APP_CONFIG.markRemovedBaseUrl;
    }
}

function updateRestockAction(itemId) {
    let selectElement = document.getElementById(`RestocklocationSelect-${itemId}`);
    let selectedLocationId = selectElement.value;
    let form = document.getElementById(`restock-form-${itemId}`);

    // Set the form action dynamically based on the selected location
    if (selectedLocationId) {
        form.action = `/mark_restock/${selectedLocationId}`;
    } else {
        // Reset the action if no location is selected
        form.action = window.APP_CONFIG.markRestockBaseUrl;
    }
}

function markRemoved(itemId) {
    // Toggle red color and strikethrough for the name of the item
    const nameElement = document.getElementById('name-' + itemId);
    if (nameElement) {
        nameElement.style.color = 'red';
        nameElement.style.textDecoration = 'line-through';
    }
}

/* ---------------------------------------------------------------------
 * Restock button + Add Stock link
 * ------------------------------------------------------------------- */

function updateRestockButton(itemId) {
    const select = document.getElementById(`locationSelect-${itemId}`);
    const button = document.getElementById(`confirmRestockButton-${itemId}`);
    const restock = select.options[select.selectedIndex].dataset.restock === "1";

    button.disabled = restock;
    button.innerText = restock ? "Cancel Refill" : "Order Refill";
}

// Add Stock function NEW:1-12-2026
function updateAddStockLink(itemId) {
    const select = document.getElementById(`locationSelect-${itemId}`);
    const selectedOption = select.options[select.selectedIndex];

    const name = selectedOption.getAttribute('data-name');
    const aka = selectedOption.getAttribute('data-aka');
    const status = selectedOption.getAttribute('data-status');
    const quantity = selectedOption.getAttribute('data-quantity');
    const location = selectedOption.getAttribute('data-location');
    const location1 = selectedOption.getAttribute('data-location1');
    const location2 = selectedOption.getAttribute('data-location2');
    const location3 = selectedOption.getAttribute('data-location3');
    const location4 = selectedOption.getAttribute('data-location4');
    const category = selectedOption.getAttribute('data-category');
    const description = selectedOption.getAttribute('data-description');
    const instrumentType = selectedOption.getAttribute('data-instrument_type');
    const expirationDate = selectedOption.getAttribute('data-expiration_date');
    const supplier = selectedOption.getAttribute('data-supplier');
    const orderNumber = selectedOption.getAttribute('data-order_number');
    const orderQuantity = selectedOption.getAttribute('data-order_quantity');
    const dosage = selectedOption.getAttribute('data-dosage');
    const form = selectedOption.getAttribute('data-form');
    const lotNumber = selectedOption.getAttribute('data-lot_number');
    const ndc = selectedOption.getAttribute('data-ndc');
    const dispenseUsed = selectedOption.getAttribute('data-dispense_used');
    const dispenseAs = selectedOption.getAttribute('data-dispense_as');
    const unitQuantity = selectedOption.getAttribute('data-unit_quantity');
    const prescriptionType = selectedOption.getAttribute('data-prescription_type');
    const medClass = selectedOption.getAttribute('data-medication_class');
    const minimumSupply = selectedOption.getAttribute('data-minimum_supply');
    const photoUrl = selectedOption.getAttribute('data-photo_url');
    const lastEdit = selectedOption.getAttribute('data-last_edit');
    const removed = selectedOption.getAttribute('data-removed');
    const restock = selectedOption.getAttribute('data-restock');
    const totalQuantity = selectedOption.getAttribute('data-total_quantity');

    let url = window.APP_CONFIG.addItemUrl +
        `?name=${encodeURIComponent(name)}` +
        `&aka=${encodeURIComponent(aka)}` +
        `&status=${encodeURIComponent(status)}` +
        `&quantity=${encodeURIComponent(quantity)}` +
        `&location=${encodeURIComponent(location)}` +
        `&location1=${encodeURIComponent(location1)}` +
        `&location2=${encodeURIComponent(location2)}` +
        `&location3=${encodeURIComponent(location3)}` +
        `&location4=${encodeURIComponent(location4)}` +
        `&category=${encodeURIComponent(category)}` +
        `&description=${encodeURIComponent(description)}` +
        `&instrument_type=${encodeURIComponent(instrumentType)}` +
        `&dosage=${encodeURIComponent(dosage)}` +
        `&form=${encodeURIComponent(form)}` +
        `&ndc=${encodeURIComponent(ndc)}` +
        `&dispense_used=${encodeURIComponent(dispenseUsed)}` +
        `&dispense_as=${encodeURIComponent(dispenseAs)}` +
        `&unit_quantity=${encodeURIComponent(unitQuantity)}` +
        `&prescription_type=${encodeURIComponent(prescriptionType)}` +
        `&medication_class=${encodeURIComponent(medClass)}` +
        `&minimum_supply=${encodeURIComponent(minimumSupply)}` +
        `&photo_url=${encodeURIComponent(photoUrl)}` +
        `&last_edit=${encodeURIComponent(lastEdit)}` +
        `&removed=${encodeURIComponent(removed)}` +
        `&expiration_date=${encodeURIComponent(expirationDate)}` +
        `&supplier=${encodeURIComponent(supplier)}` +
        `&order_number=${encodeURIComponent(orderNumber)}` +
        `&order_quantity=${encodeURIComponent(orderQuantity)}` +
        `&lot_number=${encodeURIComponent(lotNumber)}` +
        `&restock=${encodeURIComponent(restock)}` +
        `&total_quantity=${encodeURIComponent(totalQuantity)}`;

    // Add minimum_supply for ALL locations (not just selected one)
    const allOptions = select.options;
    for (let i = 0; i < allOptions.length; i++) {
        const option = allOptions[i];
        const loc = option.getAttribute('data-location');
        const minSup = option.getAttribute('data-minimum_supply');
        if (loc && minSup) {
            const locationParam = loc.replace(/ /g, '_');
            url += `&minimum_supply_${encodeURIComponent(locationParam)}=${encodeURIComponent(minSup)}`;
        }
    }

    // Update the href of the **specific button for this item**
    const link = document.getElementById(`add-stock-btn-${itemId}`);
    link.href = url;
}

/* ---------------------------------------------------------------------
 * Main "use item" location selection orchestration
 * ------------------------------------------------------------------- */

function updateLocationActions(itemId) {
    var locationSelect = document.getElementById('locationSelect-' + itemId);
    var transferSelect = document.getElementById('transferSelect-' + itemId);
    var selectedLocationId = locationSelect.value;
    var viewDetailsButton = document.getElementById('viewDetailsButton-' + itemId);
    var editDetailsButton = document.getElementById('editDetailsButton-' + itemId);
    var confirmTransferButton = document.getElementById('confirmTransferButton-' + itemId);

    var confirmRemoveButton = document.getElementById('confirmRemoveButton-' + itemId);
    var confirmRestockButton = document.getElementById('confirmRestockButton-' + itemId);
    var form = document.getElementById('use-form-' + itemId);

    updateRestockButton(itemId);
    updateAddStockLink(itemId);

    // Find the location name from the selected option
    var selectedLocation = locationSelect.options[locationSelect.selectedIndex].getAttribute('data-location');

    // // Ensure transfer options are updated (NEW)
    // // Loop through transfer options and remove the selected location
    //         option.disabled = true;  // Disable the current location from the transfer options
    //     } else {
    //         option.disabled = false;  // Enable other options

    // Update the form's action based on the selected location
    if (selectedLocationId) {
        form.action = '/use_item/' + selectedLocationId;  // Update form action to use the location_id in the URL
    }

    // Update the View Details button's href based on the selected location
    if (selectedLocationId) {
        viewDetailsButton.href = '/view/' + selectedLocationId + window.location.search;  // Update link for View Details
    }

    if (selectedLocationId) {
        editDetailsButton.href = '/edit_item/' + selectedLocationId + window.location.search;  // Update link for Edit Details
    }

    // Update the Transfer button's href based on the selected location
    if (selectedLocationId) {
        confirmTransferButton.href = '/transfer_item/' + selectedLocationId + window.location.search;  // Update link for Transfer button
    }

    // Update the Remove button's href based on the selected location
    if (selectedLocationId) {
        confirmRemoveButton.href = '/mark_removed/' + selectedLocationId + window.location.search;  // Update link for Remove button
    }

    // Update the Restock button's href based on the selected location
    if (selectedLocationId) {
        confirmRestockButton.href = '/mark_restock/' + selectedLocationId + window.location.search;  // Update link for Restock button
    }


    // NEW
    const deleteLink = document.getElementById('deleteLink-' + itemId);
    if (locationSelect && deleteLink) {
        const selectedSrc = locationSelect.value;

        if (selectedSrc) {
            // Preserve all original query parameters
            const params = new URLSearchParams(window.location.search);
            deleteLink.href = `/delete/${selectedSrc}?${params.toString()}`;
        }
    }

    // NEW 10/24/25
    const delistLink = document.getElementById('delistLink-' + itemId);
    if (locationSelect && delistLink) {
        const selectedSrc = locationSelect.value;

        if (selectedSrc) {
            // Preserve all original query parameters
            const params = new URLSearchParams(window.location.search);
            delistLink.href = `/delist/${selectedSrc}?${params.toString()}`;
        }
    }

    // NEW Update transfer options to exclude selected location
    var transferOptions = transferSelect.querySelectorAll('option');
    transferOptions.forEach(function(option) {
        var location = option.getAttribute('data-location');
        if (!location || option.value === "") return; // Skip placeholder

        if (location === selectedLocation) {
            option.style.display = 'none';
        } else {
            option.style.display = '';
        }
    });

    //NEW
    const select = document.getElementById(`locationSelect-${itemId}`);
    const selectedOption = select.options[select.selectedIndex];
    const display = document.getElementById(`itemIdDisplay-${itemId}`);

    if (select.value) {
        const selectedLocationId = select.value;

        // Retrieve the data attributes from the selected option
        const name = selectedOption.getAttribute('data-name');
        const aka = selectedOption.getAttribute('data-aka');
        const status = selectedOption.getAttribute('data-status');
        const quantity = selectedOption.getAttribute('data-quantity');
        const location = selectedOption.getAttribute('data-location');
        const location1 = selectedOption.getAttribute('data-location1');
        const location2 = selectedOption.getAttribute('data-location2');
        const location3 = selectedOption.getAttribute('data-location3');
        const location4 = selectedOption.getAttribute('data-location4');
        const category = selectedOption.getAttribute('data-category');
        const description = selectedOption.getAttribute('data-description');
        const instrumentType = selectedOption.getAttribute('data-instrument_type');
        const expirationDate = selectedOption.getAttribute('data-expiration_date');
        const supplier = selectedOption.getAttribute('data-supplier');
        const orderNumber = selectedOption.getAttribute('data-order_number');
        const orderQuantity = selectedOption.getAttribute('data-order_quantity');
        const dosage = selectedOption.getAttribute('data-dosage');
        const form = selectedOption.getAttribute('data-form');
        const lotNumber = selectedOption.getAttribute('data-lot_number');
        const ndc = selectedOption.getAttribute('data-ndc');
        const dispenseUsed = selectedOption.getAttribute('data-dispense_used');
        const dispenseAs = selectedOption.getAttribute('data-dispense_as');
        const unitQuantity = selectedOption.getAttribute('data-unit_quantity');
        const prescriptionType = selectedOption.getAttribute('data-prescription_type');
        const medClass = selectedOption.getAttribute('data-medication_class');
        const minimumSupply = selectedOption.getAttribute('data-minimum_supply');
        const photoUrl = selectedOption.getAttribute('data-photo_url');
        const lastEdit = selectedOption.getAttribute('data-last_edit');
        const removed = selectedOption.getAttribute('data-removed');
        const restock = selectedOption.getAttribute('data-restock');
        const totalQuantity = selectedOption.getAttribute('data-total_quantity');

        // Convert expirationDate from MM/DD/YYYY to YYYY-MM-DD
        const [month, day, year] = expirationDate.split('/');
        const formattedExpDate = `${year}-${month}-${day}`;
        const current_date = window.APP_CONFIG.currentDate;  // Injected from Flask via APP_CONFIG
        const one_month_date = window.APP_CONFIG.oneMonthDate;

        // // Build expiration row based on comparison
        // // if (formattedExpDate < current_date) {
        // //     expirationRow = `<tr><td><strong>Expiration:</strong></td><td style="color: red;">${expirationDate}</td></tr>`;
        // // } else if (formattedExpDate < one_month_date) {
        // //     expirationRow = `<tr><td><strong>Expiration:</strong></td><td style="color: #cc6600;">${expirationDate} (Soon)</td></tr>`;
        // // } else {
        // //     expirationRow = `<tr><td><strong>Expiration:</strong></td><td>${expirationDate}</td></tr>`;
        // } else if (formattedExpDate < one_month_date) {
        // } else {


        // } else if (formattedExpDate < current_date) {
        // } else if (formattedExpDate < one_month_date) {
        // } else {

        if (!expirationDate) {
            expirationRow = `
                <tr>
                    <th>Expiration</th><td> Does not expire</td>
                </tr>`;
        } else if (formattedExpDate < current_date) {
            expirationRow = `
                <tr>
                    <th>Expiration</th><td style="color: red; font-weight: 600;"> ${expirationDate}</td>
                </tr>`;
        } else if (formattedExpDate < one_month_date) {
            expirationRow = `
                <tr>
                    <th>Expiration</th><td style="color: #e67e00; font-weight: 600;"> ${expirationDate}</td>
                </tr>`;
                
        } else {
            expirationRow = `
                <tr>
                    <th>Expiration</th><td> ${expirationDate}</td>
                </tr>`;
        }


        let quantityRow = quantity;
            if (parseInt(totalQuantity, 10) < parseInt(minimumSupply, 10)) {
                quantityRow = `<span style="color: red; font-weight: 600;">${quantityRow} (Low)</span>`;
                // quantityRow += ` <span style="color: red; font-weight: 600;">(Low)</span>`;
            }


        const dateObj = new Date(lastEdit);
        const month1 = String(dateObj.getMonth() + 1).padStart(2, '0');
        const day1 = String(dateObj.getDate()).padStart(2, '0');
        const year1 = dateObj.getFullYear();

        let hours = dateObj.getHours();
        const minutes = String(dateObj.getMinutes()).padStart(2, '0');

        const twentyfourLastEdit = `${month1}/${day1}/${year1} ${hours}:${minutes}`;

        const ampm = hours >= 12 ? 'PM' : 'AM';
        hours = hours % 12;
        hours = hours ? hours : 12; // the hour '0' should be '12'

        const formattedLastEdit = `${month1}/${day1}/${year1} ${hours}:${minutes} ${ampm}`;


        //NEW

        const allLotNumbers = window.APP_CONFIG.allLotNumbers;


        let akaOrLot;
        if (!aka || aka.trim() === "" || aka === "None" || allLotNumbers.includes(aka) || lotNumber) {
            akaOrLot = lotNumber;
        } else {
            akaOrLot = aka;
        }


        //NEW:1-10-2026
        // Construct the URL dynamically, keeping all the Jinja fields
        // Build the URL dynamically (exact same structure as before)
        //     `?name=${encodeURIComponent(name)}` +
        //     `&aka=${encodeURIComponent(aka)}` +
        //     `&status=${encodeURIComponent(status)}` +
        //     `&quantity=${encodeURIComponent(quantity)}` +
        //     `&location=${encodeURIComponent(location)}` +
        //     `&location1=${encodeURIComponent(location1)}` +
        //     `&location2=${encodeURIComponent(location2)}` +
        //     `&location3=${encodeURIComponent(location3)}` +
        //     `&location4=${encodeURIComponent(location4)}` +
        //     `&category=${encodeURIComponent(category)}` +
        //     `&description=${encodeURIComponent(description)}` +
        //     `&instrument_type=${encodeURIComponent(instrumentType)}` +
        //     `&dosage=${encodeURIComponent(dosage)}` +
        //     `&form=${encodeURIComponent(form)}` +
        //     `&ndc=${encodeURIComponent(ndc)}` +
        //     `&dispense_used=${encodeURIComponent(dispenseUsed)}` +
        //     `&dispense_as=${encodeURIComponent(dispenseAs)}` +
        //     `&unit_quantity=${encodeURIComponent(unitQuantity)}` +
        //     `&prescription_type=${encodeURIComponent(prescriptionType)}` +
        //     `&medication_class=${encodeURIComponent(medClass)}` +
        //     `&minimum_supply=${encodeURIComponent(minimumSupply)}` +
        //     `&photo_url=${encodeURIComponent(photoUrl)}` +
        //     `&last_edit=${encodeURIComponent(lastEdit)}` +
        //     `&removed=${encodeURIComponent(removed)}` +
        //     `&expiration_date=${encodeURIComponent(expirationDate)}` +
        //     `&supplier=${encodeURIComponent(supplier)}` +
        //     `&order_number=${encodeURIComponent(orderNumber)}` +
        //     `&lot_number=${encodeURIComponent(lotNumber)}` +
        //     `&restock=${encodeURIComponent(restock)}` +
        //     `&total_quantity=${encodeURIComponent(totalQuantity)}`;

        // // Update the href of the link, do NOT navigate
        // link.href = url;


        // Update the display with all the relevant details
        display.innerHTML = `
            <table style="margin-left: 0; text-align: left;" class="chart-table">
                

                <tr>
                    <th>Site</th><td> ${location}</td>
                </tr>
                <tr>
                    <th>Lot Number</th><td> ${lotNumber}</td>
                </tr>
                <tr>
                    <th>Dispensed Unit</th><td colspan="2"> ${dispenseAs}</td>
                </tr>
                
                
                <tr>
                <th>Location</th>
                <td>
                    <div>
                    ${[location1, location2, location3, location4]
                        .filter(loc => loc && loc.trim() !== "")
                        .join("<br>")}
                    </div>
                </td>
                </tr>
                <tr>
                    <th>Quantity</th><td> ${quantityRow}</td>
                </tr>
                <tr>
                    <th>Quantity to Order</th><td> ${orderQuantity}</td>
                </tr>

                ${expirationRow}

                <tr>
                    <th>Updated</th><td> ${twentyfourLastEdit}</td>
                </tr>
                
                
            </table>
        `;
        //         
        //         
        //         
        //         
        //         
        //         
        //         
        //         ${expirationRow}
        //         
        //         
        //         
        //         
        //         
        //         
        //         
        //         
        //         
        //         
        //         
        //         
        // `;
    } else {
        display.innerHTML = `
            <table style="margin: 0 auto; text-align: left;">
                
                <tr><td> Please select a lot number to view</td></tr>
            </table>
        `;
    }

    // Handle quantity dropdown population (same logic as before)
    updateQuantityDropdown(itemId);
}

function updateQuantityDropdown(itemId) {
    var locationSelect = document.getElementById('locationSelect-' + itemId);
    var quantitySelect = document.getElementById('quantitySelect-' + itemId);

    // Get the selected location option
    var selectedOption = locationSelect.options[locationSelect.selectedIndex];
    var availableQuantity = parseInt(selectedOption.getAttribute('data-quantity'));


    if (availableQuantity === 0 || parseInt(quantitySelect.dataset.nsCount) === 0) {
        quantitySelect.innerHTML = '<option value="" selected disabled>Out of Stock</option>';
        toggleConfirmButton(itemId);
    } else {
        // Clear the quantity dropdown before updating
        quantitySelect.innerHTML = '<option value="1" selected>1</option>';

        // Add the quantities based on the selected location
        for (var i = 2; i <= availableQuantity; i++) {
            var option = document.createElement("option");
            option.value = i;
            option.text = i;
            //     option.selected = true;  // Default select 1
            quantitySelect.appendChild(option);
        }


        // Ensure the Confirm Use button is disabled until a quantity is selected
        toggleConfirmButton(itemId);
    }
}

function toggleConfirmButton(itemId) {
    var quantitySelect = document.getElementById('quantitySelect-' + itemId);
    var transferSelect = document.getElementById('transferSelect-' + itemId);
    var locationSelect = document.getElementById('locationSelect-' + itemId);
    var confirmUseButton = document.getElementById('confirmUseButton-' + itemId);
    var confirmTransferButton = document.getElementById('confirmTransferButton-' + itemId);

    var confirmRemoveButton = document.getElementById('confirmRemoveButton-' + itemId);
    var confirmRestockButton = document.getElementById('confirmRestockButton-' + itemId);
    var viewDetailsButton = document.getElementById('viewDetailsButton-' + itemId);
    var editDetailsButton = document.getElementById('editDetailsButton-' + itemId);

    // If a valid quantity is selected, enable the button, otherwise disable it
    //     confirmUseButton.disabled = false;
    //     confirmTransferButton.disabled = false;
    // } else if (quantitySelect.value && !transferSelect.value) {
    //     confirmUseButton.disabled = false;
    //     confirmTransferButton.disabled = true;
    // } else {
    //     confirmUseButton.disabled = true;
    //     confirmTransferButton.disabled = true;
    // NEW LOGIC
    const locationSelected = !!locationSelect.value;
    const quantitySelected = !!quantitySelect.value;
    const transferSelected = !!transferSelect.value;
    const nsCount = parseInt(confirmRemoveButton.dataset.nsCount);
    viewDetailsButton.disabled = !locationSelected;
    editDetailsButton.disabled = !locationSelected;
    confirmUseButton.disabled = !quantitySelected;
    confirmTransferButton.disabled = !(quantitySelected && transferSelected);
    confirmRemoveButton.disabled = !locationSelected || nsCount === 0;
    confirmRestockButton.disabled = !locationSelected;

}

/* ---------------------------------------------------------------------
 * Confirmation dialogs
 * ------------------------------------------------------------------- */

window.confirmDialogActive = false;

function confirmDelete() {
    // Set the flag to indicate the confirmation dialog is active
    window.confirmDialogActive = true;

    // Show the confirmation dialog and store the result
    const isConfirmed = confirm('Are you sure you want to delete this Lot? This action cannot be undone.');

    // Use setTimeout to delay resetting the flag after dialog closes
    setTimeout(function() {
        // Reset the flag after the dialog has been closed
        window.confirmDialogActive = false;
    }, 0);  // 0 ms delay ensures it runs after the dialog closes

    // Return whether the user confirmed the action (true for OK, false for Cancel)
    return isConfirmed;
}

function confirmDelist() {
    // Set the flag to indicate the confirmation dialog is active
    window.confirmDialogActive = true;

    // Show the confirmation dialog and store the result
    const isConfirmed = confirm('DELIST ITEM: Remove the item listing from the main page? Existing lots will be removed.');

    // Use setTimeout to delay resetting the flag after dialog closes
    setTimeout(function() {
        // Reset the flag after the dialog has been closed
        window.confirmDialogActive = false;
    }, 0);  // 0 ms delay ensures it runs after the dialog closes

    // Return whether the user confirmed the action (true for OK, false for Cancel)
    return isConfirmed;
}

/* ---------------------------------------------------------------------
 * Item details toggle (the "Details" chevron button)
 * ------------------------------------------------------------------- */

function toggleItemInfo(itemId) {
    const container = document.getElementById(`itemInfoContainer-${itemId}`);
    const button = document.getElementById(`toggleInfoBtn-${itemId}`);
    const isHidden = container.style.display === "none";

    container.style.display = isHidden ? "block" : "none";

    button.innerHTML = isHidden
        ? `<i class="bi bi-chevron-down"></i> <span class="small">Details</span>`
        : `<i class="bi bi-chevron-right"></i> <span class="small">Details</span>`;

    console.log("Debug main: line 5032");
}

/* ---------------------------------------------------------------------
 * "View Details" / "Expand Info" collapse toggle + remembered
 * expand/collapse preference (localStorage). Originally re-registered
 * once per item via `.toggle-details-btn` (a class selector that
 * matches every item's button at once), so a single registration here
 * is behaviorally identical to the original's many redundant ones.
 * ------------------------------------------------------------------- */
document.addEventListener('DOMContentLoaded', () => {
    const buttons = document.querySelectorAll('.toggle-details-btn');

    // Load saved preference from localStorage
    const savedPreference = localStorage.getItem('detailsPreference') || 'hide';

    buttons.forEach(btn => {
        // Apply saved preference on page load
        if (savedPreference === 'hide') {
            btn.textContent = 'Collapse Info';
            console.log("Debug main: line 3608");
            const target = document.querySelector(btn.getAttribute('data-bs-target'));
            target.classList.add('show'); // expand all items if preference is "hide"
        } else {
            btn.textContent = 'Expand Info';
        }

        buttons.forEach(btn => {
            const target = document.querySelector(btn.dataset.bsTarget);

            target.addEventListener('shown.bs.collapse', () => {
                btn.textContent = 'Collapse Info';
                localStorage.setItem('detailsPreference', 'hide');
            });

            target.addEventListener('hidden.bs.collapse', () => {
                btn.textContent = 'Expand Info';
                localStorage.setItem('detailsPreference', 'view');
            });
        });
    });
});

/* ---------------------------------------------------------------------
 * Use-overlay click-outside-to-close. Originally re-registered once
 * per item via the `.use-overlay` class selector (which matches every
 * item's overlay at once), so a single registration here is
 * behaviorally identical to the original's many redundant ones.
 * ------------------------------------------------------------------- */
document.addEventListener('DOMContentLoaded', function() {
    // Attach click handlers to all overlays
    document.querySelectorAll('.use-overlay').forEach(overlay => {
        console.log("Debug 5209");
        overlay.addEventListener('click', function(e) {

            if (getComputedStyle(overlay).display === 'none') return;

            console.log("Debug 5210");
            const modal = overlay.querySelector('.popup-container1');

            // Only close if clicked outside the modal
            if (!modal.contains(e.target)) {
                console.log("Debug 5214");
                const itemId = overlay.id.replace('use-overlay-', '');
                console.log("Debug line ??? main: pre toggle_use_overlay_9", itemId);
                toggleUseOverlay(itemId);
            }
        });
    });
});
