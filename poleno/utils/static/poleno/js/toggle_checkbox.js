/* Enables checkbox to automatically toggle elemets when it's checked.
 *
 * Requires:
 *  -- JQuery
 *
 * Example:
 *     <input type="checkbox" class="toggle-checkbox" data-container=".parent" data-target=".target"/>
 */
$(function(){
	function toggle(){
		var container = $(this).data('container') || 'html';
		var target = $(this).data('target');
		var checked = $(this).prop('checked');
		$(this).parents(container).find(target).toggle(checked);
	}
	function toggleAll(){
		$('.toggle-checkbox').each(toggle);
	}
	$(document).on('change', '.toggle-checkbox', toggle);
	$(document).on('dom-changed', toggleAll); // Triggered by: poleno/js/ajax.js
	toggleAll();
});
