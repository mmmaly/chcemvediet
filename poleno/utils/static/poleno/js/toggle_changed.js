/* Enables input elements to automatically toggle other elemets when their value change. Tested on
 * checkbox, radio and select. But should work on all input elements as well.
 *
 * Requires:
 *  -- JQuery
 *
 * Examples:
 *     <input type="checkbox" class="toggle-changed" data-container="form"
 *            data-target-true=".visible-if-true" data-target-false=".visible-if-false" />
 *
 *     <select class="toggle-changed" data-container="form"
 *             data-target-aaa=".visible-if-aaa" data-target-bbb=".visible-if-bbb">
 *       <option value="aaa">...</option>
 *       <option value="bbb">...</option>
 *     </select>
 *
 *     <input type="radio" name="group" value="1" class="toggle-changed" data-container="form"
 *            data-target-1=".visible-if-1" data-target-2=".visible-if-2" />
 *     <input type="radio" name="group" value="2" class="toggle-changed" data-container="form"
 *            data-target-1=".visible-if-1" data-target-2=".visible-if-2" />
 */
$(function(){
	function toggle(){
		console.log(this);
		var container = $(this).data('container') || 'html';
		var value = $(this).is(':checkbox') ? $(this).prop('checked') : $(this).val();
		var active = $(this).attr('data-target-' + value);
		var all = $.map(this.attributes, function(attr){
			if (attr.name.match("^data-target-")) return attr.value;
		}).join(', ');
		$(this).parents(container).find(all).not(active).hide();
		$(this).parents(container).find(active).show();
	}
	function toggleAll(){
		// Every radio group shlould be initialized only once. If there is a checked button
		// in the group, use this button. If there is no checked button in the group use
		// any group button.
		var checked = {};
		var unchecked = {};
		$('.toggle-changed:radio').each(function(){
			if ($(this).prop('checked')) {
				checked[this.name] = this;
				delete unchecked[this.name];
			} if (!checked[this.name]) {
				unchecked[this.name] = this;
			}
		});
		$.each(checked, toggle);
		$.each(unchecked, toggle);

		// Other input elements
		$('.toggle-changed:not(:radio)').each(toggle);
	}
	$(document).on('change', '.toggle-changed', toggle);
	$(document).on('dom-changed', toggleAll); // Triggered by: poleno/js/ajax.js
	toggleAll();
})
