/* Attaches ObligeeWithAddressInput to JQuery Autocomplete events and updates Obligee
 * details whenever the user selects a new Obligee.
 *
 * Requires:
 *  -- JQuery UI Autocomplete
 */
$(function(){
	function handler(event, ui){
		if (ui.item) {
			var obligee = ui.item.obligee;
			$('.obligee_with_address_input_street', this).text(obligee.street);
			$('.obligee_with_address_input_zip', this).text(obligee.zip);
			$('.obligee_with_address_input_city', this).text(obligee.city);
			$('.obligee_with_address_input_email', this).text(obligee.emails);
			$('.obligee_with_address_input_details', this).show();
		} else {
			$('.obligee_with_address_input_details', this).hide();
		}
	}
	$(document).on('autocompleteselect', '.obligee_with_address_input', handler);
	$(document).on('autocompletechange', '.obligee_with_address_input', handler);
});
